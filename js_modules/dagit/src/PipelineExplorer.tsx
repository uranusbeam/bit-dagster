import * as React from "react";
import gql from "graphql-tag";
import Color from "color";
import styled from "styled-components/macro";
import { History } from "history";
import { Icon, Colors, InputGroup, Checkbox } from "@blueprintjs/core";
import { Route } from "react-router";
import { Link } from "react-router-dom";
import * as querystring from "query-string";

import { PipelineExplorerFragment } from "./types/PipelineExplorerFragment";
import { PipelineGraphContainer } from "./graph/PipelineGraphContainer";
import PipelineGraph from "./graph/PipelineGraph";
import { SplitPanelContainer } from "./SplitPanelContainer";
import SidebarTabbedContainer from "./SidebarTabbedContainer";
import { PipelineExplorerSolidHandleFragment } from "./types/PipelineExplorerSolidHandleFragment";
import { filterByQuery } from "./GraphQueryImpl";
import { SolidJumpBar, PipelineJumpBar } from "./PipelineJumpComponents";
import { GraphQueryInput } from "./GraphQueryInput";

export interface PipelineExplorerOptions {
  explodeComposites: boolean;
}

export type SolidNameOrPath = { name: string } | { path: string[] };

interface PipelineExplorerProps {
  history: History;
  path: string[];
  visibleSolidsQuery: string;
  options: PipelineExplorerOptions;
  setOptions: (options: PipelineExplorerOptions) => void;
  pipeline: PipelineExplorerFragment;
  handles: PipelineExplorerSolidHandleFragment[];
  selectedHandle?: PipelineExplorerSolidHandleFragment;
  parentHandle?: PipelineExplorerSolidHandleFragment;
  getInvocations?: (definitionName: string) => { handleID: string }[];
}

interface PipelineExplorerState {
  highlighted: string;
}

export default class PipelineExplorer extends React.Component<
  PipelineExplorerProps,
  PipelineExplorerState
> {
  static fragments = {
    PipelineExplorerFragment: gql`
      fragment PipelineExplorerFragment on Pipeline {
        name
        description
        ...SidebarTabbedContainerPipelineFragment
      }
      ${SidebarTabbedContainer.fragments.SidebarTabbedContainerPipelineFragment}
    `,
    PipelineExplorerSolidHandleFragment: gql`
      fragment PipelineExplorerSolidHandleFragment on SolidHandle {
        handleID
        solid {
          name
          ...PipelineGraphSolidFragment
        }
      }
      ${PipelineGraph.fragments.PipelineGraphSolidFragment}
    `
  };

  pathOverlayEl = React.createRef<HTMLDivElement>();

  state = {
    highlighted: ""
  };

  handleQueryChange = (query: string) => {
    const { history, pipeline, path } = this.props;
    history.replace(`/pipeline/${pipeline.name}:${query}/${path.join("/")}`);
  };

  handleAdjustPath = (fn: (solidNames: string[]) => void) => {
    const { history, pipeline, path, visibleSolidsQuery } = this.props;
    const next = [...path];
    const retValue = fn(next);
    if (retValue !== undefined) {
      throw new Error(
        "handleAdjustPath function is expected to mutate the array"
      );
    }
    history.push(
      `/pipeline/${pipeline.name}:${visibleSolidsQuery}/${next.join("/")}`
    );
  };

  // Note: this method handles relative solid paths, eg: {path: ['..', 'OtherSolid']}.
  // This is important because the DAG component tree doesn't always have access to a handleID,
  // and we sometimes want to be able to jump to a solid in the parent layer.
  //
  handleClickSolid = (arg: SolidNameOrPath) => {
    this.handleAdjustPath(solidNames => {
      if ("name" in arg) {
        solidNames[solidNames.length - 1] = arg.name;
      } else {
        if (arg.path[0] !== "..") {
          solidNames.length = 0;
        }
        if (arg.path[0] === ".." && solidNames[solidNames.length - 1] !== "") {
          solidNames.pop(); // remove the last path component indicating selection
        }
        while (arg.path[0] === "..") {
          arg.path.shift();
          solidNames.pop();
        }
        solidNames.push(...arg.path);
      }
    });
  };

  handleEnterCompositeSolid = (arg: SolidNameOrPath) => {
    // To animate the rect of the composite solid expanding correctly, we need
    // to select it before entering it so we can draw the "initial state" of the
    // labeled rectangle.
    this.handleClickSolid(arg);

    window.requestAnimationFrame(() => {
      this.handleAdjustPath(solidNames => {
        const last = "name" in arg ? arg.name : arg.path[arg.path.length - 1];
        solidNames[solidNames.length - 1] = last;
        solidNames.push("");
      });
    });
  };

  handleLeaveCompositeSolid = () => {
    this.handleAdjustPath(solidNames => {
      solidNames.pop();
    });
  };

  handleClickBackground = () => {
    this.handleClickSolid({ name: "" });
  };

  public render() {
    const {
      path,
      options,
      history,
      pipeline,
      parentHandle,
      visibleSolidsQuery
    } = this.props;
    const { highlighted } = this.state;

    const solids = this.props.handles.map(h => h.solid);
    const solidsQueryEnabled = !parentHandle;
    const explodeCompositesEnabled =
      !parentHandle &&
      (options.explodeComposites ||
        solids.some(
          f => f.definition.__typename === "CompositeSolidDefinition"
        ));

    const queryResultSolids = solidsQueryEnabled
      ? filterByQuery(solids, visibleSolidsQuery)
      : { all: solids, focus: [] };

    const highlightedSolids = queryResultSolids.all.filter(s =>
      s.name.includes(highlighted)
    );

    let selectedHandle = this.props.selectedHandle;
    if (
      selectedHandle &&
      !queryResultSolids.all.some(s => s.name === selectedHandle!.solid.name)
    ) {
      selectedHandle = undefined;
    }

    const backgroundColor = parentHandle
      ? Colors.LIGHT_GRAY3
      : Colors.LIGHT_GRAY5;

    const backgroundTranslucent = Color(backgroundColor)
      .fade(0.6)
      .toString();

    return (
      <SplitPanelContainer
        identifier="explorer"
        firstInitialPercent={70}
        first={
          <>
            <PathOverlay
              style={{ background: backgroundTranslucent }}
              ref={this.pathOverlayEl}
            >
              <PipelineJumpBar
                selectedPipelineName={pipeline.name}
                onChange={name => history.push(`/pipeline/${name}:/`)}
              />
              <Icon icon="chevron-right" />
              {path.slice(0, path.length - 1).map((name, idx) => (
                <React.Fragment key={idx}>
                  <Link
                    style={{ padding: 3 }}
                    to={`/pipeline/${
                      pipeline.name
                    }:${visibleSolidsQuery}/${path
                      .slice(0, idx + 1)
                      .join("/")}`}
                  >
                    {name}
                  </Link>
                  <Icon icon="chevron-right" />
                </React.Fragment>
              ))}
              <SolidJumpBar
                solids={queryResultSolids.all}
                selectedSolid={selectedHandle && selectedHandle.solid}
                onChange={solid => this.handleClickSolid({ name: solid.name })}
              />
            </PathOverlay>
            {solidsQueryEnabled && (
              <GraphQueryInput
                items={solids}
                value={visibleSolidsQuery}
                placeholder="Type a Solid Subset"
                onChange={this.handleQueryChange}
              />
            )}

            <SearchOverlay style={{ background: backgroundTranslucent }}>
              <SolidHighlightInput
                type="text"
                name="highlighted"
                leftIcon="search"
                value={highlighted}
                placeholder="Highlight..."
                onChange={(e: React.ChangeEvent<any>) =>
                  this.setState({ highlighted: e.target.value })
                }
              />
            </SearchOverlay>
            {explodeCompositesEnabled && (
              <OptionsOverlay>
                <Checkbox
                  label="Explode composites"
                  checked={options.explodeComposites}
                  onChange={() => {
                    this.handleQueryChange("");
                    this.props.setOptions({
                      ...options,
                      explodeComposites: !options.explodeComposites
                    });
                  }}
                />
              </OptionsOverlay>
            )}
            {queryResultSolids.all.length === 0 &&
              !visibleSolidsQuery.length && <LargeDAGNotice />}
            <PipelineGraphContainer
              pipelineName={pipeline.name}
              backgroundColor={backgroundColor}
              solids={queryResultSolids.all}
              focusSolids={queryResultSolids.focus}
              highlightedSolids={highlightedSolids}
              selectedHandle={selectedHandle}
              parentHandle={parentHandle}
              onClickSolid={this.handleClickSolid}
              onClickBackground={this.handleClickBackground}
              onEnterCompositeSolid={this.handleEnterCompositeSolid}
              onLeaveCompositeSolid={this.handleLeaveCompositeSolid}
            />
          </>
        }
        second={
          <RightInfoPanel>
            <Route
              // eslint-disable-next-line react/no-children-prop
              children={({ location }: { location: any }) => (
                <SidebarTabbedContainer
                  pipeline={pipeline}
                  solidHandleID={selectedHandle && selectedHandle.handleID}
                  parentSolidHandleID={parentHandle && parentHandle.handleID}
                  getInvocations={this.props.getInvocations}
                  onEnterCompositeSolid={this.handleEnterCompositeSolid}
                  onClickSolid={this.handleClickSolid}
                  {...querystring.parse(location.search || "")}
                />
              )}
            />
          </RightInfoPanel>
        }
      />
    );
  }
}

const RightInfoPanel = styled.div`
  // Fixes major perofmance hit. To reproduce, add enough content to
  // the sidebar that it scrolls (via overflow-y below) and then try
  // to pan the DAG.
  position: relative;

  height: 100%;
  overflow-y: scroll;
  background: ${Colors.WHITE};
`;

const OptionsOverlay = styled.div`
  z-index: 2;
  padding: 3px 15px;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  bottom: 0;
  left: 0;
`;

const SearchOverlay = styled.div`
  z-index: 2;
  padding: 7px 5px;
  display: inline-flex;
  align-items: stretch;
  position: absolute;
  top: 0;
  right: 0;
`;

const PathOverlay = styled.div`
  z-index: 2;
  padding: 7px;
  padding-left: 10px;
  max-width: 80%;
  display: inline-flex;
  align-items: center;
  position: absolute;
  left: 0;
`;

const SolidHighlightInput = styled(InputGroup)`
  margin-left: 7px;
  font-size: 14px;
  width: 220px;
`;

const LargeDAGNotice = () => (
  <LargeDAGContainer>
    <LargeDAGInstructionBox>
      <p>
        This is a large DAG that may be difficult to visualize. Type{" "}
        <code>*</code> in the subset box below to render the entire thing, or
        type a solid name and use:
      </p>
      <ul style={{ marginBottom: 0 }}>
        <li>
          <code>+</code> to expand a single layer before or after the solid.
        </li>
        <li>
          <code>*</code> to expand recursively before or after the solid.
        </li>
        <li>
          <code>AND</code> to render another disconnected fragment.
        </li>
      </ul>
    </LargeDAGInstructionBox>
    <Icon icon="arrow-down" iconSize={40} />
  </LargeDAGContainer>
);

const LargeDAGContainer = styled.div`
  width: 50vw;
  position: absolute;
  transform: translateX(-50%);
  left: 50%;
  bottom: 60px;
  z-index: 2;
  max-width: 600px;
  text-align: center;
  .bp3-icon {
    color: ${Colors.LIGHT_GRAY1};
  }
`;

const LargeDAGInstructionBox = styled.div`
  padding: 15px 20px;
  border: 1px solid #fff5c3;
  margin-bottom: 20px;
  color: ${Colors.DARK_GRAY3};
  background: #fffbe5;
  text-align: left;
  line-height: 1.4rem;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  code {
    background: #f8ebad;
    font-weight: 500;
    padding: 0 4px;
  }
`;
