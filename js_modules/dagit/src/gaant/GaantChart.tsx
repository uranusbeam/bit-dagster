import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components";
import { isEqual } from "lodash";
import { Colors, Checkbox } from "@blueprintjs/core";

import { weakmapMemoize } from "../Util";
import { GaantChartExecutionPlanFragment } from "./types/GaantChartExecutionPlanFragment";
import { GaantChartTimescale } from "./GaantChartTimescale";
import { RunFragment } from "../runs/types/RunFragment";
import { GraphQueryInput } from "../GraphQueryInput";
import { filterByQuery, GraphQueryItem } from "../GraphQueryImpl";
import { IRunMetadataDict, EMPTY_RUN_METADATA } from "../RunMetadataProvider";
import {
  buildLayout,
  boxStyleFor,
  interestingQueriesFor,
  adjustLayoutWithRunMetadata,
  BuildLayoutParams
} from "./GaantChartLayout";
import {
  GaantChartLayoutOptions,
  GaantChartLayout,
  GaantChartMode,
  GaantChartBox,
  IGaantNode,
  DEFAULT_OPTIONS,
  BOX_HEIGHT,
  BOX_MARGIN_Y,
  BOX_SPACING_X,
  LINE_SIZE,
  CSS_DURATION,
  BOX_DOT_WIDTH_CUTOFF,
  BOX_SHOW_LABEL_WIDTH_CUTOFF,
  BOX_DOT_SIZE,
  MIN_SCALE,
  MAX_SCALE,
  GaantViewport,
  GaantChartPlacement
} from "./Constants";
import { SplitPanelContainer } from "../SplitPanelContainer";
import { GaantChartModeControl } from "./GaantChartModeControl";
import { GaantStatusPanel } from "./GaantStatusPanel";
import { ZoomSlider } from "./ZoomSlider";
import { useViewport } from "./useViewport";

export { GaantChartMode } from "./Constants";

const HIGHLIGHT_TIME_EVENT = "gaant-highlight-time";

let highlightTimer: NodeJS.Timeout;

/**
 * Set or clear the highlighted time on the Gaant chart. Goal of this convenience
 * method is to make the implementation (via event dispatch) private to this file.
 */
export function setHighlightedGaantChartTime(
  timestamp: null | string,
  debounced = true
) {
  clearTimeout(highlightTimer);

  if (debounced) {
    highlightTimer = setTimeout(
      () => setHighlightedGaantChartTime(timestamp, false),
      100
    );
  } else {
    document.dispatchEvent(
      new CustomEvent(HIGHLIGHT_TIME_EVENT, { detail: timestamp })
    );
  }
}

/**
 * Converts a Run execution plan into a tree of `GraphQueryItem` items that
 * can be used as the input to the "solid query" filtering algorithm. The idea
 * is that this data structure is generic, but it's really a fake solid tree.
 */
export const toGraphQueryItems = weakmapMemoize(
  (plan: GaantChartExecutionPlanFragment) => {
    const nodeTable: { [key: string]: IGaantNode } = {};

    for (const step of plan.steps) {
      const node: IGaantNode = {
        name: step.key,
        inputs: [],
        outputs: []
      };
      nodeTable[step.key] = node;
    }

    for (const step of plan.steps) {
      for (const input of step.inputs) {
        nodeTable[step.key].inputs.push({
          dependsOn: input.dependsOn.map(d => ({
            solid: {
              name: d.key
            }
          }))
        });

        for (const upstream of input.dependsOn) {
          let output = nodeTable[upstream.key].outputs[0];
          if (!output) {
            output = {
              dependedBy: []
            };
            nodeTable[upstream.key].outputs.push(output);
          }
          output.dependedBy.push({
            solid: { name: step.key }
          });
        }
      }
    }

    return Object.values(nodeTable);
  }
);

interface GaantChartProps {
  selectedStep: string | null;
  plan: GaantChartExecutionPlanFragment;
  options?: Partial<GaantChartLayoutOptions>;
  metadata?: IRunMetadataDict;
  toolbarActions?: React.ReactChild;
  toolbarLeftActions?: React.ReactChild;
  run?: RunFragment;

  onApplyStepFilter?: (step: string) => void;
}

interface GaantChartState {
  options: GaantChartLayoutOptions;
  query: string;
}

export class GaantChart extends React.Component<
  GaantChartProps,
  GaantChartState
> {
  static fragments = {
    GaantChartExecutionPlanFragment: gql`
      fragment GaantChartExecutionPlanFragment on ExecutionPlan {
        steps {
          key
          kind
        }
        steps {
          key
          inputs {
            dependsOn {
              key
              outputs {
                name
                type {
                  name
                }
              }
            }
          }
        }
        artifactsPersisted
      }
    `
  };

  _cachedLayout: GaantChartLayout | null = null;
  _cachedLayoutParams: BuildLayoutParams | null = null;

  constructor(props: GaantChartProps) {
    super(props);

    this.state = {
      query: "*",
      options: {
        ...DEFAULT_OPTIONS,
        ...props.options
      }
    };
  }

  getLayout = (params: BuildLayoutParams) => {
    if (
      !this._cachedLayoutParams ||
      this._cachedLayoutParams.nodes !== params.nodes ||
      this._cachedLayoutParams.mode !== params.mode
    ) {
      this._cachedLayout = buildLayout(params);
      this._cachedLayoutParams = params;
    }
    return this._cachedLayout!;
  };

  updateOptions = (changes: Partial<GaantChartLayoutOptions>) => {
    this.setState({
      ...this.state,
      options: { ...this.state.options, ...changes }
    });
  };

  onUpdateQuery = (query: string) => {
    this.setState({ query });
  };

  onDoubleClickStep = (stepKey: string) => {
    const query = `*${stepKey}*`;
    this.setState({ query: this.state.query !== query ? query : "*" });
  };

  render() {
    const { plan } = this.props;
    const { query, options } = this.state;

    const graph = toGraphQueryItems(plan);
    const graphFiltered = filterByQuery(graph, query);

    const layout = this.getLayout({
      nodes: graphFiltered.all,
      mode: options.mode
    });

    return (
      <GaantChartContainer>
        <OptionsContainer>
          {this.props.toolbarLeftActions}
          {this.props.toolbarLeftActions && <OptionsDivider />}
          <GaantChartModeControl
            value={options.mode}
            onChange={mode => this.updateOptions({ mode })}
            hideTimedMode={options.hideTimedMode}
          />
          {options.mode === GaantChartMode.WATERFALL_TIMED && (
            <>
              <div style={{ width: 15 }} />
              <div style={{ width: 200 }}>
                <ZoomSlider
                  value={options.zoom}
                  onChange={v => this.updateOptions({ zoom: v })}
                />
              </div>
              <div style={{ width: 15 }} />
              <Checkbox
                style={{ marginBottom: 0 }}
                label="Hide not started steps"
                checked={options.hideWaiting}
                onClick={() =>
                  this.updateOptions({ hideWaiting: !options.hideWaiting })
                }
              />
            </>
          )}
          <div style={{ flex: 1 }} />
          {this.props.toolbarActions}
        </OptionsContainer>
        <GaantChartInner
          {...this.props}
          {...this.state}
          layout={layout}
          graph={graph}
          onUpdateQuery={this.onUpdateQuery}
          onDoubleClickStep={this.onDoubleClickStep}
        />
      </GaantChartContainer>
    );
  }
}
type GaantChartInnerProps = GaantChartProps &
  GaantChartState & {
    graph: GraphQueryItem[];
    layout: GaantChartLayout;
    onUpdateQuery: (value: string) => void;
    onDoubleClickStep: (stepName: string) => void;
  };

interface TooltipState {
  text: string;
  cx: number;
  cy: number;
}

const GaantChartInner = (props: GaantChartInnerProps) => {
  const { viewport, containerProps, onMoveToViewport } = useViewport();
  const [hoveredStep, setHoveredNodeName] = React.useState<string | null>(null);
  const [hoveredTime, setHoveredTime] = React.useState<number | null>(null);
  const [tooltip, setTooltip] = React.useState<TooltipState | null>(null);
  const [nowMs, setNowMs] = React.useState<number>(Date.now());
  const { options, metadata } = props;

  // The slider in the UI updates `options.zoom` from 1-100. We convert that value
  // into a px-per-ms "scale", where the minimum is the value required to zoom-to-fit.
  // To make the slider feel more linear, we convert the input from log10 to logE.
  let minScale = MIN_SCALE;
  if (viewport.width && metadata && metadata.firstLogAt) {
    const zoomToFitWidthPx = Math.max(1, viewport.width - 150);
    const elapsedMs = Math.max(1, nowMs - metadata.firstLogAt);
    minScale = zoomToFitWidthPx / elapsedMs;
  }

  const scale = Math.exp(
    Math.log(minScale) +
      ((Math.log(MAX_SCALE) - Math.log(minScale)) / 100) * options.zoom
  );

  // When the pipeline is running we want the graph to be steadily moving, even if logs
  // aren't arriving. To achieve this we determine an update interval based on the scale
  // and advance a "now" value that is used as the currnet time when adjusting the layout
  // to account for run metadata below.

  // Because renders can happen "out of band" of our update interval, we set a timer for
  // "time until the next interval after the current nowMs".
  React.useEffect(() => {
    if (scale === 0) return;
    if (metadata?.exitedAt) {
      if (nowMs !== metadata.exitedAt) {
        setNowMs(metadata.exitedAt);
      }
      return;
    }

    // time required for 2px shift in viz, but not more rapid than our CSS animation duration
    const renderInterval = Math.max(CSS_DURATION, 2 / scale);

    const timeUntilIntervalElasped = renderInterval - (Date.now() - nowMs);
    const timeout = setTimeout(
      () => setNowMs(Date.now()),
      timeUntilIntervalElasped
    );
    return () => clearTimeout(timeout);
  }, [scale, setNowMs, metadata, nowMs]);

  // Listen for events specifying hover time (eg: a marker at a particular timestamp)
  // and sync them to our React state for display.
  React.useEffect(() => {
    const listener = (e: CustomEvent) => setHoveredTime(e.detail);
    document.addEventListener(HIGHLIGHT_TIME_EVENT, listener);
    return () => document.removeEventListener(HIGHLIGHT_TIME_EVENT, listener);
  });

  // The `layout` we receive has been laid out and the rows / "waterfall" are final,
  // but it doesn't incorporate the display scale or run metadata. We stretch and
  // shift the layout boxes using this data to create the final layout for display.
  const layout = adjustLayoutWithRunMetadata(
    props.layout,
    options,
    metadata || EMPTY_RUN_METADATA,
    scale,
    nowMs
  );
  const layoutSize = {
    width: Math.max(0, ...layout.boxes.map(b => b.x + b.width + BOX_SPACING_X)),
    height: Math.max(0, ...layout.boxes.map(b => b.y * BOX_HEIGHT + BOX_HEIGHT))
  };

  React.useEffect(() => {
    const node = layout.boxes.find(b => b.node.name === props.selectedStep);
    if (!node) {
      return;
    }
    const bounds = boundsForBox(node);
    const x = (bounds.maxX + bounds.minX) / 2 - viewport.width / 2;
    const y = (bounds.maxY + bounds.minY) / 2 - viewport.height / 2;
    onMoveToViewport({ left: x, top: y }, true);
  }, [props.selectedStep]); // eslint-disable-line

  const onUpdateTooltip = (e: React.MouseEvent<any>) => {
    if (!(e.target instanceof HTMLElement)) return;
    const tooltippedEl = e.target.closest("[data-tooltip-text]");
    const text =
      tooltippedEl &&
      tooltippedEl instanceof HTMLElement &&
      tooltippedEl.dataset.tooltipText;

    if (text && (!tooltip || tooltip.text !== text)) {
      const bounds = tooltippedEl!.getBoundingClientRect();
      setTooltip({
        text,
        cx: bounds.left,
        cy: bounds.bottom
      });
    } else if (!text && tooltip) {
      setTooltip(null);
    }
  };

  const highlightedMs: number[] = [];
  if (hoveredTime) {
    highlightedMs.push(hoveredTime);
  } else if (props.selectedStep) {
    const meta = metadata?.steps[props.selectedStep];
    meta && meta.start && highlightedMs.push(meta.start);
    meta && meta.end && highlightedMs.push(meta.end);
  }

  const content = (
    <>
      {options.mode === GaantChartMode.WATERFALL_TIMED && (
        <GaantChartTimescale
          scale={scale}
          viewport={viewport}
          layoutSize={layoutSize}
          startMs={metadata?.firstLogAt || 0}
          highlightedMs={highlightedMs}
          nowMs={nowMs}
        />
      )}
      <div style={{ overflow: "scroll", flex: 1 }} {...containerProps}>
        <div
          style={{ position: "relative", ...layoutSize }}
          onMouseOver={onUpdateTooltip}
          onMouseOut={onUpdateTooltip}
        >
          <GaantChartViewportContents
            options={options}
            metadata={metadata || EMPTY_RUN_METADATA}
            layout={layout}
            hoveredStep={hoveredStep}
            focusedStep={props.selectedStep}
            viewport={viewport}
            setHoveredNodeName={setHoveredNodeName}
            onApplyStepFilter={props.onApplyStepFilter}
            onDoubleClickStep={props.onDoubleClickStep}
          />
        </div>
        {tooltip && (
          <GaantTooltip style={{ left: tooltip.cx, top: tooltip.cy }}>
            {tooltip.text}
          </GaantTooltip>
        )}
      </div>

      <GraphQueryInput
        items={props.graph}
        value={props.query}
        placeholder="Type a Step Subset"
        onChange={props.onUpdateQuery}
        presets={metadata ? interestingQueriesFor(metadata, layout) : undefined}
      />
    </>
  );

  return metadata ? (
    <SplitPanelContainer
      identifier="gaant-split"
      axis="horizontal"
      first={content}
      firstInitialPercent={80}
      second={
        <GaantStatusPanel
          {...props}
          nowMs={nowMs}
          metadata={metadata}
          onHighlightStep={name => setHoveredNodeName(name)}
        />
      }
    />
  ) : (
    content
  );
};

interface GaantChartViewportContentsProps {
  options: GaantChartLayoutOptions;
  metadata: IRunMetadataDict;
  layout: GaantChartLayout;
  hoveredStep: string | null;
  focusedStep: string | null;
  viewport: GaantViewport;
  setHoveredNodeName: (name: string | null) => void;
  onDoubleClickStep: (step: string) => void;
  onApplyStepFilter?: (step: string) => void;
}

const GaantChartViewportContents: React.FunctionComponent<GaantChartViewportContentsProps> = props => {
  const {
    viewport,
    layout,
    hoveredStep,
    focusedStep,
    metadata,
    options
  } = props;
  const items: React.ReactChild[] = [];

  // To avoid drawing zillions of DOM nodes, we render only the boxes + lines that
  // intersect with the current viewport.
  const intersectsViewport = (bounds: Bounds) =>
    bounds.minX < viewport.left + viewport.width &&
    bounds.maxX > viewport.left &&
    bounds.minY < viewport.top + viewport.height &&
    bounds.maxY > viewport.top;

  if (options.mode !== GaantChartMode.FLAT) {
    layout.boxes.forEach(box => {
      box.children.forEach((child, childIdx) => {
        const bounds = boundsForLine(box, child);
        if (!intersectsViewport(bounds)) {
          return;
        }
        const childNotDrawn = !layout.boxes.includes(child);
        const childWaiting = metadata
          ? !metadata.steps[child.node.name]?.state
          : false;

        items.push(
          <GaantLine
            darkened={
              (focusedStep || hoveredStep) === box.node.name ||
              (focusedStep || hoveredStep) === child.node.name
            }
            dotted={childNotDrawn || childWaiting}
            key={`${box.key}-${child.key}-${childIdx}`}
            depNotDrawn={childNotDrawn}
            depIdx={childIdx}
            {...bounds}
          />
        );
      });
    });
  }

  layout.boxes.forEach(box => {
    const bounds = boundsForBox(box);
    const useDot = box.width === BOX_DOT_WIDTH_CUTOFF;
    if (!intersectsViewport(bounds)) {
      return;
    }

    items.push(
      <div
        key={box.key}
        data-tooltip-text={
          box.width < box.node.name.length * 5 ? box.node.name : undefined
        }
        onClick={() => props.onApplyStepFilter?.(box.node.name)}
        onDoubleClick={() => props.onDoubleClickStep?.(box.node.name)}
        onMouseEnter={() => props.setHoveredNodeName(box.node.name)}
        onMouseLeave={() => props.setHoveredNodeName(null)}
        className={`
            chart-element
            ${useDot ? "dot" : "box"}
            ${focusedStep === box.node.name && "focused"}
            ${hoveredStep === box.node.name && "hovered"}`}
        style={{
          left: bounds.minX,
          top:
            bounds.minY +
            (useDot ? (BOX_HEIGHT - BOX_DOT_SIZE) / 2 : BOX_MARGIN_Y),
          width: useDot ? BOX_DOT_SIZE : box.width,
          ...boxStyleFor(box.state, { metadata, options })
        }}
      >
        {box.width > BOX_SHOW_LABEL_WIDTH_CUTOFF ? box.node.name : undefined}
      </div>
    );
  });

  if (options.mode === GaantChartMode.WATERFALL_TIMED) {
    // Note: We sort the markers from left to right so that they're added to the DOM in that
    // order and a long one doesn't make ones "behind it" unclickable.
    layout.markers
      .map((marker, idx) => ({ marker, idx, bounds: boundsForBox(marker) }))
      .filter(({ bounds }) => intersectsViewport(bounds))
      .sort((a, b) => a.bounds.minX - b.bounds.minX)
      .forEach(({ marker, bounds, idx }) => {
        const useDot = marker.width === BOX_DOT_WIDTH_CUTOFF;

        items.push(
          <div
            key={idx}
            data-tooltip-text={marker.key}
            className={`
            chart-element
            ${useDot ? "marker-dot" : "marker-whiskers"}`}
            style={{
              left: bounds.minX,
              top:
                bounds.minY +
                (useDot ? (BOX_HEIGHT - BOX_DOT_SIZE) / 2 : BOX_MARGIN_Y),
              width: useDot ? BOX_DOT_SIZE : marker.width
            }}
          >
            <div />
          </div>
        );
      });
  }

  return <>{items}</>;
};

interface Bounds {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

/**
 * Returns the top left + bottom right bounds for the provided Gaant chart box
 * so that the box can be drawn and tested for intersection with the viewport.
 */
const boundsForBox = (a: GaantChartPlacement): Bounds => {
  return {
    minX: a.x,
    minY: a.y * BOX_HEIGHT,
    maxX: a.x + a.width,
    maxY: a.y * BOX_HEIGHT + BOX_HEIGHT
  };
};

/**
 * Returns the top left + bottom right bounds for the line between two Gaant
 * chart boxes. The boxes do not need to be provided in left -> right order.
 * @param a: GaantChartBox
 */
const boundsForLine = (a: GaantChartBox, b: GaantChartBox): Bounds => {
  const minIdx = Math.min(a.y, b.y);
  const maxIdx = Math.max(a.y, b.y);

  const straight = maxIdx === minIdx;
  const maxY = straight
    ? maxIdx * BOX_HEIGHT + BOX_HEIGHT / 2
    : maxIdx * BOX_HEIGHT + BOX_MARGIN_Y;
  const minY = straight
    ? minIdx * BOX_HEIGHT + BOX_HEIGHT / 2
    : minIdx * BOX_HEIGHT + BOX_HEIGHT / 2;

  const minX = Math.min(a.x + a.width, b.x + b.width);
  const maxX =
    maxIdx === minIdx
      ? Math.max(a.x, b.x)
      : Math.max(a.x + a.width / 2, b.x + b.width / 2);

  return { minX, minY, maxX, maxY };
};

/**
 * Renders a line on the Gaant visualization using a thin horizontal <div> and
 * a thin vertical <div> as necessary.
 */
const GaantLine = React.memo(
  ({
    minX,
    minY,
    maxX,
    maxY,
    dotted,
    darkened,
    depIdx,
    depNotDrawn
  }: {
    dotted: boolean;
    darkened: boolean;
    depIdx: number;
    depNotDrawn: boolean;
  } & Bounds) => {
    const border = `${LINE_SIZE}px ${dotted ? "dotted" : "solid"} ${
      darkened ? Colors.DARK_GRAY1 : Colors.LIGHT_GRAY3
    }`;

    return (
      <>
        <div
          className="line"
          style={{
            height: 1,
            left: minX,
            width: depNotDrawn ? 50 : maxX + (depIdx % 10) * LINE_SIZE - minX,
            top: minY - 1,
            borderTop: border,
            zIndex: darkened ? 100 : 1
          }}
        />
        {minY !== maxY && !depNotDrawn && (
          <div
            className="line"
            style={{
              width: 1,
              left: maxX + (depIdx % 10) * LINE_SIZE,
              top: minY,
              height: maxY - minY,
              borderRight: border,
              zIndex: darkened ? 100 : 1
            }}
          />
        )}
      </>
    );
  },
  isEqual
);

// Note: It is much faster to use standard CSS class selectors here than make
// each box and line a styled-component because all styled components register
// listeners for the "theme" React context.
const GaantChartContainer = styled.div`
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  z-index: 2;
  user-select: none;
  background: ${Colors.WHITE};

  .line {
    position: absolute;
    user-select: none;
    pointer-events: none;
    transition: top ${CSS_DURATION}ms linear, left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear, height ${CSS_DURATION}ms linear;
  }

  .chart-element {
    font-size: 11px;
    transition: top ${CSS_DURATION}ms linear, left ${CSS_DURATION}ms linear;
    display: inline-block;
    position: absolute;
    color: white;
    overflow: hidden;
    user-select: text;
    z-index: 2;
  }

  .dot {
    width: ${BOX_DOT_SIZE}px;
    height: ${BOX_DOT_SIZE}px;
    border: 1px solid transparent;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    border-radius: ${BOX_DOT_SIZE / 2}px;
  }

  .box {
    height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
    padding: 2px;
    border: 1px solid transparent;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    border-radius: 2px;

    transition: top ${CSS_DURATION}ms linear, left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear, height ${CSS_DURATION}ms linear;

    &.focused {
      border: 1px solid ${Colors.DARK_GRAY1};
      box-shadow: 0 0 0 2px ${Colors.GOLD3};
    }
    &.hovered {
      border: 1px solid ${Colors.DARK_GRAY3};
    }
  }

  .marker-dot {
    width: ${BOX_DOT_SIZE}px;
    height: ${BOX_DOT_SIZE}px;
    border: 1px solid rgb(27, 164, 206);
    border-radius: ${BOX_DOT_SIZE / 2}px;
  }
  .marker-whiskers {
    display: inline-block;
    position: absolute;
    height: ${BOX_HEIGHT - BOX_MARGIN_Y * 2}px;
    background: rgba(27, 164, 206, 0.09);
    border-left: 1px solid rgba(27, 164, 206, 0.6);
    border-right: 1px solid rgba(27, 164, 206, 0.6);
    transition: top ${CSS_DURATION}ms linear, left ${CSS_DURATION}ms linear,
      width ${CSS_DURATION}ms linear;

    & > div {
      border-bottom: 1px dashed rgba(27, 164, 206, 0.6);
      height: ${(BOX_HEIGHT - BOX_MARGIN_Y * 2) / 2}px;
    }
  }
`;

const GaantTooltip = styled.div`
  position: fixed;
  font-size: 11px;
  padding: 3px;
  color: #a88860;
  background: #fffaf5;
  border: 1px solid #dbc5ad;
  transform: translate(5px, 5px);
  z-index: 100;
`;
const OptionsContainer = styled.div`
  min-height: 40px;
  display: flex;
  align-items: center;
  padding: 5px 15px;
  border-bottom: 1px solid #A7B6C2;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  background: ${Colors.WHITE};
  flex-shrink: 0;
  flex-wrap: wrap;
  z-index: 3;
}`;

const OptionsDivider = styled.div`
  width: 1px;
  height: 25px;
  padding-left: 7px;
  margin-left: 7px;
  border-left: 1px solid ${Colors.LIGHT_GRAY3};
`;
