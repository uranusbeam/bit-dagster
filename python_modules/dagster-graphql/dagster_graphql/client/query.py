STEP_EVENT_FRAGMENTS = '''
fragment eventMetadataEntryFragment on EventMetadataEntry {
  __typename
  label
  description
  ... on EventPathMetadataEntry {
    path
  }
  ... on EventJsonMetadataEntry {
    jsonString
  }
  ... on EventUrlMetadataEntry {
    url
  }
  ... on EventTextMetadataEntry {
    text
  }
  ... on EventMarkdownMetadataEntry {
    mdStr
  }
  ... on EventPythonArtifactMetadataEntry {
    module
    name
  }
}

fragment errorFragment on PythonError {
  message
  stack
  className
  cause {
    message
    stack
    className
    cause {
      message
      stack
      className
    }
  }
}


fragment stepEventFragment on StepEvent {
  step {
    key
    inputs {
      name
      type {
        key
      }
      dependsOn {
        key
      }
    }
    outputs {
      name
      type {
        key
      }
    }
    solidHandleID
    kind
    metadata {
      key
      value
    }
  }
  ... on MessageEvent {
    runId
    message
    timestamp
    level
  }
  ... on StepExpectationResultEvent {
    expectationResult {
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on StepMaterializationEvent {
    materialization {
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepInputEvent {
    inputName
    typeCheck {
      __typename
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepOutputEvent {
    outputName
    typeCheck {
      __typename
      success
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepFailureEvent {
    error {
      ...errorFragment
    }
    failureMetadata {
      label
      description
      metadataEntries {
        ...eventMetadataEntryFragment
      }
    }
  }
  ... on ExecutionStepUpForRetryEvent {
    retryError: error {
      ...errorFragment
    }
    secondsToWait
  }
  ... on EngineEvent {
    metadataEntries {
      ...eventMetadataEntryFragment
    }
    markerStart
    markerEnd
    engineError: error {
      ...errorFragment
    }
  }
}
'''

MESSAGE_EVENT_FRAGMENTS = (
    '''
fragment messageEventFragment on MessageEvent {
  runId
  message
  timestamp
  level
  ...stepEventFragment
  ... on PipelineInitFailureEvent {
    initError: error {
      ...errorFragment
    }
  }
}
'''
    + STEP_EVENT_FRAGMENTS
)


START_PIPELINE_EXECUTION_RESULT_FRAGMENT = (
    '''
fragment startPipelineExecutionResultFragment on StartPipelineExecutionResult {
	__typename
	... on InvalidStepError {
		invalidStepKey
	}
	... on InvalidOutputError {
		stepKey
		invalidOutputName
	}
	... on PipelineConfigValidationInvalid {
		pipeline {
			name
		}
		errors {
			__typename
			message
			path
			reason
		}
	}
	... on PipelineNotFoundError {
		message
		pipelineName
	}
  ... on PythonError {
    message
    stack
  }
	... on StartPipelineRunSuccess {
		run {
			runId
			status
			pipeline {
				name
			}
			logs {
				nodes {
					__typename
	        ...messageEventFragment
				}
				pageInfo {
					lastCursor
					hasNextPage
					hasPreviousPage
					count
					totalCount
				}
			}
			environmentConfigYaml
			mode
		}
	}
  ... on PipelineRunConflict {
    message
  }
}
'''
    + MESSAGE_EVENT_FRAGMENTS
)

START_PIPELINE_EXECUTION_FOR_CREATED_RUN_RESULT_FRAGMENT = (
    '''
fragment startPipelineExecutionForCreatedRunResultFragment on StartPipelineExecutionForCreatedRunResult {
	__typename
	... on InvalidStepError {
		invalidStepKey
	}
	... on InvalidOutputError {
		stepKey
		invalidOutputName
	}
	... on PipelineConfigValidationInvalid {
		pipeline {
			name
		}
		errors {
			__typename
			message
			path
			reason
		}
	}
	... on PipelineNotFoundError {
		message
		pipelineName
	}
  ... on PythonError {
    message
    stack
  }
	... on StartPipelineRunSuccess {
		run {
			runId
			status
			pipeline {
				name
			}
			logs {
				nodes {
					__typename
	        ...messageEventFragment
				}
				pageInfo {
					lastCursor
					hasNextPage
					hasPreviousPage
					count
					totalCount
				}
			}
			environmentConfigYaml
			mode
		}
	}
}
'''
    + MESSAGE_EVENT_FRAGMENTS
)

START_PIPELINE_EXECUTION_MUTATION = (
    '''
mutation(
  $executionParams: ExecutionParams!
) {
  startPipelineExecution(
    executionParams: $executionParams,
  ) {
    ...startPipelineExecutionResultFragment
  }
}
'''
    + START_PIPELINE_EXECUTION_RESULT_FRAGMENT
)

START_PIPELINE_EXECUTION_FOR_CREATED_RUN_MUTATION = (
    '''
mutation(
  $runId: String!
) {
  startPipelineExecutionForCreatedRun(
    runId: $runId,
  ) {
    ...startPipelineExecutionForCreatedRunResultFragment
  }
}
'''
    + START_PIPELINE_EXECUTION_FOR_CREATED_RUN_RESULT_FRAGMENT
)

START_SCHEDULED_EXECUTION_MUTATION = '''
mutation(
  $scheduleName: String!
) {
  startScheduledExecution(
    scheduleName: $scheduleName,
  ) {
    __typename
    ...on ScheduleNotFoundError {
      message
      scheduleName
    }
    ...on SchedulerNotDefinedError {
      message
    }
    ...on ScheduledExecutionBlocked {
      message
    }
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on PipelineConfigValidationInvalid {
      pipeline {
        name
      }
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
      stack
      cause {
        message
        stack
      }
    }
    ... on StartPipelineRunSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
      }
    }
    ... on RunLauncherNotDefinedError {
      message
    }
    ... on LaunchPipelineRunSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
      }
    }

  }
}
'''

EXECUTE_PLAN_MUTATION = (
    '''
mutation(
  $executionParams: ExecutionParams!
) {
  executePlan(
    executionParams: $executionParams,
  ) {
    __typename
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on PipelineConfigValidationInvalid {
      pipeline {
        name
      }
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
      stack
    }
    ... on ExecutePlanSuccess {
      pipeline {
        name
      }
      hasFailures
      stepEvents {
        __typename
        ...stepEventFragment
      }
    }
  }
}
'''
    + STEP_EVENT_FRAGMENTS
)

RAW_EXECUTE_PLAN_MUTATION = '''
mutation(
  $executionParams: ExecutionParams!
) {
  executePlan(
    executionParams: $executionParams,
  ) {
    __typename
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on PipelineConfigValidationInvalid {
      pipeline {
        name
      }
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
      stack
      cause {
          message
          stack
      }
    }
    ... on ExecutePlanSuccess {
      pipeline {
        name
      }
      hasFailures
      rawEventRecords
    }
  }
}
'''

SUBSCRIPTION_QUERY = (
    MESSAGE_EVENT_FRAGMENTS
    + '''
subscription subscribeTest($runId: ID!) {
    pipelineRunLogs(runId: $runId) {
        __typename
        ... on PipelineRunLogsSubscriptionSuccess {
            run {
              runId
            },
            messages {
                __typename
                ...messageEventFragment
            }
        }
        ... on PipelineRunLogsSubscriptionFailure {
            missingRunId
        }
    }
}
'''
)

LAUNCH_PIPELINE_EXECUTION_MUTATION = '''
mutation(
  $executionParams: ExecutionParams!
) {
  launchPipelineExecution(
    executionParams: $executionParams,
  ) {
    __typename
    ... on RunLauncherNotDefinedError {
      message
    }
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on PipelineConfigValidationInvalid {
      pipeline {
        name
      }
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
      stack
    }
    ... on LaunchPipelineRunSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
        environmentConfigYaml
        mode
      }
    }
  }
}
'''

LAUNCH_PIPELINE_REEXECUTION_MUTATION = '''
mutation(
  $executionParams: ExecutionParams!
) {
  launchPipelineReexecution(
    executionParams: $executionParams,
  ) {
    __typename
    ... on RunLauncherNotDefinedError {
      message
    }
    ... on InvalidStepError {
      invalidStepKey
    }
    ... on InvalidOutputError {
      stepKey
      invalidOutputName
    }
    ... on PipelineConfigValidationInvalid {
      pipeline {
        name
      }
      errors {
        __typename
        message
        path
        reason
      }
    }
    ... on PipelineNotFoundError {
      message
      pipelineName
    }
    ... on PythonError {
      message
      stack
    }
    ... on LaunchPipelineRunSuccess {
      run {
        runId
        status
        pipeline {
          name
        }
        environmentConfigYaml
        mode
      }
    }
  }
}
'''
