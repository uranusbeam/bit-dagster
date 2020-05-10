import * as React from "react";
import {
  Button,
  Menu,
  Spinner,
  MenuItem,
  Intent,
  IInputGroupProps,
  HTMLInputProps
} from "@blueprintjs/core";
import * as ReactDOM from "react-dom";

import { Select, Suggest } from "@blueprintjs/select";
import { useQuery } from "react-apollo";
import {
  ConfigPresetsQuery,
  ConfigPresetsQuery_pipeline_presets
} from "./types/ConfigPresetsQuery";
import {
  ConfigPartitionsQuery,
  ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results
} from "./types/ConfigPartitionsQuery";
import {
  ConfigPartitionSetsQuery,
  ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results
} from "./types/ConfigPartitionSetsQuery";
import gql from "graphql-tag";
import { IExecutionSession } from "../LocalStorage";
import { isEqual } from "apollo-utilities";
import styled from "styled-components";
import { ShortcutHandler } from "../ShortcutHandler";

type Preset = ConfigPresetsQuery_pipeline_presets;
type PartitionSet = ConfigPartitionSetsQuery_partitionSetsOrError_PartitionSets_results;
type Partition = ConfigPartitionsQuery_partitionSetOrError_PartitionSet_partitions_results;
type ConfigGenerator = Preset | PartitionSet;
interface Pipeline {
  tags: {
    key: string;
    value: string;
  }[];
}

interface ConfigEditorConfigPickerProps {
  base: IExecutionSession["base"];
  pipelineName: string;
  solidSubset: string[] | null;
  onSaveSession: (updates: Partial<IExecutionSession>) => void;
  onCreateSession: (initial: Partial<IExecutionSession>) => void;
}

const PRESET_PICKER_HINT_TEXT = `Define a PresetDefinition, PartitionSetDefinition, or a schedule decorator (e.g. @daily_schedule) to autofill this session...`;

export class ConfigEditorConfigPicker extends React.Component<
  ConfigEditorConfigPickerProps
> {
  onSelectPartitionSet = (partitionSet: PartitionSet) => {
    this.props.onSaveSession({
      base: {
        partitionsSetName: partitionSet.name,
        partitionName: null
      }
    });
  };

  onSelectPreset = (preset: Preset, pipeline?: Pipeline) => {
    this.onCommit({
      base: { presetName: preset.name },
      name: preset.name,
      environmentConfigYaml: preset.environmentConfigYaml || "",
      solidSubset: preset.solidSubset,
      mode: preset.mode,
      tags: [...(pipeline?.tags || [])]
    });
  };

  onSelectPartition = (partition: Partition, pipeline?: Pipeline) => {
    this.onCommit({
      name: partition.name,
      base: Object.assign({}, this.props.base, {
        partitionName: partition.name
      }),
      environmentConfigYaml: partition.environmentConfigYaml || "",
      solidSubset: partition.solidSubset,
      mode: partition.mode,
      tags: [...(pipeline?.tags || []), ...partition.tags]
    });
  };

  onCommit = (changes: Partial<IExecutionSession>) => {
    this.props.onSaveSession(changes);
  };

  render() {
    const { pipelineName, solidSubset, base } = this.props;

    return (
      <PickerContainer>
        <ConfigEditorConfigGeneratorPicker
          value={base}
          pipelineName={pipelineName}
          solidSubset={solidSubset}
          onSelectPreset={this.onSelectPreset}
          onSelectPartitionSet={this.onSelectPartitionSet}
        />
        {base && "partitionsSetName" in base && (
          <>
            <div style={{ width: 5 }} />
            <ConfigEditorPartitionPicker
              key={base.partitionsSetName}
              pipelineName={pipelineName}
              partitionSetName={base.partitionsSetName}
              value={base.partitionName}
              onSelect={this.onSelectPartition}
            />
          </>
        )}
      </PickerContainer>
    );
  }
}

interface ConfigEditorPartitionPickerProps {
  pipelineName: string;
  partitionSetName: string;
  value: string | null;
  onSelect: (partition: Partition, pipeline?: Pipeline) => void;
}

export const ConfigEditorPartitionPicker: React.FunctionComponent<ConfigEditorPartitionPickerProps> = React.memo(
  props => {
    const { partitionSetName, pipelineName, value, onSelect } = props;
    const { data, loading } = useQuery<ConfigPartitionsQuery>(
      CONFIG_PARTITIONS_QUERY,
      {
        variables: { partitionSetName, pipelineName },
        fetchPolicy: "network-only"
      }
    );

    const partitions: Partition[] =
      data?.partitionSetOrError.__typename === "PartitionSet"
        ? data.partitionSetOrError.partitions.results
        : [];

    const selected = partitions.find(p => p.name === value);

    const inputProps: IInputGroupProps & HTMLInputProps = {
      placeholder: "Partition",
      style: { width: 180 },
      intent: (loading ? !!value : !!selected) ? Intent.NONE : Intent.DANGER
    };

    // If we are loading the partitions and do NOT have any cached data to display,
    // show the component in a loading state with a spinner and fill it with the
    // current partition's name so it doesn't flicker (if one is set already.)
    if (loading && partitions.length === 0) {
      return (
        <Suggest<string>
          key="loading"
          inputProps={{
            ...inputProps,
            rightElement: !value ? <Spinner size={17} /> : undefined
          }}
          items={[]}
          itemRenderer={() => null}
          noResults={<Menu.Item disabled={true} text="Loading..." />}
          inputValueRenderer={str => str}
          selectedItem={value}
        />
      );
    }

    // Note: We don't want this Suggest to be a fully "controlled" React component.
    // Keeping it's state is annoyign and we only want to update our data model on
    // selection change. However, we need to set an initial value (defaultSelectedItem)
    // and ensure it is re-applied to the internal state when it changes (via `key` below).
    return (
      <Suggest<Partition>
        key={selected ? selected.name : "none"}
        defaultSelectedItem={selected}
        items={partitions}
        inputProps={inputProps}
        inputValueRenderer={partition => partition.name}
        itemPredicate={(query, partition) =>
          query.length === 0 || partition.name.includes(query)
        }
        itemRenderer={(partition, props) => (
          <Menu.Item
            active={props.modifiers.active}
            onClick={props.handleClick}
            key={partition.name}
            text={partition.name}
          />
        )}
        noResults={<Menu.Item disabled={true} text="No presets." />}
        onItemSelect={item => onSelect(item, data?.pipeline)}
      />
    );
  },
  isEqual
);

interface ConfigEditorConfigGeneratorPickerProps {
  pipelineName: string;
  solidSubset: string[] | null;
  value: IExecutionSession["base"];
  onSelectPreset: (preset: Preset, pipeline?: Pipeline) => void;
  onSelectPartitionSet: (
    partitionSet: PartitionSet,
    pipeline?: Pipeline
  ) => void;
}

export const ConfigEditorConfigGeneratorPicker: React.FunctionComponent<ConfigEditorConfigGeneratorPickerProps> = React.memo(
  props => {
    const { pipelineName, onSelectPreset, onSelectPartitionSet, value } = props;
    const {
      presets,
      partitionSets,
      loading,
      pipeline
    } = usePresetsAndPartitions(pipelineName);

    const configGenerators: ConfigGenerator[] = [...presets, ...partitionSets];
    const empty = !loading && configGenerators.length === 0;

    const select: React.RefObject<Select<ConfigGenerator>> = React.createRef();
    const onSelect = (item: ConfigGenerator) => {
      if (item.__typename === "PartitionSet") {
        onSelectPartitionSet(item, pipeline);
      } else {
        onSelectPreset(item, pipeline);
      }
    };

    let emptyLabel = `Preset / Partition Set`;
    if (presets.length && !partitionSets.length) {
      emptyLabel = `Preset`;
    } else if (!presets.length && partitionSets.length) {
      emptyLabel = `Partition Set`;
    }

    const label = !value
      ? emptyLabel
      : "presetName" in value
      ? `Preset: ${value.presetName}`
      : `Partition Set: ${value.partitionsSetName}`;

    return (
      <div>
        <ShortcutHandler
          shortcutLabel={"⌥E"}
          shortcutFilter={e => e.keyCode === 69 && e.altKey}
          onShortcut={() => activateSelect(select.current)}
        >
          <Select<ConfigGenerator>
            ref={select}
            disabled={empty}
            items={configGenerators}
            itemPredicate={(query, configGenerator) =>
              query.length === 0 || configGenerator.name.includes(query)
            }
            itemListRenderer={({
              itemsParentRef,
              renderItem,
              filteredItems
            }) => {
              const renderedPresetItems = filteredItems
                .filter(item => item.__typename === "PipelinePreset")
                .map(renderItem)
                .filter(Boolean);

              const renderedPartitionSetItems = filteredItems
                .filter(item => item.__typename === "PartitionSet")
                .map(renderItem)
                .filter(Boolean);

              const bothTypesPresent =
                renderedPresetItems.length > 0 &&
                renderedPartitionSetItems.length > 0;

              return (
                <Menu ulRef={itemsParentRef}>
                  {bothTypesPresent && (
                    <MenuItem disabled={true} text={`Presets`} />
                  )}
                  {renderedPresetItems}
                  {bothTypesPresent && <Menu.Divider />}
                  {bothTypesPresent && (
                    <MenuItem disabled={true} text={`Partition Sets`} />
                  )}
                  {renderedPartitionSetItems}
                </Menu>
              );
            }}
            itemRenderer={(item, props) => (
              <Menu.Item
                active={props.modifiers.active}
                onClick={props.handleClick}
                key={item.name}
                text={
                  <div>
                    {item.name}
                    <div style={{ opacity: 0.4, fontSize: "0.75rem" }}>
                      {[
                        item.solidSubset
                          ? item.solidSubset.length === 1
                            ? `Solids: ${item.solidSubset[0]}`
                            : `Solids: ${item.solidSubset.length}`
                          : `Solids: All`,
                        `Mode: ${item.mode}`
                      ].join(" - ")}
                    </div>
                  </div>
                }
              />
            )}
            noResults={<Menu.Item disabled={true} text="No presets." />}
            onItemSelect={onSelect}
          >
            <Button
              disabled={empty}
              text={label}
              title={empty ? PRESET_PICKER_HINT_TEXT : undefined}
              data-test-id="preset-selector-button"
              rightIcon="caret-down"
            />
          </Select>
        </ShortcutHandler>
      </div>
    );
  },
  isEqual
);

function activateSelect(select: Select<any> | null) {
  if (!select) return;
  // eslint-disable-next-line react/no-find-dom-node
  const selectEl = ReactDOM.findDOMNode(select) as HTMLElement;
  const btnEl = selectEl.querySelector("button");
  if (btnEl) {
    btnEl.click();
  }
}

const PickerContainer = styled.div`
  display: flex;
  justify: space-between;
  align-items: center;
`;

export const CONFIG_PRESETS_QUERY = gql`
  query ConfigPresetsQuery($pipelineName: String!) {
    pipeline(params: { name: $pipelineName }) {
      name
      presets {
        __typename
        name
        mode
        solidSubset
        environmentConfigYaml
      }
      tags {
        key
        value
      }
    }
  }
`;

export const CONFIG_PARTITION_SETS_QUERY = gql`
  query ConfigPartitionSetsQuery($pipelineName: String!) {
    partitionSetsOrError(pipelineName: $pipelineName) {
      __typename
      ... on PartitionSets {
        results {
          name
          mode
          solidSubset
        }
      }
    }
  }
`;

export const CONFIG_PARTITIONS_QUERY = gql`
  query ConfigPartitionsQuery(
    $partitionSetName: String!
    $pipelineName: String!
  ) {
    pipeline(params: { name: $pipelineName }) {
      name
      tags {
        key
        value
      }
    }
    partitionSetOrError(partitionSetName: $partitionSetName) {
      __typename
      ... on PartitionSet {
        partitions {
          results {
            name
            solidSubset
            environmentConfigYaml
            mode
            tags {
              key
              value
            }
          }
        }
      }
    }
  }
`;

function usePresetsAndPartitions(
  pipelineName: string
): {
  presets: Preset[];
  partitionSets: PartitionSet[];
  loading: boolean;
  pipeline?: Pipeline;
} {
  const presetsQuery = useQuery<ConfigPresetsQuery>(CONFIG_PRESETS_QUERY, {
    fetchPolicy: "network-only",
    variables: { pipelineName }
  });
  const partitionSetsQuery = useQuery<ConfigPartitionSetsQuery>(
    CONFIG_PARTITION_SETS_QUERY,
    {
      fetchPolicy: "network-only",
      variables: { pipelineName }
    }
  );

  const byName = (a: { name: string }, b: { name: string }) =>
    a.name.localeCompare(b.name);

  return {
    loading: presetsQuery.loading || partitionSetsQuery.loading,
    presets:
      presetsQuery.data?.pipeline?.__typename === "Pipeline"
        ? presetsQuery.data.pipeline.presets.sort(byName)
        : [],
    partitionSets:
      partitionSetsQuery.data?.partitionSetsOrError?.__typename ===
      "PartitionSets"
        ? partitionSetsQuery.data.partitionSetsOrError.results.sort(byName)
        : [],
    pipeline: presetsQuery.data?.pipeline
  };
}
