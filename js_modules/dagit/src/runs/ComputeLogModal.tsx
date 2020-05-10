import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Dialog, Spinner, Intent } from "@blueprintjs/core";
import { RunContext } from "../runs/RunContext";
import { IStepState } from "../RunMetadataProvider";
import { DirectGraphQLSubscription } from "../DirectGraphQLSubscription";
import { ComputeLogContent } from "./ComputeLogContent";
import { ComputeLogsSubscription } from "./types/ComputeLogsSubscription";
import { ComputeLogsSubscriptionFragment } from "./types/ComputeLogsSubscriptionFragment";
import { ComputeLogContentFileFragment } from "./types/ComputeLogContentFileFragment";
import { ComputeIOType } from "../types/globalTypes";

const MAX_STREAMING_LOG_BYTES = 5242880; // 5 MB

interface IComputeLogLink {
  children: React.ReactNode;
  runState: IStepState;
  stepKey: string;
}

export const ComputeLogLink = ({
  runState,
  stepKey,
  children
}: IComputeLogLink) => {
  const [isOpen, setOpen] = React.useState(false);
  const run = React.useContext(RunContext);

  if (!run || !run.runId || runState === IStepState.SKIPPED) {
    return null;
  }

  const open = (e: React.SyntheticEvent) => {
    e.stopPropagation();
    setOpen(true);
  };
  const close = () => setOpen(false);
  return (
    <>
      <span onClick={open}>{children}</span>
      <Dialog
        onClose={close}
        style={{
          width: "100vw",
          height: "100vh",
          margin: 0,
          padding: 0,
          borderRadius: 0
        }}
        usePortal={true}
        isOpen={isOpen}
      >
        {isOpen ? (
          <ComputeLogModal
            runId={run.runId}
            runState={runState}
            stepKey={stepKey}
            onRequestClose={close}
          />
        ) : (
          <LoadingContainer>
            <Spinner intent={Intent.NONE} size={32} />
          </LoadingContainer>
        )}
      </Dialog>
    </>
  );
};

interface ComputeLogModalProps {
  runId: string;
  stepKey: string;
  runState: IStepState;
  onRequestClose: () => void;
}

export const ComputeLogModal = ({
  runId,
  onRequestClose,
  stepKey,
  runState
}: ComputeLogModalProps) => {
  return (
    <ComputeLogsProvider
      runId={runId}
      stepKey={stepKey}
      maxBytes={MAX_STREAMING_LOG_BYTES}
    >
      {({ isLoading, stdout, stderr, maxBytes }) => {
        if (isLoading) {
          return (
            <LoadingContainer>
              <Spinner intent={Intent.NONE} size={32} />
            </LoadingContainer>
          );
        }

        return (
          <ComputeLogContent
            runState={runState}
            onRequestClose={onRequestClose}
            stdout={stdout}
            stderr={stderr}
            maxBytes={maxBytes}
          />
        );
      }}
    </ComputeLogsProvider>
  );
};

interface IComputeLogsProviderProps {
  children: (props: {
    isLoading: boolean;
    stdout: ComputeLogsSubscriptionFragment | null;
    stderr: ComputeLogsSubscriptionFragment | null;
    maxBytes: number;
  }) => React.ReactChild;
  runId: string;
  stepKey: string;
  maxBytes: number;
}
interface IComputeLogsProviderState {
  stdout: ComputeLogsSubscriptionFragment | null;
  stderr: ComputeLogsSubscriptionFragment | null;
  isLoading: boolean;
}

export class ComputeLogsProvider extends React.Component<
  IComputeLogsProviderProps,
  IComputeLogsProviderState
> {
  static fragments = {
    subscription: gql`
      fragment ComputeLogsSubscriptionFragment on ComputeLogFile {
        data
        cursor
        ...ComputeLogContentFileFragment
      }
      ${ComputeLogContent.fragments.ComputeLogContentFragment}
    `
  };

  _stdout: DirectGraphQLSubscription<ComputeLogsSubscription>;
  _stderr: DirectGraphQLSubscription<ComputeLogsSubscription>;
  state: IComputeLogsProviderState = {
    stdout: null,
    stderr: null,
    isLoading: true
  };

  componentDidMount() {
    this.subscribe();
  }

  componentWillUnmount() {
    this.unsubscribe();
  }

  componentDidUpdate(prevProps: IComputeLogsProviderProps) {
    if (
      prevProps.runId !== this.props.runId ||
      prevProps.stepKey !== this.props.stepKey
    ) {
      this.unsubscribe();
      this.subscribe();
    }
  }

  subscribe() {
    const { runId, stepKey } = this.props;
    this.setState({ isLoading: true });
    this._stdout = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      COMPUTE_LOGS_SUBSCRIPTION,
      { runId, stepKey, ioType: ComputeIOType.STDOUT, cursor: null },
      this.onStdout,
      this.onError
    );
    this._stderr = new DirectGraphQLSubscription<ComputeLogsSubscription>(
      COMPUTE_LOGS_SUBSCRIPTION,
      { runId, stepKey, ioType: ComputeIOType.STDERR, cursor: null },
      this.onStderr,
      this.onError
    );
  }

  unsubscribe() {
    if (this._stdout) {
      this._stdout.close();
    }
    if (this._stderr) {
      this._stderr.close();
    }
  }

  onStdout = (messages: ComputeLogsSubscription[], _: boolean) => {
    this.onMessages("stdout", messages);
  };

  onStderr = (messages: ComputeLogsSubscription[], _: boolean) => {
    this.onMessages("stderr", messages);
  };

  onMessages = (ioType: string, messages: ComputeLogsSubscription[]) => {
    let computeLogs = this.state[ioType];
    messages.forEach((subscription: ComputeLogsSubscription) => {
      computeLogs = this.merge(computeLogs, subscription.computeLogs);
    });

    if (ioType === "stdout") {
      this.setState({ stdout: computeLogs, isLoading: false });
    } else {
      this.setState({ stderr: computeLogs, isLoading: false });
    }
  };

  onError = () => {
    this.setState({ isLoading: false });
  };

  merge(
    a: ComputeLogContentFileFragment | null,
    b: ComputeLogContentFileFragment | null
  ) {
    if (!b) return a;
    let data = a?.data;
    if (a?.data && b?.data) {
      data = this.slice(a.data + b.data);
    } else if (b?.data) {
      data = this.slice(b.data);
    }
    return {
      __typename: b.__typename,
      path: b.path,
      downloadUrl: b.downloadUrl,
      data: data,
      cursor: b.cursor
    };
  }

  slice(s: string) {
    if (s.length < MAX_STREAMING_LOG_BYTES) {
      return s;
    }
    return s.slice(-MAX_STREAMING_LOG_BYTES);
  }

  render() {
    const { isLoading, stdout, stderr } = this.state;
    const { maxBytes } = this.props;
    return this.props.children({ isLoading, stdout, stderr, maxBytes });
  }
}

const COMPUTE_LOGS_SUBSCRIPTION = gql`
  subscription ComputeLogsSubscription(
    $runId: ID!
    $stepKey: String!
    $ioType: ComputeIOType!
    $cursor: String
  ) {
    computeLogs(
      runId: $runId
      stepKey: $stepKey
      ioType: $ioType
      cursor: $cursor
    ) {
      ...ComputeLogsSubscriptionFragment
    }
  }
  ${ComputeLogsProvider.fragments.subscription}
`;

const LoadingContainer = styled.div`
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
`;
