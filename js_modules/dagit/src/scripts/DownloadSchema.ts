import { writeFileSync } from "fs";
import { execSync } from "child_process";
import { getIntrospectionQuery, buildClientSchema, printSchema } from "graphql";

const pyVer = execSync("python --version").toString();
const verMatch = pyVer.match(/Python ([\d.]*)/);
if (
  !(verMatch != null && verMatch.length >= 2 && parseFloat(verMatch[1]) >= 3.6)
) {
  const errMsg =
    pyVer !== ""
      ? pyVer
      : "nothing on stdout indicating no python or a version earlier than 3.4";
  throw new Error(`Must use Python version >= 3.6 got ${errMsg}`);
}

const result = execSync(
  `dagster-graphql -y ../../examples/dagster_examples/intro_tutorial/repository.yaml -t '${getIntrospectionQuery(
    {
      descriptions: false
    }
  )}'`
).toString();

const schemaJson = JSON.parse(result).data;

// Write schema.graphql in the SDL format
const sdl = printSchema(buildClientSchema(schemaJson));
writeFileSync("./src/schema.graphql", sdl);

// Write filteredSchema.json, a reduced schema for runtime usage
// See https://www.apollographql.com/docs/react/advanced/fragments.html
const types = schemaJson.__schema.types.map(
  (type: { name: string; kind: string; possibleTypes: [{ name: string }] }) => {
    const { name, kind } = type;
    const possibleTypes = type.possibleTypes
      ? type.possibleTypes.map(t => ({
          name: t.name
        }))
      : null;
    return { name, kind, possibleTypes };
  }
);

writeFileSync(
  "./src/filteredSchema.generated.json",
  JSON.stringify({
    __schema: {
      types
    }
  })
);
