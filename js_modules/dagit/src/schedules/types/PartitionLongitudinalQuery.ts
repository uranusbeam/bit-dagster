// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PipelineRunStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PartitionLongitudinalQuery
// ====================================================

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSetNotFoundError {
  __typename: "PartitionSetNotFoundError" | "PythonError";
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_tags {
  __typename: "PipelineTag";
  key: string;
  value: string;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stats_PythonError {
  __typename: "PythonError";
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stats_PipelineRunStatsSnapshot {
  __typename: "PipelineRunStatsSnapshot";
  startTime: number | null;
  endTime: number | null;
  materializations: number;
}

export type PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stats = PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stats_PythonError | PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stats_PipelineRunStatsSnapshot;

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stepStats_materializations {
  __typename: "Materialization";
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stepStats_expectationResults {
  __typename: "ExpectationResult";
  success: boolean;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stepStats {
  __typename: "PipelineRunStepStats";
  stepKey: string;
  startTime: number | null;
  endTime: number | null;
  materializations: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stepStats_materializations[];
  expectationResults: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stepStats_expectationResults[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs {
  __typename: "PipelineRun";
  runId: string;
  tags: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_tags[];
  stats: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stats;
  stepStats: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs_stepStats[];
  status: PipelineRunStatus;
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results {
  __typename: "Partition";
  name: string;
  runs: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results_runs[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions {
  __typename: "Partitions";
  results: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions_results[];
}

export interface PartitionLongitudinalQuery_partitionSetOrError_PartitionSet {
  __typename: "PartitionSet";
  name: string;
  partitions: PartitionLongitudinalQuery_partitionSetOrError_PartitionSet_partitions;
}

export type PartitionLongitudinalQuery_partitionSetOrError = PartitionLongitudinalQuery_partitionSetOrError_PartitionSetNotFoundError | PartitionLongitudinalQuery_partitionSetOrError_PartitionSet;

export interface PartitionLongitudinalQuery {
  partitionSetOrError: PartitionLongitudinalQuery_partitionSetOrError;
}

export interface PartitionLongitudinalQueryVariables {
  partitionSetName: string;
  partitionsLimit?: number | null;
  partitionsCursor?: string | null;
}
