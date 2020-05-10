import * as React from "react";
import gql from "graphql-tag";
import styled from "styled-components/macro";
import { H3, UL } from "@blueprintjs/core";
import TypeWithTooltip from "../TypeWithTooltip";
import { TypeListFragment } from "./types/TypeListFragment";
import {
  SidebarSubhead,
  SidebarSection,
  SidebarTitle,
  SectionInner
} from "../SidebarComponents";

interface ITypeListProps {
  types: Array<TypeListFragment>;
}

function groupTypes(types: Array<TypeListFragment>) {
  const groups = {
    Custom: Array<TypeListFragment>(),
    "Built-in": Array<TypeListFragment>()
  };
  types.forEach(type => {
    if (type.isBuiltin) {
      groups["Built-in"].push(type);
    } else {
      groups["Custom"].push(type);
    }
  });
  return groups;
}

export default class TypeList extends React.Component<ITypeListProps, {}> {
  static fragments = {
    TypeListFragment: gql`
      fragment TypeListFragment on RuntimeType {
        name
        isBuiltin
        ...RuntimeTypeWithTooltipFragment
      }

      ${TypeWithTooltip.fragments.RuntimeTypeWithTooltipFragment}
    `
  };

  renderTypes(types: TypeListFragment[]) {
    return types.map((type, i) => (
      <TypeLI key={i}>
        <TypeWithTooltip type={type} />
      </TypeLI>
    ));
  }

  render() {
    const groups = groupTypes(this.props.types);

    return (
      <>
        <SidebarSubhead />
        <SectionInner>
          <SidebarTitle>Pipeline Types</SidebarTitle>
        </SectionInner>
        {Object.keys(groups).map((title, idx) => (
          <SidebarSection
            key={idx}
            title={title}
            collapsedByDefault={idx !== 0}
          >
            <UL>{this.renderTypes(groups[title])}</UL>
          </SidebarSection>
        ))}
        <H3 />
      </>
    );
  }
}

const TypeLI = styled.li`
  text-overflow: ellipsis;
  overflow: hidden;
`;
