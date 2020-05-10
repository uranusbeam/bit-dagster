import * as React from "react";
import * as TestRenderer from "react-test-renderer";
import { BrowserRouter } from "react-router-dom";

import { ConfigEditorModePicker } from "../execute/ConfigEditorModePicker";
import { ModeNotFoundError } from "../execute/ExecutionSessionContainer";
import { ExecutionSessionContainerFragment_Pipeline_modes } from "../execute/types/ExecutionSessionContainerFragment";

const defaultMode: ExecutionSessionContainerFragment_Pipeline_modes = {
  __typename: "Mode",
  description: null,
  name: "default"
};

const mode1: ExecutionSessionContainerFragment_Pipeline_modes = {
  __typename: "Mode",
  description: "Mode 1",
  name: "mode_1"
};

const mode2: ExecutionSessionContainerFragment_Pipeline_modes = {
  __typename: "Mode",
  description: "Mode 2",
  name: "mode_2"
};

it("renders single mode pipelines", () => {
  const componentNullSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        modes={[defaultMode]}
        modeName={null}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentNullSelected.toJSON()).toMatchSnapshot();

  const componentDefaultSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        modes={[defaultMode]}
        modeName={"default"}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentDefaultSelected.toJSON()).toMatchSnapshot();
});

it("renders multi mode pipelines", () => {
  const componentNullSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        modes={[mode1, mode2]}
        modeName={null}
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentNullSelected.toJSON()).toMatchSnapshot();

  const componentMode1Selected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        modes={[mode1, mode2]}
        modeName="mode_1"
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentMode1Selected.toJSON()).toMatchSnapshot();
});

it("renders error mode", () => {
  const error: ModeNotFoundError = {
    __typename: "ModeNotFoundError",
    message: "Mode Not Found"
  };
  const componentNullSelected = TestRenderer.create(
    <BrowserRouter>
      <ConfigEditorModePicker
        modes={[mode1, mode2]}
        modeError={error}
        modeName="mode_1"
        onModeChange={() => null}
      />
    </BrowserRouter>
  );
  expect(componentNullSelected.toJSON()).toMatchSnapshot();
});
