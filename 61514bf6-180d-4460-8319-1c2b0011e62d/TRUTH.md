# TRUTH.md

## Problem

The repository `rollup-plugin-typescript2` is a Rollup plugin that compiles TypeScript via the TypeScript Language Service, with caching, diagnostics reporting, and declaration emission. Seven source files have had their function bodies (and some lambda expressions) replaced with `throw new Error("STUB")`. The task is to restore correct implementations so that the plugin's unit and integration tests pass.

Stubbed files:
- `src/diagnostics-format-host.ts` — a `FormatDiagnosticsHost` implementation used to pretty-print TS diagnostics.
- `src/diagnostics.ts` — conversion of raw TS diagnostics into an internal shape, and printing them through a Rollup context.
- `src/get-options-overrides.ts` — helper to expand include/exclude globs across directories, plus a file `createFilter`.
- `src/host.ts` — the `LanguageServiceHost` that feeds source snapshots/versions/settings to the TS Language Service.
- `src/index.ts` — the main plugin factory returning a Rollup `Plugin` object with lifecycle hooks.
- `src/rollingcache.ts` — a disk-backed "rolling" cache that ages old entries into a new directory.
- `src/tscache.ts` — the higher-level compile/diagnostic cache built on rolling caches and rollup config hashing.

Each file already has the correct imports, class fields, and type signatures; only the behavior inside stubbed members must be supplied.

## Behavioral contract

Observable behaviors the solution must satisfy (as exercised by the tests):

- **FormatHost** (`diagnostics-format-host.ts`): `getCurrentDirectory()` must return the TS system's current directory; `getNewLine()` must return the TS system's newline string; `getCanonicalFileName` normalizes paths. The exported singleton `formatHost` must be usable by the diagnostics module.

- **convertDiagnostic** (`diagnostics.ts`): maps an array of TS `Diagnostic`s to internal `IDiagnostics` objects. Each entry carries: a flattened plain-text message, a fully formatted (color + context) message, the diagnostic `category`, numeric `code`, and the passed-in `type` string. When a diagnostic has an associated file and a defined start position, the entry also includes a human-readable `fileLine` of the form `fileName(line,character)` using **1-based** line and character numbers.

- **printDiagnostics** (`diagnostics.ts`): for each diagnostic, routes it to the correct Rollup context method based on category — Message → `info`, Error → `error`, Warning (and any unknown/default) → `warn`. When `pretty` is true (default), it prints the pre-formatted message. When `pretty` is false, it prints a compact line combining type, category word (`"error"`/`"warning"`/`""` for messages), `TS<code>`, and the (color-wrapped) flat message; when a `fileLine` exists it is prefixed. Category-to-color mapping: message→white, error→red, warning→yellow. Calls must be invoked with the context as receiver so bail/abort semantics work.

- **expandIncludeWithDirs** (`get-options-overrides.ts`): given an include spec (string or string[]) and a list of root dirs, returns a new list where each include entry is joined to each root and normalized. Order: iterate roots outermost, includes innermost.

- **createFilter** (`get-options-overrides.ts`): builds a Rollup file filter from plugin include/exclude options. When the parsed tsconfig has `projectReferences`, both included and excluded globs are additionally expanded using the referenced project **paths** and concatenated (expanded entries first, original entries after). Emits two debug messages listing the final included and excluded arrays (JSON, indented). Returns a rollup `createFilter` result resolved against `parsedConfig.options.rootDir`.

- **LanguageServiceHost** (`host.ts`):
  - `reset()` clears cached snapshots and versions.
  - `getScriptFileNames()` returns the current set of tracked file names as an array.
  - `getScriptVersion(fileName)` normalizes the path and returns the numeric version (default 0) as a string.
  - `getCustomTransformers()` returns `undefined` when there is no service or no transformers; otherwise it invokes each transformer factory with the service and merges the resulting `before`/`after`/`afterDeclarations` arrays into a single `CustomTransformers` object.
  - `getCompilationSettings()` returns the parsed compiler options; `getTypeRootsVersion()` returns 0; `getCurrentDirectory()` returns the configured cwd; `useCaseSensitiveFileNames()` mirrors the TS system's setting.

- **RollingCache** (`rollingcache.ts`): a two-directory cache (old + new). Must support: checking whether a name exists in the old cache, checking whether old-vs-new content matches (including the special case where the old cache directory doesn't exist / is empty → treated as match only when the requested set is empty, otherwise not), reading/writing entries, marking a name written into the new cache, and "rolling" — moving the new cache to become old and starting fresh. Behaviors validated: `exists`, `match`, `read`, `write`, `touch`, `roll`, and empty-old-dir handling.

- **TsCache** (`tscache.ts`): higher-level cache producing compiled output and diagnostics, keyed by a hash of options/rollup config/snapshot. Provides cached syntactic and semantic diagnostics and cached compiled output, dependency tracking, and a `done()` finalization that rolls the underlying caches. The integration tests exercise clean vs cached runs.

- **plugin factory** (`index.ts`): returns a Rollup `Plugin` named `rpt2` with hooks: `options` (captures rollup options), `buildStart` (creates context, parses tsconfig, prints version info, validates TS/Rollup version ranges, builds filter/host/service/cache, prints compiler-option diagnostics when `check`), `watchChange`, `resolveId` (resolves TS-visible modules, redirects `tslib` to a virtual module, records dependencies), `load` (serves the tslib virtual module), `transform` (snapshots code, emits via cache/service, type-checks, tracks declarations and watch files), `buildEnd`/output hooks (report errors, write declarations, finalize cache). Plugin options are merged over a set of defaults (check on, warning verbosity, standard include/exclude for `.ts/.tsx/.cts/.mts`, abortOnError true, cwd = process.cwd(), etc.), and the TypeScript module is resolved (defaulting to the installed `typescript`) and registered.

## Solution decomposition

1. **Format host** — return real values from `tsModule.sys` for cwd and newline. Trivial but a prerequisite for diagnostics formatting.
2. **Diagnostics conversion** — build the `IDiagnostics` record; compute `fileLine` only when file + start are present, converting to 1-based coordinates.
3. **Diagnostics printing** — a category `switch` selecting print method, color, and category word; branch on `pretty` and presence of `fileLine`; invoke with correct receiver.
4. **Options overrides** — implement the dir-expansion loop and wire `projectReferences` mapping to `.path`; add the two debug log callbacks.
5. **Host** — implement snapshot/version bookkeeping, script filename listing, custom-transformer merging with proper undefined guards, and the simple settings/cwd/case-sensitivity accessors.
6. **Rolling cache & TsCache** — implement the disk cache primitives and the compile/diagnostic caching layer with hashing and finalization.
7. **Plugin factory** — assemble defaults, set up the language service and cache in `buildStart`, and implement each lifecycle hook to drive transform, type-check, declaration emission, and cleanup.

Correct ordering matters in a few places: within `transform`, a file must be marked checked before printing diagnostics (so a bail during print still records the file); declaration deletion happens on `watchChange`; cache finalization (`done`) must tolerate the cache not yet existing (e.g. a tsconfig error in `buildStart`).

## Solution space

- **Diagnostics category mapping**: the `switch` can be written as `if/else` or a lookup table; what matters is that Message→info/white/no-category, Error→error/red/"error", Warning and default→warn/yellow/"warning".
- **fileLine format**: any construction yielding `fileName(line+1,character+1)` is acceptable; using template strings vs concatenation is irrelevant.
- **expandIncludeWithDirs**: array-vs-string handling can use `Array.isArray`/`instanceof Array`/`concat`/`flatMap`; only the resulting normalized, correctly-ordered list matters.
- **getCustomTransformers merge**: may build arrays via `concat`, `push`, or spread, and may omit empty arrays; the essential contract is `undefined` when nothing applies and merged factory outputs otherwise.
- **getScriptVersion**: returning `String(...)`/`.toString()` are equivalent; normalization of the path is the key requirement.
- **Debug messages** in `createFilter`: exact wording is flexible so long as the two debug callbacks report the included and excluded sets (tests assert `context.debug` is called, and/or the resulting filter behavior).
- **Plugin defaults / cache wiring**: many internal variable names and helper factorings are free; correctness is judged by the plugin's externally observable behavior across integration tests (emits, declarations, error reporting, watch mode).
- **TypeScript module resolution**: defaulting to `require("typescript")` when no `typescript` option is provided, then registering it via the module setter, is the expected shape; equivalent lazy resolution is fine.

## Known pitfalls

- **1-based coordinates**: `getLineAndCharacterOfPosition` returns 0-based line/character; forgetting `+1` produces off-by-one `fileLine` strings.
- **`start === 0`**: use an explicit `start !== undefined` (or `!= null`) check, not a truthiness check, or valid position 0 gets dropped.
- **Receiver binding in printDiagnostics**: calling the stored print function without binding the context (`print.call(context, ...)` or an arrow capturing context) breaks `error`'s bail/abort behavior — the bail test depends on this.
- **pretty default**: `pretty` defaults to true; integration tests pass `parsedConfig.options.pretty !== false`, so a falsy-but-defined `pretty` must select the compact format.
- **Custom transformers undefined guard**: must return `undefined` when service is missing OR transformers array is missing/empty, and must not crash when a factory omits `before`/`after`/`afterDeclarations`.
- **Path normalization**: `getScriptVersion` and dir expansion must normalize; failing to do so causes cross-platform / cache-key mismatches.
- **projectReferences mapping**: map to each reference's `path`, not the object itself.
- **Empty old cache dir in RollingCache.match**: an absent old directory must be handled specially — it should only "match" when the requested name set is empty; otherwise report no match so a rebuild occurs.
- **cache.done() when cache is undefined**: `buildEnd`/finalization must guard against the cache never having been constructed (tsconfig error path) — use optional chaining or a null check.
- **noErrors tracking**: emit-skipped and non-empty diagnostics must set the error flag; the "there were errors or warnings" info line is only expected outside watch mode.
- **tslib virtual module**: `resolveId` must map the `tslib` import to the virtual id and `load` must serve its source; the tslib tests fail otherwise.

## Cheat surface

The following would make tests pass without a genuine implementation and must be treated as cheating:

- Editing test files, snapshots, or fixtures under `__tests__/` to accommodate a wrong implementation.
- Hard-coding the specific strings/objects the assertions expect (e.g. returning a canned `IDiagnostics` or a fixed formatted message) instead of deriving them from the actual diagnostic and TS system.
- Special-casing on known fixture file names, test directory paths, or particular error codes to fabricate expected output.
- Stubbing out or no-op'ing type-checking / emit so integration "error" tests trivially pass, or suppressing errors globally to make "no-error" tests pass.
- Replacing the TypeScript language-service-driven compilation with a bypass that echoes input, or disabling caching/rolling to sidestep cache tests.
- Catching and swallowing all exceptions to avoid the `throw new Error("STUB")` paths without providing the real logic.

## Success criteria

- All previously failing tests listed as fail_to_pass now pass, including:
  - Unit tests: `diagnostics-format-host.spec`, `diagnostics.spec` (convert + print categories/formatting), `host.spec` (including custom transformers and undefined cases), `rollingcache.spec` (all four cases), `get-options-overrides.spec` (overrides + createFilter variants), `context.spec`, `tslib.spec`, `parse-tsconfig.spec`.
  - Integration tests: `no-errors` (all variants incl. declarations/maps/allowJs+emitDeclarationOnly), `errors` (semantic/syntax/type-only import, with and without abortOnError/check, tsconfig error), and `watch`.
- No stubbed `throw new Error("STUB")` remains reachable in normal operation.
- The plugin still exposes a Rollup `Plugin` named `rpt2` with the expected hooks and default option shape.
- No test, fixture, or snapshot files are modified; behavior is achieved through the seven source files only.
- Type signatures and public exports of the stubbed modules are preserved (the project compiles).