// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ConfigPresetsQuery
// ====================================================

export interface ConfigPresetsQuery_pipeline_presets {
  __typename: "PipelinePreset";
  name: string;
  mode: string;
  solidSubset: string[] | null;
  environmentConfigYaml: string;
}

export interface ConfigPresetsQuery_pipeline_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface ConfigPresetsQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  presets: ConfigPresetsQuery_pipeline_presets[];
  tags: ConfigPresetsQuery_pipeline_tags[];
}

export interface ConfigPresetsQuery {
  pipeline: ConfigPresetsQuery_pipeline;
}

export interface ConfigPresetsQueryVariables {
  pipelineName: string;
}
