# Implement `ezolenko/rollup-plugin-typescript2`

You are given a TypeScript repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that throws `new Error("STUB")` on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, classes, interfaces, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `ezolenko/rollup-plugin-typescript2`
- Source directory to implement: `src/`
- Test command: `npx jest` (run against `__tests__`)
- Specification / docs: https://github.com/ezolenko/rollup-plugin-typescript2

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

npm npm v0.37.0 v0.37.0 downloads downloads 8.7M/month 8.7M/month Node.js CI Node.js CI passing passing Rollup plugin for typescript with compiler errors.

This is a rewrite of the original rollup-plugin-typescript , starting and borrowing from this fork.

This version is somewhat slower than the original, but it will print out TypeScript syntactic and semantic diagnostic messages (the main reason for using TypeScript after all).

This plugin inherits all compiler options and file lists from your tsconfig.json file. If your tsconfig has another name or another relative path from the root directory, see tsconfigDefaults , tsconfig , and tsconfigOverride options below. This also allows for passing in different tsconfig files depending on your build target.

noEmitHelpers : false importHelpers : true noResolve : false rollup-plugin-typescript2 Installation # with npm npm install rollup-plugin-typescript2 typescript tslib --save-dev # with yarn yarn add rollup-plugin-typescript2 typescript tslib --dev Usage // rollup.config.js import typescript from 'rollup-plugin-typescript2'; export default { input: './main.ts', plugins: [ typescript(/*{ plugin options }*/) ] } Some compiler options are forced noEmit : false (Rollup controls emit) noEmitOnError : false (Rollup controls emit. See #254 and the abortOnError plugin option below) inlineSourceMap : false (see #71) outDir : ./placeholder in cache root (see #83 and Microsoft/TypeScript#24715) declarationDir : Rollup's output.file or output.dir (unless useTsconfigDeclarationDir is true in the plugin options) allowNonTsExtensions : true to let other plugins on the chain generate typescript; update plugin's include filter to pick them up (see #111) module : defaults to ES2015 . Other valid values are ES2020 , ES2022 and ESNext (required for dynamic imports, see #54).

moduleResolution : defaults to node10 (same as node ), but value from tsconfig is used if specified. Other valid (but mostly untested) values are node16 , nodenext and bundler .

If in doubt, use node10 .

classic is deprecated and changed to node10 . It also breaks this plugin, see #12 and #14.

allowJs : lets TypeScript process JS files as well. If you use it, modify this plugin's include option to add "*.js{,x}", "**/*.js{,x}" (might also want to exclude "**/node_modules/**/*" , as it can slow down the build significantly).

Must be before rollup-plugin-typescript2 in the plugin list, especially when the browser: true option is used (see #66).

See the explanation for rollupCommonJSResolveHack option below.

This plugin transpiles code, but doesn't change file extensions. @rollup/plugin-babel only looks at code with these extensions by default: .js,.jsx,.es6,.es,.mjs . To workaround this, add .ts and .tsx to its list of extensions.

Some compiler options have more than one compatible value Some options need additional configuration on plugin side Compatibility @rollup/plugin-node-resolve @rollup/plugin-commonjs @rollup/plugin-babel // ...

import { DEFAULT_EXTENSIONS } from '@babel/core'; // ...

babel({ See #108 cwd : string The current working directory. Defaults to process.cwd() .

tsconfigDefaults : {} The object passed as tsconfigDefaults will be merged with the loaded tsconfig.json .

The final config passed to TypeScript will be the result of values in tsconfigDefaults replaced by values in the loaded tsconfig.json , replaced by values in tsconfigOverride , and then replaced by forced compilerOptions overrides on top of that (see above).

For simplicity and other tools' sake, try to minimize the usage of defaults and overrides and keep everything in a tsconfig.json file ( tsconfig s can themselves be chained with extends , so save some turtles).

This is a deep merge: objects are merged, arrays are merged by index, primitives are replaced, etc. Increase verbosity to 3 and look for parsed tsconfig if you get something unexpected.

tsconfig : undefined Path to tsconfig.json . Set this if your tsconfig has another name or relative location from the project directory.

extensions: [ ...DEFAULT_EXTENSIONS, '.ts', '.tsx' ] }), // ...

Plugin options let defaults = { compilerOptions: { declaration: true } }; let override = { compilerOptions: { declaration: false } }; // ...

plugins: [

tsconfigDefaults: defaults,

tsconfig: "tsconfig.json",

tsconfigOverride: override

}) ] By default, will try to load ./tsconfig.json , but will not fail if the file is missing, unless the value is explicitly set.

tsconfigOverride : {} See tsconfigDefaults .

check : true Set to false to avoid doing any diagnostic checks on the code. Setting to false is sometimes referred to as transpileOnly by other TypeScript integrations.

verbosity : 1 0 -- Error 1 -- Warning 2 -- Info 3 -- Debug clean : false Set to true to disable the cache and do a clean build. This also wipes any existing cache.

cacheRoot : node_modules/.cache/rollup-plugin-typescript2 Path to cache. Defaults to a folder in node_modules .

include : [ "*.ts{,x}", "**/*.ts{,x}", "**/*.cts", "**/*.mts" ] By default compiles all .ts and .tsx files with TypeScript.

exclude : [ "*.d.ts", "**/*.d.ts", "**/*.d.cts", "**/*.d.mts" ] But excludes type definitions.

abortOnError : true Bail out on first syntactic or semantic error. In some cases, setting this to false will result in an exception in Rollup itself (for example, unresolvable imports).

rollupCommonJSResolveHack : false Deprecated. OS native paths are now always used since 0.30.0 (see #251), so this no longer has any effect -- as if it is always true .

objectHashIgnoreUnknownHack : false The plugin uses your Rollup config as part of its cache key. object-hash is used to generate a hash, but it can have trouble with some uncommon types of elements. Setting this option to true will make object-hash ignore unknowns, at the cost of not invalidating the cache if ignored elements are changed.

Only enable this option if you need it (e.g. if you get Error: Unknown object type "xxx" ) and make sure to run with clean: true once in a while and definitely before a release.

(See #105 and #203) useTsconfigDeclarationDir : false If true, declaration files will be emitted in the declarationDir given in the tsconfig . If false, declaration files will be placed inside the destination directory given in the Rollup configuration.

Set to false if any other Rollup plugins need access to declaration files.

typescript : peerDependency If you'd like to use a different version of TS than the peerDependency, you can import a different TypeScript module and pass it in as typescript: require("path/to/other/typescript") .

You can also use an alternative TypeScript implementation, such as ttypescript , with this option.

Must be TS 2.0+; things might break if the compiler interfaces changed enough from what the plugin was built against.

transformers : undefined experimental, TypeScript 2.4.1+ Transformers will likely be available in tsconfig eventually, so this is not a stable interface (see Microsoft/TypeScript#14419).

For example, integrating kimamula/ts-transformer-keys: const keysTransformer = require('ts-transformer-keys/transformer').default; const transformer = (service) => ({

before: [ keysTransformer(service.getProgram()) ],

after: [] }); // ...

plugins: [

typescript({ transformers: [transformer] }) ] Declarations This plugin respects declaration: true in your tsconfig.json file. When set, it will emit *.d.ts files for your bundle. The resulting file(s) can then be used with the types property in your package.json file as described here.

By default, the declaration files will be located in the same directory as the generated Rollup bundle. If you want to override this behavior and instead use declarationDir , set useTsconfigDeclarationDir: true in the plugin options.

The above also applies to declarationMap: true and *.d.ts.map files for your bundle.

This plugin also respects emitDeclarationOnly: true and will only emit declarations (and declaration maps, if enabled) if set in your tsconfig.json . If you use emitDeclarationOnly , you will need another plugin to compile any TypeScript sources, such as @rollup/plugin- babel , rollup-plugin-esbuild , rollup-plugin-swc , etc. When composing Rollup plugins this way, rollup-plugin-typescript2 will perform type-checking and declaration generation, while another plugin performs the TypeScript to JavaScript compilation.

Some scenarios where this can be particularly useful: you want to use Babel plugins on TypeScript source, or you want declarations and type-checking for your Vite builds (NOTE: this space has not been fully explored yet).

The way TypeScript handles type-only imports and ambient types effectively hides them from Rollup's watch mode, because import statements are not generated and changing them doesn't trigger a rebuild.

Otherwise the plugin should work in watch mode. Make sure to run a normal build after watch session to catch any type errors.

TypeScript 2.4+ Rollup 1.26.3+ Node 6.4.0+ (basic ES6 support) See CONTRIBUTING.md Watch mode Requirements Reporting bugs and Contributing
