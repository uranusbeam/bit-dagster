import * as React from "react";
import { IconNames } from "@blueprintjs/icons";
import { Button, Intent, Tooltip, Position } from "@blueprintjs/core";
import { useMutation } from "react-apollo";
import ExecutionStartButton from "../execute/ExecutionStartButton";
import { PipelineRunStatus } from "../types/globalTypes";
import { ExecutionType } from "../LocalStorage";

import { CANCEL_MUTATION } from "./RunUtils";
import { SharedToaster } from "../DomUtils";
import { IStepState } from "../RunMetadataProvider";
import { formatStepKey } from "../Util";
import { LaunchButtonGroup } from "../execute/PipelineExecutionButtonGroup";

// Descriptions of buttons
const REEXECUTE_DESCRIPTION = "Re-execute the pipeline run from scratch";

const REEXECUTE_PIPELINE_UNKNOWN =
  "Re-execute is unavailable because the pipeline is not present in the current repository.";
const RETRY_DESCRIPTION =
  "Retries the pipeline run, skipping steps that completed successfully";
const RETRY_DISABLED =
  "Retries are only enabled on persistent storage. Try rerunning with a different storage configuration.";
const RETRY_PIPELINE_UNKNOWN =
  "Retry is unavailable because the pipeline is not present in the current repository.";

const REEXECUTE_SINGLE_STEP_NO_ARTIFACTS =
  "Use a persisting storage mode such as 'filesystem' to enable single step re-execution";
const REEXECUTE_SINGLE_STEP_NOT_DONE =
  "Wait for this step to finish to re-execute it.";
const REEXECUTE_SINGLE_STEP =
  "Re-run just this step with existing configuration.";

// Buttons using RunActionButtons
const START_REEXECUTE_TITLE = "Re-execute";
const LAUNCH_REEXECUTE_TITLE = "Launch Re-execution";

const START_RETRY_TITLE = "Resume / Retry";
const LAUNCH_RETRY_TITLE = "Launch Resume / Retry";
const RETRY_DISABLED_TITLE = "Resume / Retry";
const CANCEL_TITLE = "Terminate";

const getTitleForStartReexecuteSingleStep = (stepLabel: string) =>
  `Re-execute ${stepLabel}`;

const getTitleForLaunchReexecuteSingleStep = (stepLabel: string) =>
  `Re-launch ${stepLabel}`;

interface RunActionButtonsRun {
  runId: string;
  status: PipelineRunStatus;
  pipeline: {
    __typename: string;
  };
  canCancel: boolean;
}

interface RunActionButtonsProps {
  run?: RunActionButtonsRun;
  selectedStep: string | null;
  selectedStepState: IStepState;
  artifactsPersisted: boolean;
  executionPlan?: {
    artifactsPersisted: boolean;
  } | null;
  onExecute: (stepKey?: string, resumeRetry?: boolean) => Promise<void>;
  onLaunch: (stepKey?: string, resumeRetry?: boolean) => Promise<void>;
}

const CancelRunButton: React.FunctionComponent<{
  run: RunActionButtonsRun;
}> = ({ run }) => {
  const [cancel] = useMutation(CANCEL_MUTATION);
  const [inFlight, setInFlight] = React.useState(false);
  return (
    <Button
      icon={IconNames.STOP}
      small={true}
      text={CANCEL_TITLE}
      intent="warning"
      disabled={inFlight}
      onClick={async () => {
        setInFlight(true);
        const res = await cancel({
          variables: { runId: run.runId }
        });
        setInFlight(false);
        if (res.data?.cancelPipelineExecution?.message) {
          SharedToaster.show({
            message: res.data.cancelPipelineExecution.message,
            icon: "error",
            intent: Intent.DANGER
          });
        }
      }}
    />
  );
};

interface ReexecuteButtonProps {
  stepName: string;
  stepState: IStepState;
  artifactsPersisted: boolean;
  onExecute: (stepKey?: string, resumeRetry?: boolean) => void;
  onLaunch: (stepKey?: string, resumeRetry?: boolean) => void;
  onChangeExecutionType?: (type: ExecutionType) => void;
}

export function ReexecuteSingleStepButton(props: ReexecuteButtonProps) {
  const {
    onExecute,
    onLaunch,
    stepState,
    artifactsPersisted,
    stepName,
    onChangeExecutionType
  } = props;
  const stepLabel = formatStepKey(stepName);
  const stepInFlight = ![IStepState.FAILED, IStepState.SUCCEEDED].includes(
    stepState
  );

  // if execution artifacts are not persisted, we can reexecute but we want to communicate
  // that we could if configuration was changed
  return (
    <Tooltip
      hoverOpenDelay={300}
      position={Position.BOTTOM}
      content={
        stepInFlight
          ? REEXECUTE_SINGLE_STEP_NOT_DONE
          : !artifactsPersisted
          ? REEXECUTE_SINGLE_STEP_NO_ARTIFACTS
          : REEXECUTE_SINGLE_STEP
      }
    >
      <LaunchButtonGroup small={true} onChange={onChangeExecutionType}>
        <ExecutionStartButton
          title={getTitleForStartReexecuteSingleStep(stepLabel)}
          icon={IconNames.REPEAT}
          small={true}
          disabled={stepInFlight || !artifactsPersisted}
          onClick={onExecute}
        />
        <ExecutionStartButton
          title={getTitleForLaunchReexecuteSingleStep(stepLabel)}
          icon={IconNames.REPEAT}
          small={true}
          disabled={stepInFlight || !artifactsPersisted}
          onClick={onLaunch}
        />
      </LaunchButtonGroup>
    </Tooltip>
  );
}

export const RunActionButtons: React.FunctionComponent<RunActionButtonsProps> = props => {
  const { run, executionPlan, onExecute, onLaunch } = props;
  // TODO: temporary hack to try to force rerender of the action buttons based on
  // the local storage state.  Real solution is to push the LaunchButtonGroup to use
  // context (https://github.com/dagster-io/dagster/issues/2153)
  const [, updateState] = React.useState<ExecutionType>(ExecutionType.START);
  const isUnknown = run?.pipeline.__typename === "UnknownPipeline";

  return (
    <>
      {props.selectedStep && (
        <ReexecuteSingleStepButton
          stepName={props.selectedStep}
          stepState={props.selectedStepState}
          onExecute={() => onExecute(props.selectedStep || undefined)}
          onLaunch={() => onLaunch(props.selectedStep || undefined)}
          onChangeExecutionType={updateState}
          artifactsPersisted={props.artifactsPersisted}
        />
      )}

      <Tooltip
        hoverOpenDelay={300}
        position={Position.BOTTOM}
        content={isUnknown ? REEXECUTE_PIPELINE_UNKNOWN : REEXECUTE_DESCRIPTION}
      >
        <LaunchButtonGroup small={true} onChange={updateState}>
          <ExecutionStartButton
            title={START_REEXECUTE_TITLE}
            icon={IconNames.REPEAT}
            small={true}
            disabled={isUnknown}
            onClick={() => onExecute()}
          />
          <ExecutionStartButton
            title={LAUNCH_REEXECUTE_TITLE}
            icon={IconNames.REPEAT}
            small={true}
            disabled={isUnknown}
            onClick={() => onLaunch()}
          />
        </LaunchButtonGroup>
      </Tooltip>

      {run?.canCancel && (
        <>
          <div style={{ minWidth: 6 }} />
          <CancelRunButton run={run} />
        </>
      )}

      {executionPlan &&
        run &&
        run.status === PipelineRunStatus.FAILURE &&
        (executionPlan.artifactsPersisted ? (
          <Tooltip
            hoverOpenDelay={300}
            content={isUnknown ? RETRY_PIPELINE_UNKNOWN : RETRY_DESCRIPTION}
            position={Position.BOTTOM}
          >
            <LaunchButtonGroup small={true} onChange={updateState}>
              <ExecutionStartButton
                title={START_RETRY_TITLE}
                icon={IconNames.REPEAT}
                small={true}
                disabled={isUnknown}
                onClick={() => onExecute(undefined, true)}
              />
              <ExecutionStartButton
                title={LAUNCH_RETRY_TITLE}
                icon={IconNames.REPEAT}
                small={true}
                disabled={isUnknown}
                onClick={() => onLaunch(undefined, true)}
              />
            </LaunchButtonGroup>
          </Tooltip>
        ) : (
          <Tooltip
            hoverOpenDelay={300}
            content={RETRY_DISABLED}
            position={Position.BOTTOM}
          >
            <ExecutionStartButton
              title={RETRY_DISABLED_TITLE}
              icon={IconNames.DISABLE}
              small={true}
              disabled
              onClick={() => null}
            />
          </Tooltip>
        ))}
    </>
  );
};
