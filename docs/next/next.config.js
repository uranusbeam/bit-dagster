const ExtraWatchPlugin = require('extra-watch-webpack-plugin');
const path = require('path');
const visit = require('unist-util-visit');
const fs = require('fs');
const limitSnippetLines = require('./snippet-engine/functions/limitSnippetLines');
const TSConfigPathsPlugin = require('tsconfig-paths-webpack-plugin');

const setUpAbsoluteImports = (config) => {
  if (config.resolve.plugins) {
    config.resolve.plugins.push(new TSConfigPathsPlugin());
  } else {
    config.resolve.plugins = [new TSConfigPathsPlugin()];
  }
};

const DIRECTIVE_PATTERN = 'literalinclude';

const transform = () => (tree) => {
  const visitor = (node) => {
    const { value, meta } = node;
    const metaValues = meta ? meta.split(' ') : [];
    if (metaValues.includes(DIRECTIVE_PATTERN)) {
      const data = value.trim();
      const values = data.split('\n').map((i) => i.trim().split(':'));

      const map = {};
      for (const val of values) {
        map[val[0]] = val[1];
      }

      const REPO = process.env.DAGSTER_REPO || path.join(__dirname, '../../');

      if (!REPO) {
        node.value =
          'Unable to produce literal include: Environment variable $DAGSTER_REPO is not set';
        return;
      }

      const root = path.join(REPO, '/examples/');
      const filePath = path.join(root, map.file);
      try {
        // TODO: Fix all other literal includes because now they need to include /dagster_examples/ in their paths
        const content = fs.readFileSync(filePath).toString();
        node.value = limitSnippetLines(content, map.lines);
      } catch (error) {
        node.value = `Unable to read file at: ${filePath}`;
      }
    }
  };

  visit(tree, 'code', visitor);
};

const withMDX = require('@next/mdx')({
  extension: /\.mdx?$/,
  options: {
    remarkPlugins: [transform],
  },
});

module.exports = withMDX({
  pageExtensions: ['mdx', 'jsx', 'js', 'ts', 'tsx'],
  webpack: (config) => {
    config.plugins.push(
      new ExtraWatchPlugin({
        dirs: [path.join(config.context, 'pages')],
      }),
    );
    setUpAbsoluteImports(config);
    return config;
  },
});
