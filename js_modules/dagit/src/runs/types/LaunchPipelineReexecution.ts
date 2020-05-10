// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { ExecutionParams } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: LaunchPipelineReexecution
// ====================================================

export interface LaunchPipelineReexecution_launchPipelineReexecution_RunLauncherNotDefinedError {
  __typename: "RunLauncherNotDefinedError" | "InvalidStepError" | "InvalidOutputError" | "PipelineRunConflict";
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_LaunchPipelineRunSuccess_run_pipeline {
  __typename: "Pipeline" | "UnknownPipeline";
  name: string;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_LaunchPipelineRunSuccess_run {
  __typename: "PipelineRun";
  runId: string;
  pipeline: LaunchPipelineReexecution_launchPipelineReexecution_LaunchPipelineRunSuccess_run_pipeline;
  rootRunId: string | null;
  parentRunId: string | null;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_LaunchPipelineRunSuccess {
  __typename: "LaunchPipelineRunSuccess";
  run: LaunchPipelineReexecution_launchPipelineReexecution_LaunchPipelineRunSuccess_run;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PipelineNotFoundError {
  __typename: "PipelineNotFoundError";
  message: string;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PipelineConfigValidationInvalid_errors {
  __typename: "FieldNotDefinedConfigError" | "FieldsNotDefinedConfigError" | "MissingFieldConfigError" | "MissingFieldsConfigError" | "RuntimeMismatchConfigError" | "SelectorTypeConfigError";
  message: string;
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PipelineConfigValidationInvalid {
  __typename: "PipelineConfigValidationInvalid";
  errors: LaunchPipelineReexecution_launchPipelineReexecution_PipelineConfigValidationInvalid_errors[];
}

export interface LaunchPipelineReexecution_launchPipelineReexecution_PythonError {
  __typename: "PythonError";
  message: string;
  stack: string[];
}

export type LaunchPipelineReexecution_launchPipelineReexecution = LaunchPipelineReexecution_launchPipelineReexecution_RunLauncherNotDefinedError | LaunchPipelineReexecution_launchPipelineReexecution_LaunchPipelineRunSuccess | LaunchPipelineReexecution_launchPipelineReexecution_PipelineNotFoundError | LaunchPipelineReexecution_launchPipelineReexecution_PipelineConfigValidationInvalid | LaunchPipelineReexecution_launchPipelineReexecution_PythonError;

export interface LaunchPipelineReexecution {
  launchPipelineReexecution: LaunchPipelineReexecution_launchPipelineReexecution;
}

export interface LaunchPipelineReexecutionVariables {
  executionParams: ExecutionParams;
}
