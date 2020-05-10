import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Colors, Icon, Checkbox } from "@blueprintjs/core";

import PythonErrorInfo from "../PythonErrorInfo";
import { showCustomAlert } from "../CustomAlertProvider";
import { SplitPanelContainer } from "../SplitPanelContainer";
import { errorStackToYamlPath } from "../configeditor/ConfigEditorUtils";
import { ButtonLink } from "../ButtonLink";

import {
  ConfigEditorEnvironmentSchemaFragment,
  ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType
} from "../configeditor/types/ConfigEditorEnvironmentSchemaFragment";
import { RunPreviewExecutionPlanResultFragment } from "./types/RunPreviewExecutionPlanResultFragment";
import {
  RunPreviewValidationFragment,
  RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors
} from "./types/RunPreviewValidationFragment";

type ValidationError = RunPreviewValidationFragment_PipelineConfigValidationInvalid_errors;
type ValidationErrorOrNode = ValidationError | React.ReactNode;

function isValidationError(e: ValidationErrorOrNode): e is ValidationError {
  return e && typeof e === "object" && "__typename" in e ? true : false;
}

interface RunPreviewProps {
  plan: RunPreviewExecutionPlanResultFragment | null;
  validation: RunPreviewValidationFragment | null;
  document: object | null;

  actions?: React.ReactChild;
  environmentSchema: ConfigEditorEnvironmentSchemaFragment;
  onHighlightPath: (path: string[]) => void;
}

interface RunPreviewState {
  errorsOnly: boolean;
}

export class RunPreview extends React.Component<
  RunPreviewProps,
  RunPreviewState
> {
  static fragments = {
    RunPreviewExecutionPlanResultFragment: gql`
      fragment RunPreviewExecutionPlanResultFragment on ExecutionPlanResult {
        __typename
        ... on ExecutionPlan {
          __typename
        }
        ... on PipelineNotFoundError {
          message
        }
        ... on InvalidSubsetError {
          message
        }
        ...PythonErrorFragment
      }
      ${PythonErrorInfo.fragments.PythonErrorFragment}
    `,
    RunPreviewValidationFragment: gql`
      fragment RunPreviewValidationFragment on PipelineConfigValidationResult {
        __typename
        ... on PipelineConfigValidationInvalid {
          errors {
            __typename
            reason
            message
            stack {
              entries {
                __typename
                ... on EvaluationStackPathEntry {
                  fieldName
                }
                ... on EvaluationStackListItemEntry {
                  listIndex
                }
              }
            }
            ... on MissingFieldConfigError {
              field {
                name
              }
            }
            ... on MissingFieldsConfigError {
              fields {
                name
              }
            }
          }
        }
      }
    `
  };

  state: RunPreviewState = {
    errorsOnly: false
  };

  shouldComponentUpdate(
    nextProps: RunPreviewProps,
    nextState: RunPreviewState
  ) {
    return (
      nextProps.validation !== this.props.validation ||
      nextProps.plan !== this.props.plan ||
      nextState.errorsOnly !== this.state.errorsOnly
    );
  }

  getRootCompositeChildren = () => {
    const {
      allConfigTypes,
      rootEnvironmentType
    } = this.props.environmentSchema;
    const children: {
      [fieldName: string]: ConfigEditorEnvironmentSchemaFragment_allConfigTypes_CompositeConfigType;
    } = {};

    const root = allConfigTypes.find(t => t.key === rootEnvironmentType.key);
    if (root?.__typename !== "CompositeConfigType") return children;

    root.fields.forEach(field => {
      const allConfigVersion = allConfigTypes.find(
        t => t.key === field.configTypeKey
      );
      if (allConfigVersion?.__typename !== "CompositeConfigType") return;
      children[field.name] = allConfigVersion;
    });

    return children;
  };

  render() {
    const { plan, actions, document, validation, onHighlightPath } = this.props;
    const { errorsOnly } = this.state;

    const missingNodes: string[] = [];
    const errorsAndPaths: {
      pathKey: string;
      error: ValidationErrorOrNode;
    }[] = [];

    if (
      validation &&
      validation.__typename === "PipelineConfigValidationInvalid"
    ) {
      validation.errors.forEach(e => {
        const path = errorStackToYamlPath(e.stack.entries);

        if (e.__typename === "MissingFieldConfigError") {
          missingNodes.push([...path, e.field.name].join("."));
        } else if (e.__typename === "MissingFieldsConfigError") {
          for (const field of e.fields) {
            missingNodes.push([...path, field.name].join("."));
          }
        } else {
          errorsAndPaths.push({ pathKey: path.join("."), error: e });
        }
      });
    }

    if (plan?.__typename === "InvalidSubsetError") {
      errorsAndPaths.push({ pathKey: "", error: plan.message });
    }

    if (plan?.__typename === "PythonError") {
      const info = <PythonErrorInfo error={plan} />;
      errorsAndPaths.push({
        pathKey: "",
        error: (
          <>
            PythonError{" "}
            <span onClick={() => showCustomAlert({ body: info })}>
              click for details
            </span>
          </>
        )
      });
    }

    const { resources, solids, ...rest } = this.getRootCompositeChildren();

    const itemsIn = (parents: string[], names: string[]) => {
      const parentsKey = parents.join(".");
      const parentErrors = errorsAndPaths.filter(e => e.pathKey === parentsKey);

      const boxes = names
        .map(name => {
          const path = [...parents, name];
          const pathKey = path.join(".");
          const pathErrors = errorsAndPaths
            .filter(
              e => e.pathKey === pathKey || e.pathKey.startsWith(`${pathKey}.`)
            )
            .map(e => e.error);

          const isPresent = pathExistsInObject(path, document);
          const isInvalid = pathErrors.length || parentErrors.length;
          const isMissing = path.some((_, idx) =>
            missingNodes.includes(path.slice(0, idx + 1).join("."))
          );

          if (errorsOnly && !isInvalid) {
            return false;
          }
          const state = isMissing
            ? "missing"
            : isInvalid
            ? "invalid"
            : isPresent
            ? "present"
            : "none";

          return (
            <Item
              key={name}
              state={state}
              title={
                {
                  invalid: `You need to fix this configuration section.`,
                  missing: `You need to add this configuration section.`,
                  present: `This section is present and valid.`,
                  none: `This section is empty and valid.`
                }[state]
              }
              onClick={() => {
                const first = pathErrors.find(isValidationError);
                onHighlightPath(
                  first ? errorStackToYamlPath(first.stack.entries) : path
                );
              }}
            >
              {name}
            </Item>
          );
        })
        .filter(Boolean);

      if (!boxes.length) {
        return <ItemsEmptyNotice>Nothing to display.</ItemsEmptyNotice>;
      }
      return boxes;
    };

    return (
      <SplitPanelContainer
        identifier="run-preview"
        axis="horizontal"
        first={
          <ErrorListContainer>
            <Section>
              <SectionTitle>Errors</SectionTitle>
              {errorsAndPaths.map((item, idx) => (
                <ErrorRow
                  key={idx}
                  error={item.error}
                  onHighlight={onHighlightPath}
                />
              ))}
            </Section>
          </ErrorListContainer>
        }
        firstInitialPercent={50}
        firstMinSize={150}
        second={
          <>
            <div style={{ overflowY: "scroll", width: "100%", height: "100%" }}>
              <RuntimeAndResourcesSection>
                <Section>
                  <SectionTitle>Runtime</SectionTitle>
                  <ItemSet>{itemsIn([], Object.keys(rest))}</ItemSet>
                </Section>
                {(resources?.fields.length || 0) > 0 && (
                  <Section>
                    <SectionTitle>Resources</SectionTitle>
                    <ItemSet>
                      {itemsIn(
                        ["resources"],
                        (resources?.fields || []).map(f => f.name)
                      )}
                    </ItemSet>
                  </Section>
                )}
              </RuntimeAndResourcesSection>
              <Section>
                <SectionTitle>Solids</SectionTitle>
                <ItemSet>
                  {itemsIn(
                    ["solids"],
                    (solids?.fields || []).map(f => f.name)
                  )}
                </ItemSet>
              </Section>
              <div style={{ height: 50 }} />
            </div>
            <div
              style={{
                position: "absolute",
                top: 0,
                right: 0,
                padding: "12px 15px 0px 10px",
                background: "rgba(255,255,255,0.7)"
              }}
            >
              <Checkbox
                label="Errors Only"
                checked={errorsOnly}
                onChange={() => this.setState({ errorsOnly: !errorsOnly })}
              />
            </div>
            <div style={{ position: "absolute", bottom: 14, right: 14 }}>
              {actions}
            </div>
          </>
        }
      />
    );
  }
}

const SectionTitle = styled.div`
  color: ${Colors.GRAY3};
  text-transform: uppercase;
  font-size: 12px;
`;

const Section = styled.div`
  margin-top: 14px;
  margin-left: 10px;
`;

const ItemSet = styled.div`
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
`;

const ItemsEmptyNotice = styled.div`
  font-size: 13px;
  padding-top: 7px;
  padding-bottom: 7px;
`;

const ItemBorder = {
  invalid: `1px solid #CE1126`,
  missing: `1px solid #D9822B`,
  present: `1px solid #AFCCE1`,
  none: `1px solid ${Colors.LIGHT_GRAY2}`
};

const ItemBackground = {
  invalid: Colors.RED5,
  missing: "#F2A85C",
  present: "#C8E1F4",
  none: Colors.LIGHT_GRAY4
};

const ItemBackgroundHover = {
  invalid: "#E15858",
  missing: "#F2A85C",
  present: "#AFCCE1",
  none: Colors.LIGHT_GRAY4
};

const ItemColor = {
  invalid: Colors.WHITE,
  missing: Colors.WHITE,
  present: Colors.BLACK,
  none: Colors.BLACK
};

const Item = styled.div<{
  state: "present" | "missing" | "invalid" | "none";
}>`
  white-space: nowrap;
  font-size: 13px;
  color: ${({ state }) => ItemColor[state]};
  background: ${({ state }) => ItemBackground[state]};
  border-radius: 3px;
  border: ${({ state }) => ItemBorder[state]};
  padding: 3px 5px;
  margin: 3px;
  transition: background 150ms linear, color 150ms linear;
  cursor: ${({ state }) => (state === "present" ? "default" : "not-allowed")};

  &:hover {
    transition: none;
    background: ${({ state }) => ItemBackgroundHover[state]};
  }
`;

const ErrorListContainer = styled.div`
  margin-left: 10px;
  overflow-y: scroll;
  height: 100%;
`;

const ErrorRowContainer = styled.div<{ hoverable: boolean }>`
  text-align: left;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  border-bottom: 1px solid #ccc;
  padding: 7px 0;
  padding-right: 7px;
  margin-bottom: 8px;
  &:last-child {
    border-bottom: 0;
    margin-bottom: 15px;
  }
  ${({ hoverable }) =>
    hoverable &&
    `&:hover {
      background: ${Colors.LIGHT_GRAY5};
    }
  `}
`;

const RuntimeAndResourcesSection = styled.div`
  display: flex;
  @media (max-width: 800px) {
    flex-direction: column;
  }
`;

const ErrorRow: React.FunctionComponent<{
  error: ValidationError | React.ReactNode;
  onHighlight: (path: string[]) => void;
}> = ({ error, onHighlight }) => {
  let message = error;
  let target: ValidationError | null = null;
  if (isValidationError(error)) {
    message = error.message;
    target = error;
  }

  let displayed = message;
  if (typeof message === "string" && message.length > 400) {
    displayed = truncateErrorMessage(message);
  }

  return (
    <ErrorRowContainer
      hoverable={!!target}
      onClick={() =>
        target && onHighlight(errorStackToYamlPath(target.stack.entries))
      }
    >
      <div style={{ paddingRight: 8 }}>
        <Icon icon="error" iconSize={14} color={Colors.RED4} />
      </div>
      <div>
        {displayed}
        {displayed !== message && (
          <>
            &nbsp;
            <ButtonLink
              onClick={() =>
                showCustomAlert({
                  body: <div style={{ whiteSpace: "pre-wrap" }}>{message}</div>
                })
              }
            >
              View&nbsp;All&nbsp;&gt;
            </ButtonLink>
          </>
        )}
      </div>
    </ErrorRowContainer>
  );
};

function truncateErrorMessage(message: string) {
  let split = message.indexOf("{");
  if (split === -1) {
    split = message.indexOf(". ");
  }
  if (split === -1) {
    split = 400;
  }
  return message.substr(0, split) + "... ";
}

function pathExistsInObject(path: string[], object: any): boolean {
  if (!object || typeof object !== "object") return false;
  if (path.length === 0) return true;
  const [first, ...rest] = path;
  return pathExistsInObject(rest, object[first]);
}
