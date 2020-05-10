import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { Colors } from "@blueprintjs/core";
import {
  ConfigEditorHelpContext,
  isHelpContextEqual
} from "../configeditor/ConfigEditor";
import { ConfigTypeSchema, TypeData } from "../ConfigTypeSchema";

interface ConfigEditorHelpProps {
  context: ConfigEditorHelpContext | null;
  allInnerTypes: TypeData[];
}

export const ConfigEditorHelp: React.FunctionComponent<ConfigEditorHelpProps> = React.memo(
  ({ context, allInnerTypes }) => {
    if (!context) {
      return <span />;
    }
    return (
      <Container>
        <ConfigScrollWrap>
          <ConfigTypeSchema
            type={context.type}
            typesInScope={allInnerTypes}
            maxDepth={2}
          />
        </ConfigScrollWrap>
        <AutocompletionsNote>
          Ctrl+Space to show auto-completions inline.
        </AutocompletionsNote>
      </Container>
    );
  },
  (prev, next) => isHelpContextEqual(prev.context, next.context)
);

export const ConfigEditorHelpConfigTypeFragment = gql`
  fragment ConfigEditorHelpConfigTypeFragment on ConfigType {
    ...ConfigTypeSchemaFragment
  }
  ${ConfigTypeSchema.fragments.ConfigTypeSchemaFragment}
`;

const AutocompletionsNote = styled.div`
  font-size: 0.75rem;
  text-align: center;
  padding: 4px;
  border-top: 1px solid ${Colors.LIGHT_GRAY1};
  background: rgba(238, 238, 238, 0.9);
  color: rgba(0, 0, 0, 0.7);
`;

const ConfigScrollWrap = styled.div`
  padding: 8px;
  color: black;
  pointer-events: initial;
  background-color: #e1e8edd1;
  max-height: 100%;
  overflow-y: auto;
`;

const Container = styled.div`
  width: 300px;
  top: 14px;
  right: 14px;
  bottom: 68px;
  position: absolute;
  align-items: center;
  pointer-events: none;
  z-index: 3;
`;
