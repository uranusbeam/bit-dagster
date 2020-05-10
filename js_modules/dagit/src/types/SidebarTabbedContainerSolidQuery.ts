// @generated
/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SidebarTabbedContainerSolidQuery
// ====================================================

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_definition {
  __typename: "InputDefinition";
  name: string;
  description: string | null;
  type: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_definition_type;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_dependsOn_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_dependsOn_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_dependsOn {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_dependsOn_definition;
  solid: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_dependsOn_solid;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs {
  __typename: "Input";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_definition;
  dependsOn: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs_dependsOn[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_definition_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_definition {
  __typename: "OutputDefinition";
  name: string;
  description: string | null;
  type: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_definition_type;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_dependedBy_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_dependedBy_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_dependedBy {
  __typename: "Input";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_dependedBy_definition;
  solid: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_dependedBy_solid;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_definition;
  dependedBy: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs_dependedBy[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  recursiveConfigTypes: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
  recursiveConfigTypes: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_fields[];
  recursiveConfigTypes: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType_recursiveConfigTypes[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType {
  __typename: "ArrayConfigType" | "NullableConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType {
  __typename: "EnumConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType {
  __typename: "RegularConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  givenName: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields {
  __typename: "ConfigTypeField";
  name: string;
  description: string | null;
  isOptional: boolean;
  configTypeKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType {
  __typename: "CompositeConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  fields: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType_fields[];
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ArrayConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_EnumConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_RegularConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_CompositeConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes_ScalarUnionConfigType;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType {
  __typename: "ScalarUnionConfigType";
  key: string;
  description: string | null;
  isSelector: boolean;
  typeParamKeys: string[];
  scalarTypeKey: string;
  nonScalarTypeKey: string;
  recursiveConfigTypes: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType_recursiveConfigTypes[];
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ArrayConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_EnumConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_RegularConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_CompositeConfigType | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType_ScalarUnionConfigType;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField {
  __typename: "ConfigTypeField";
  configType: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField_configType;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition {
  __typename: "SolidDefinition";
  outputDefinitions: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_metadata[];
  requiredResources: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_requiredResources[];
  configField: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition_configField | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions {
  __typename: "OutputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions_type;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type {
  __typename: "RegularRuntimeType" | "ListRuntimeType" | "NullableRuntimeType";
  name: string | null;
  displayName: string;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions {
  __typename: "InputDefinition";
  name: string;
  type: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions_type;
  description: string | null;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_metadata {
  __typename: "MetadataItemDefinition";
  key: string;
  value: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_requiredResources {
  __typename: "ResourceRequirement";
  resourceKey: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition {
  __typename: "InputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput {
  __typename: "Input";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_definition;
  solid: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput_solid;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings {
  __typename: "InputMapping";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_definition;
  mappedInput: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings_mappedInput;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition {
  __typename: "OutputDefinition";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid {
  __typename: "Solid";
  name: string;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput {
  __typename: "Output";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_definition;
  solid: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput_solid;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings {
  __typename: "OutputMapping";
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_definition;
  mappedOutput: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings_mappedOutput;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition {
  __typename: "CompositeSolidDefinition";
  outputDefinitions: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputDefinitions[];
  inputDefinitions: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputDefinitions[];
  name: string;
  description: string | null;
  metadata: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_metadata[];
  requiredResources: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_requiredResources[];
  inputMappings: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_inputMappings[];
  outputMappings: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition_outputMappings[];
}

export type SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition = SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_SolidDefinition | SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition_CompositeSolidDefinition;

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid {
  __typename: "Solid";
  name: string;
  inputs: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_inputs[];
  outputs: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_outputs[];
  definition: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid_definition;
}

export interface SidebarTabbedContainerSolidQuery_pipeline_solidHandle {
  __typename: "SolidHandle";
  solid: SidebarTabbedContainerSolidQuery_pipeline_solidHandle_solid;
}

export interface SidebarTabbedContainerSolidQuery_pipeline {
  __typename: "Pipeline";
  name: string;
  solidHandle: SidebarTabbedContainerSolidQuery_pipeline_solidHandle | null;
}

export interface SidebarTabbedContainerSolidQuery {
  pipeline: SidebarTabbedContainerSolidQuery_pipeline;
}

export interface SidebarTabbedContainerSolidQueryVariables {
  pipeline: string;
  handleID: string;
}
