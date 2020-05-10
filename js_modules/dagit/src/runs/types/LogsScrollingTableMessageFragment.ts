// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LogLevel, ObjectStoreOperationType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: LogsScrollingTableMessageFragment
// ====================================================

export interface LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent {
  __typename: "ExecutionStepSkippedEvent" | "ExecutionStepStartEvent" | "ExecutionStepSuccessEvent" | "ExecutionStepUpForRetryEvent" | "ExecutionStepRestartEvent" | "LogMessageEvent" | "PipelineFailureEvent" | "PipelineStartEvent" | "PipelineSuccessEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent_step | null;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries = LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization {
  __typename: "Materialization";
  label: string;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_StepMaterializationEvent {
  __typename: "StepMaterializationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_StepMaterializationEvent_step | null;
  materialization: LogsScrollingTableMessageFragment_StepMaterializationEvent_materialization;
}

export interface LogsScrollingTableMessageFragment_PipelineInitFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_PipelineInitFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_PipelineInitFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_PipelineInitFailureEvent_error_cause | null;
}

export interface LogsScrollingTableMessageFragment_PipelineInitFailureEvent {
  __typename: "PipelineInitFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_PipelineInitFailureEvent_step | null;
  error: LogsScrollingTableMessageFragment_PipelineInitFailureEvent_error;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error_cause | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata {
  __typename: "FailureMetadata";
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepFailureEvent {
  __typename: "ExecutionStepFailureEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_step | null;
  error: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_error;
  failureMetadata: LogsScrollingTableMessageFragment_ExecutionStepFailureEvent_failureMetadata | null;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepInputEvent {
  __typename: "ExecutionStepInputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_step | null;
  inputName: string;
  typeCheck: LogsScrollingTableMessageFragment_ExecutionStepInputEvent_typeCheck;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries = LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck {
  __typename: "TypeCheck";
  label: string;
  description: string | null;
  success: boolean;
  metadataEntries: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ExecutionStepOutputEvent {
  __typename: "ExecutionStepOutputEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_step | null;
  outputName: string;
  typeCheck: LogsScrollingTableMessageFragment_ExecutionStepOutputEvent_typeCheck;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries = LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult {
  __typename: "ExpectationResult";
  success: boolean;
  label: string;
  description: string | null;
  metadataEntries: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_StepExpectationResultEvent {
  __typename: "StepExpectationResultEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_StepExpectationResultEvent_step | null;
  expectationResult: LogsScrollingTableMessageFragment_StepExpectationResultEvent_expectationResult;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries = LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult {
  __typename: "ObjectStoreOperationResult";
  op: ObjectStoreOperationType;
  metadataEntries: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult_metadataEntries[];
}

export interface LogsScrollingTableMessageFragment_ObjectStoreOperationEvent {
  __typename: "ObjectStoreOperationEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_step | null;
  operationResult: LogsScrollingTableMessageFragment_ObjectStoreOperationEvent_operationResult;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_step {
  __typename: "ExecutionStep";
  key: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPathMetadataEntry {
  __typename: "EventPathMetadataEntry";
  label: string;
  description: string | null;
  path: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry {
  __typename: "EventJsonMetadataEntry";
  label: string;
  description: string | null;
  jsonString: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry {
  __typename: "EventUrlMetadataEntry";
  label: string;
  description: string | null;
  url: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventTextMetadataEntry {
  __typename: "EventTextMetadataEntry";
  label: string;
  description: string | null;
  text: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry {
  __typename: "EventMarkdownMetadataEntry";
  label: string;
  description: string | null;
  mdStr: string;
}

export interface LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry {
  __typename: "EventPythonArtifactMetadataEntry";
  label: string;
  description: string | null;
  module: string;
  name: string;
}

export type LogsScrollingTableMessageFragment_EngineEvent_metadataEntries = LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPathMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventJsonMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventUrlMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventTextMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventMarkdownMetadataEntry | LogsScrollingTableMessageFragment_EngineEvent_metadataEntries_EventPythonArtifactMetadataEntry;

export interface LogsScrollingTableMessageFragment_EngineEvent_engineError_cause {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export interface LogsScrollingTableMessageFragment_EngineEvent_engineError {
  __typename: "PythonError";
  message: string;
  stack: string[];
  cause: LogsScrollingTableMessageFragment_EngineEvent_engineError_cause | null;
}

export interface LogsScrollingTableMessageFragment_EngineEvent {
  __typename: "EngineEvent";
  message: string;
  timestamp: string;
  level: LogLevel;
  step: LogsScrollingTableMessageFragment_EngineEvent_step | null;
  metadataEntries: LogsScrollingTableMessageFragment_EngineEvent_metadataEntries[];
  engineError: LogsScrollingTableMessageFragment_EngineEvent_engineError | null;
}

export type LogsScrollingTableMessageFragment = LogsScrollingTableMessageFragment_ExecutionStepSkippedEvent | LogsScrollingTableMessageFragment_StepMaterializationEvent | LogsScrollingTableMessageFragment_PipelineInitFailureEvent | LogsScrollingTableMessageFragment_ExecutionStepFailureEvent | LogsScrollingTableMessageFragment_ExecutionStepInputEvent | LogsScrollingTableMessageFragment_ExecutionStepOutputEvent | LogsScrollingTableMessageFragment_StepExpectationResultEvent | LogsScrollingTableMessageFragment_ObjectStoreOperationEvent | LogsScrollingTableMessageFragment_EngineEvent;
