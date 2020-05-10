import * as React from "react";
import gql from "graphql-tag";
import { Icon, Colors } from "@blueprintjs/core";
import { IconNames } from "@blueprintjs/icons";

import { pluginForMetadata } from "./plugins";
import SolidTypeSignature from "./SolidTypeSignature";
import TypeWithTooltip from "./TypeWithTooltip";
import {
  SidebarSection,
  SidebarTitle,
  SidebarSubhead,
  SectionSmallHeader,
  SectionItemContainer
} from "./SidebarComponents";
import Description from "./Description";
import { ConfigTypeSchema } from "./ConfigTypeSchema";
import { SidebarSolidDefinitionFragment } from "./types/SidebarSolidDefinitionFragment";
import {
  SolidMappingTable,
  ResourceContainer,
  ResourceHeader,
  TypeWrapper,
  SolidLinks,
  Invocation,
  ShowAllButton,
  SidebarSolidInvocationInfo
} from "./SidebarSolidHelpers";
import { breakOnUnderscores } from "./Util";

interface SidebarSolidDefinitionProps {
  definition: SidebarSolidDefinitionFragment;
  getInvocations?: (definitionName: string) => { handleID: string }[];
  showingSubsolids: boolean;
  onClickInvocation: (arg: SidebarSolidInvocationInfo) => void;
}

const DEFAULT_INVOCATIONS_SHOWN = 20;

export class SidebarSolidDefinition extends React.Component<
  SidebarSolidDefinitionProps,
  { showingAllInvocations: boolean }
> {
  static fragments = {
    SidebarSolidDefinitionFragment: gql`
      fragment SidebarSolidDefinitionFragment on ISolidDefinition {
        ...SolidTypeSignatureFragment
        __typename
        name
        description
        metadata {
          key
          value
        }
        requiredResources {
          resourceKey
        }
        outputDefinitions {
          name
          description
          type {
            ...RuntimeTypeWithTooltipFragment
          }
        }
        inputDefinitions {
          name
          description
          type {
            ...RuntimeTypeWithTooltipFragment
          }
        }
        ... on SolidDefinition {
          configField {
            configType {
              ...ConfigTypeSchemaFragment
              recursiveConfigTypes {
                ...ConfigTypeSchemaFragment
              }
            }
          }
        }
        ... on CompositeSolidDefinition {
          inputMappings {
            definition {
              name
            }
            mappedInput {
              definition {
                name
              }
              solid {
                name
              }
            }
          }
          outputMappings {
            definition {
              name
            }
            mappedOutput {
              definition {
                name
              }
              solid {
                name
              }
            }
          }
        }
      }

      ${TypeWithTooltip.fragments.RuntimeTypeWithTooltipFragment}
      ${SolidTypeSignature.fragments.SolidTypeSignatureFragment}
      ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
    `
  };

  public render() {
    const {
      definition,
      getInvocations,
      showingSubsolids,
      onClickInvocation
    } = this.props;
    const Plugin = pluginForMetadata(definition.metadata);
    const isComposite = definition.__typename === "CompositeSolidDefinition";
    const configField =
      definition.__typename === "SolidDefinition"
        ? definition.configField
        : null;

    const inputMappings: SolidMappingTable = {};
    const outputMappings: SolidMappingTable = {};

    if (
      showingSubsolids &&
      definition.__typename === "CompositeSolidDefinition"
    ) {
      definition.inputMappings.forEach(
        m =>
          (inputMappings[m.definition.name] = [
            ...(inputMappings[m.definition.name] || []),
            m.mappedInput
          ])
      );
      definition.outputMappings.forEach(
        m =>
          (outputMappings[m.definition.name] = [
            ...(outputMappings[m.definition.name] || []),
            m.mappedOutput
          ])
      );
    }

    const hasRequiredResources = !!(
      definition.requiredResources && definition.requiredResources.length
    );

    return (
      <div>
        <SidebarSection title={"Definition"}>
          <SidebarSubhead>
            {isComposite ? "Composite Solid" : "Solid"}
          </SidebarSubhead>
          <SidebarTitle>{breakOnUnderscores(definition.name)}</SidebarTitle>
          <SolidTypeSignature definition={definition} />
        </SidebarSection>
        {definition.description && (
          <SidebarSection title={"Description"}>
            <Description description={definition.description} />
          </SidebarSection>
        )}
        {definition.metadata && Plugin && Plugin.SidebarComponent && (
          <SidebarSection title={"Metadata"}>
            <Plugin.SidebarComponent definition={definition} />
          </SidebarSection>
        )}
        {configField && (
          <SidebarSection title={"Config"}>
            <ConfigTypeSchema
              type={configField.configType}
              typesInScope={configField.configType.recursiveConfigTypes}
            />
          </SidebarSection>
        )}
        {hasRequiredResources && (
          <SidebarSection title={"Required Resources"}>
            {definition.requiredResources.sort().map(requirement => (
              <ResourceContainer key={requirement.resourceKey}>
                <Icon
                  iconSize={14}
                  icon={IconNames.LAYERS}
                  color={Colors.DARK_GRAY2}
                />
                <ResourceHeader>{requirement.resourceKey}</ResourceHeader>
              </ResourceContainer>
            ))}
          </SidebarSection>
        )}
        <SidebarSection title={"Inputs"}>
          {definition.inputDefinitions.map((inputDef, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>
                {breakOnUnderscores(inputDef.name)}
              </SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={inputDef.type} />
              </TypeWrapper>
              <Description description={inputDef.description} />
              <SolidLinks
                title="Mapped to:"
                items={inputMappings[inputDef.name]}
              />
            </SectionItemContainer>
          ))}
        </SidebarSection>
        <SidebarSection title={"Outputs"}>
          {definition.outputDefinitions.map((outputDef, idx) => (
            <SectionItemContainer key={idx}>
              <SectionSmallHeader>
                {breakOnUnderscores(outputDef.name)}
              </SectionSmallHeader>
              <TypeWrapper>
                <TypeWithTooltip type={outputDef.type} />
              </TypeWrapper>
              <SolidLinks
                title="Mapped from:"
                items={outputMappings[outputDef.name]}
              />
              <Description description={outputDef.description} />
            </SectionItemContainer>
          ))}
        </SidebarSection>
        {getInvocations && (
          <SidebarSection title={"All Invocations"}>
            <InvocationList
              invocations={getInvocations(definition.name)}
              onClickInvocation={onClickInvocation}
            />
          </SidebarSection>
        )}
      </div>
    );
  }
}

const InvocationList: React.FunctionComponent<{
  invocations: SidebarSolidInvocationInfo[];
  onClickInvocation: (arg: SidebarSolidInvocationInfo) => void;
}> = ({ invocations, onClickInvocation }) => {
  const [showAll, setShowAll] = React.useState<boolean>(false);
  const displayed = showAll
    ? invocations
    : invocations.slice(0, DEFAULT_INVOCATIONS_SHOWN);

  return (
    <>
      {displayed.map((invocation, idx) => (
        <Invocation
          key={idx}
          invocation={invocation}
          onClick={() => onClickInvocation(invocation)}
        />
      ))}
      {displayed.length < invocations.length && (
        <ShowAllButton onClick={() => setShowAll(true)}>
          {`Show ${invocations.length - displayed.length} More Invocations`}
        </ShowAllButton>
      )}
    </>
  );
};
