import * as React from "react";
import styled from "styled-components/macro";
import { Button } from "@blueprintjs/core";
import gql from "graphql-tag";
import { PythonErrorFragment } from "./types/PythonErrorFragment";
import { MetadataEntryFragment } from "./runs/types/MetadataEntryFragment";
import { MetadataEntries } from "./runs/MetadataEntry";

interface IPythonErrorInfoProps {
  showReload?: boolean;
  centered?: boolean;
  contextMsg?: string;
  error: { message: string } | PythonErrorFragment;
  failureMetadata?: { metadataEntries: MetadataEntryFragment[] } | null;
}

export default class PythonErrorInfo extends React.Component<
  IPythonErrorInfoProps
> {
  static fragments = {
    PythonErrorFragment: gql`
      fragment PythonErrorFragment on PythonError {
        __typename
        message
        stack
        cause {
          message
          stack
        }
      }
    `
  };

  render() {
    const message = this.props.error.message;
    const stack = (this.props.error as PythonErrorFragment).stack;
    const cause = (this.props.error as PythonErrorFragment).cause;

    const Wrapper = this.props.centered ? ErrorWrapperCentered : ErrorWrapper;
    const context = this.props.contextMsg ? (
      <ErrorHeader>{this.props.contextMsg}</ErrorHeader>
    ) : null;
    const metadataEntries = this.props.failureMetadata?.metadataEntries;

    return (
      <Wrapper>
        {context}
        <ErrorHeader>{message}</ErrorHeader>
        {metadataEntries ? (
          <div style={{ marginTop: 10, marginBottom: 10 }}>
            <MetadataEntries entries={metadataEntries} />
          </div>
        ) : null}
        <Trace>{stack ? stack.join("") : "No Stack Provided."}</Trace>
        {cause ? (
          <>
            <CauseHeader>
              The above exception was the direct cause of the following
              exception:
            </CauseHeader>
            <ErrorHeader>{cause.message}</ErrorHeader>
            <Trace>
              {cause.stack ? cause.stack.join("") : "No Stack Provided."}
            </Trace>
          </>
        ) : null}
        {this.props.showReload && (
          <Button icon="refresh" onClick={() => window.location.reload()}>
            Reload
          </Button>
        )}
      </Wrapper>
    );
  }
}

const CauseHeader = styled.h3`
  font-weight: 400;
  margin: 1em 0 1em;
`;

const ErrorHeader = styled.h3`
  color: #b05c47;
  font-weight: 400;
  margin: 0.5em 0 0.25em;
`;

const Trace = styled.div`
  color: rgb(41, 50, 56);
  font-family: Consolas, Menlo, monospace;
  font-size: 0.85em;
  white-space: pre;
  overflow-x: auto;
  padding-bottom: 1em;
`;

const ErrorWrapper = styled.div`
  background-color: rgba(206, 17, 38, 0.05);
  border: 1px solid #d17257;
  border-radius: 3px;
  max-width: 90vw;
  max-height: 80vh;
  padding: 1em 2em;
  overflow: auto;
`;

const ErrorWrapperCentered = styled(ErrorWrapper)`
  position: absolute;
  left: 50%;
  top: 100px;
  transform: translate(-50%, 0);
`;
