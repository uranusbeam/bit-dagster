// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: TypeListContainerQuery
// ====================================================

export interface TypeListContainerQuery_pipelineOrError_PipelineNotFoundError {
  __typename: "PipelineNotFoundError" | "InvalidSubsetError" | "PythonError";
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline_runtimeTypes {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  isBuiltin: boolean;
  displayName: string;
  description: string | null;
}

export interface TypeListContainerQuery_pipelineOrError_Pipeline {
  __typename: "Pipeline";
  name: string;
  runtimeTypes: TypeListContainerQuery_pipelineOrError_Pipeline_runtimeTypes[];
}

export type TypeListContainerQuery_pipelineOrError = TypeListContainerQuery_pipelineOrError_PipelineNotFoundError | TypeListContainerQuery_pipelineOrError_Pipeline;

export interface TypeListContainerQuery {
  pipelineOrError: TypeListContainerQuery_pipelineOrError;
}

export interface TypeListContainerQueryVariables {
  pipelineName: string;
}
