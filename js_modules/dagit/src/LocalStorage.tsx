import * as React from "react";

// Internal LocalStorage data format and mutation helpers

export interface IStorageData {
  sessions: { [name: string]: IExecutionSession };
  selectedExecutionType?: ExecutionType;
  current: string;
}

export enum ExecutionType {
  START = "start",
  LAUNCH = "launch"
}

export interface IExecutionSessionPlan {
  steps: Array<{
    name: string;
    kind: string;
    solid: {
      name: string;
    };
  }>;
}

export interface PipelineRunTag {
  key: string;
  value: string;
}

export interface IExecutionSession {
  key: string;
  name: string;
  environmentConfigYaml: string;
  base:
    | { presetName: string }
    | { partitionsSetName: string; partitionName: string | null }
    | null;
  mode: string | null;
  solidSubset: string[] | null;
  solidSubsetQuery: string | null;
  tags: PipelineRunTag[] | null;

  // this is set when you execute the session and freeze it
  runId?: string;
  configChangedSinceRun: boolean;
}

export type IExecutionSessionChanges = Partial<IExecutionSession>;

export function applySelectSession(data: IStorageData, key: string) {
  return { ...data, current: key };
}

export function applyRemoveSession(data: IStorageData, key: string) {
  const next = { current: data.current, sessions: { ...data.sessions } };
  const idx = Object.keys(next.sessions).indexOf(key);
  delete next.sessions[key];
  if (next.current === key) {
    const remaining = Object.keys(next.sessions);
    next.current = remaining[idx] || remaining[idx - 1] || remaining[0];
  }
  return next;
}

export function applyChangesToSession(
  data: IStorageData,
  key: string,
  changes: IExecutionSessionChanges
) {
  const saved = data.sessions[key];
  if (
    changes.environmentConfigYaml &&
    changes.environmentConfigYaml !== saved.environmentConfigYaml &&
    saved.runId
  ) {
    changes.configChangedSinceRun = true;
  }

  return {
    current: data.current,
    sessions: { ...data.sessions, [key]: { ...saved, ...changes } },
    selectedExecutionType: data.selectedExecutionType
  };
}

export function applyCreateSession(
  data: IStorageData,
  initial: IExecutionSessionChanges = {}
): IStorageData {
  const key = `s${Date.now()}`;

  return {
    current: key,
    sessions: {
      ...data.sessions,
      [key]: {
        name: "Workspace",
        environmentConfigYaml: "",
        mode: null,
        base: null,
        solidSubset: null,
        solidSubsetQuery: "*",
        tags: null,
        runId: undefined,
        ...initial,
        configChangedSinceRun: false,
        key
      }
    },
    selectedExecutionType: data.selectedExecutionType
  };
}

// StorageProvider component that vends `IStorageData` via a render prop

export type StorageHook = [
  IStorageData,
  React.Dispatch<React.SetStateAction<IStorageData>>
];

let _data: IStorageData | null = null;
let _dataNamespace = "";

function getKey(namespace: string) {
  return `dagit.v2.${namespace}`;
}

function getStorageDataForNamespace(namespace: string) {
  if (_data && _dataNamespace === namespace) {
    return _data;
  }

  let data: IStorageData = {
    sessions: {},
    current: ""
  };
  try {
    const jsonString = window.localStorage.getItem(getKey(namespace));
    if (jsonString) {
      data = Object.assign(data, JSON.parse(jsonString));
    }
  } catch (err) {
    // noop
  }
  if (Object.keys(data.sessions).length === 0) {
    data = applyCreateSession(data, {});
  }
  if (!data.sessions[data.current]) {
    data.current = Object.keys(data.sessions)[0];
  }

  _data = data;
  _dataNamespace = namespace;

  return data;
}

function writeStorageDataForNamespace(namespace: string, data: IStorageData) {
  _data = data;
  _dataNamespace = namespace;
  window.localStorage.setItem(getKey(namespace), JSON.stringify(data));
}

/* React hook that provides local storage to the caller. A previous version of this
loaded data into React state, but changing namespaces caused the data to be out-of-sync
for one render (until a useEffect could update the data in state). Now we keep the
current localStorage namespace in memory (in _data above) and React keeps a simple
version flag it can use to trigger a re-render after changes are saved, so changing
namespaces changes the returned data immediately.
*/
export function useStorage(namespace = "shared"): StorageHook {
  const [version, setVersion] = React.useState<number>(0);

  const onSave = (newData: IStorageData) => {
    writeStorageDataForNamespace(namespace, newData);
    setVersion(version + 1); // trigger a React render
  };

  return [getStorageDataForNamespace(namespace), onSave];
}
