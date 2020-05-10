import * as React from "react";
import gql from "graphql-tag";
import PipelineColorScale from "./PipelineColorScale";
import { IFullSolidLayout } from "./getFullSolidLayout";
import { SolidNodeInvocationFragment } from "./types/SolidNodeInvocationFragment";
import { SolidNodeDefinitionFragment } from "./types/SolidNodeDefinitionFragment";
import { SVGFlowLayoutRect, SVGMonospaceText } from "./SVGComponents";

import SolidTags, { ISolidTag } from "./SolidTags";
import { SolidConfigPort } from "./SolidConfigPort";
import { SolidIOBox, metadataForIO } from "./SolidIOBox";
import { Edge } from "./highlighting";

interface ISolidNodeProps {
  layout: IFullSolidLayout;
  invocation?: SolidNodeInvocationFragment;
  definition: SolidNodeDefinitionFragment;
  highlightedEdges: Edge[];
  minified: boolean;
  selected: boolean;
  focused: boolean;
  dim: boolean;
  onClick: () => void;
  onDoubleClick: () => void;
  onEnterComposite: () => void;
  onHighlightEdges: (edges: Edge[]) => void;
}

const SELECTED_STYLE = {
  stroke: "rgba(255, 69, 0, 1)",
  fill: "rgba(255, 69, 0, 0.2)",
  dashed: true
};
const FOCUSED_STYLE = {
  stroke: "rgba(59, 141, 227, 1)",
  fill: "rgba(59, 141, 227, 0.2)",
  dashed: false
};

export default class SolidNode extends React.Component<ISolidNodeProps> {
  static fragments = {
    SolidNodeInvocationFragment: gql`
      fragment SolidNodeInvocationFragment on Solid {
        name
        inputs {
          definition {
            name
          }
          dependsOn {
            definition {
              name
              type {
                displayName
              }
            }
            solid {
              name
            }
          }
        }
        outputs {
          definition {
            name
          }
          dependedBy {
            solid {
              name
            }
            definition {
              name
              type {
                displayName
              }
            }
          }
        }
      }
    `,
    SolidNodeDefinitionFragment: gql`
      fragment SolidNodeDefinitionFragment on ISolidDefinition {
        __typename
        name
        metadata {
          key
          value
        }
        inputDefinitions {
          name
          type {
            displayName
          }
        }
        outputDefinitions {
          name
          type {
            displayName
          }
        }
        ... on SolidDefinition {
          configField {
            configType {
              key
              description
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
    `
  };

  shouldComponentUpdate(prevProps: ISolidNodeProps) {
    if (prevProps.dim !== this.props.dim) return true;
    if (prevProps.selected !== this.props.selected) return true;
    if (prevProps.focused !== this.props.focused) return true;
    if (prevProps.minified !== this.props.minified) return true;
    if (prevProps.highlightedEdges !== this.props.highlightedEdges) return true;
    if (prevProps.layout !== this.props.layout) return true;
    if (
      (prevProps.invocation && prevProps.invocation.name) !==
      (this.props.invocation && this.props.invocation.name)
    )
      return true;
    return false;
  }

  handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onClick();
  };

  handleDoubleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onDoubleClick();
  };

  handleEnterComposite = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    this.props.onEnterComposite();
  };

  handleKindClicked = (e: React.MouseEvent) => {
    this.handleClick(e);
    window.requestAnimationFrame(() =>
      document.dispatchEvent(new Event("show-kind-info"))
    );
  };

  renderSurroundingBox(style: {
    stroke: string;
    fill: string;
    dashed: boolean;
  }) {
    const { x, y, width, height } = this.props.layout.boundingBox;
    return (
      <rect
        x={x - 10}
        y={y - 10}
        width={width + 20}
        height={
          height +
          (this.props.definition.outputDefinitions.length > 0 ? 20 : 30)
        }
        stroke={style.stroke}
        fill={style.fill}
        strokeWidth={this.props.minified ? 5 : 3}
        strokeDasharray={
          style.dashed ? (this.props.minified ? 8 : 4) : undefined
        }
      />
    );
  }

  renderSolid() {
    const { invocation, definition, layout, minified } = this.props;
    const composite = definition.__typename === "CompositeSolidDefinition";

    return (
      <SVGFlowLayoutRect
        {...layout.solid}
        fill={PipelineColorScale(
          composite
            ? "solidComposite"
            : invocation?.name.includes(".")
            ? "solidCompositeChild"
            : "solid"
        )}
        stroke="#979797"
        strokeWidth={1}
        spacing={0}
        padding={12}
      >
        <SVGMonospaceText
          size={minified ? 30 : 16}
          allowTwoLines={!minified}
          text={invocation ? invocation.name : definition.name}
          fill={"#222"}
        />
      </SVGFlowLayoutRect>
    );
  }

  public renderSolidCompositeIndicator() {
    const { x, y, width, height } = this.props.layout.solid;
    return (
      <>
        <rect
          x={x - 6}
          y={y - 6}
          width={width + 12}
          height={height + 12}
          fill={PipelineColorScale("solidComposite")}
          stroke="#979797"
          strokeWidth={1}
        />
        <rect
          x={x - 3}
          y={y - 3}
          width={width + 6}
          height={height + 6}
          fill={PipelineColorScale("solidComposite")}
          stroke="#979797"
          strokeWidth={1}
        />
      </>
    );
  }

  public render() {
    const {
      definition,
      invocation,
      layout,
      dim,
      focused,
      selected,
      minified
    } = this.props;
    const { metadata } = definition;
    const { x, y, width, height } = layout.solid;

    let configField = null;
    if (definition.__typename === "SolidDefinition") {
      configField = definition.configField;
    }

    const tags: ISolidTag[] = [];

    const kind = metadata.find(m => m.key === "kind");
    const composite = definition.__typename === "CompositeSolidDefinition";

    if (kind) {
      tags.push({ label: kind.value, onClick: this.handleKindClicked });
    }
    if (composite) {
      tags.push({ label: "Expand", onClick: this.handleEnterComposite });
    }

    return (
      <g
        onClick={this.handleClick}
        onDoubleClick={this.handleDoubleClick}
        opacity={dim ? 0.3 : undefined}
      >
        {selected
          ? this.renderSurroundingBox(SELECTED_STYLE)
          : focused
          ? this.renderSurroundingBox(FOCUSED_STYLE)
          : undefined}

        {composite && this.renderSolidCompositeIndicator()}

        {this.renderSolid()}

        {definition.inputDefinitions.map((item, idx) => (
          <SolidIOBox
            {...this.props}
            {...metadataForIO(item, invocation)}
            key={idx}
            item={item}
            layout={layout.inputs[item.name].layout}
            colorKey="input"
          />
        ))}

        {definition.outputDefinitions.map((item, idx) => (
          <SolidIOBox
            {...this.props}
            {...metadataForIO(item, invocation)}
            key={idx}
            item={item}
            layout={layout.outputs[item.name].layout}
            colorKey="output"
          />
        ))}

        {configField && (
          <SolidConfigPort x={x + width - 33} y={y - 13} minified={minified} />
        )}

        {tags.length > 0 && (
          <SolidTags
            x={x}
            y={y + height}
            width={width + 5}
            minified={minified}
            tags={tags}
          />
        )}
      </g>
    );
  }
}
