# TRUTH.md

## Problem

This task is to implement the stubbed-out internals of the `spf13/viper` configuration library (Go). The repository has been reduced to a compiling skeleton in which most functions and methods contain placeholder bodies of the form `_ = "STUB: not implemented"` returning zero values. The public API surface (types, interfaces, function signatures, struct fields) is already present; the behavior behind that surface must be restored so that the full test suite passes.

The stubbed files span the whole library:

- `encoding.go` — codec/encoder/decoder registry and option wiring
- `errors.go` — error types and their `Error()`/`Unwrap()` formatting
- `experimental.go` — experimental feature options
- `file.go` — config-file discovery on a filesystem
- `finder.go` — `Finder` interface, combinator, and option
- `flags.go` — pflag ↔ viper flag adapters
- `logger.go` — logger option(s)
- `remote.go` and `remote/remote.go` — remote provider plumbing
- `util.go` — helper utilities (path handling, map manipulation, key insensitivity, byte-size parsing, etc.)
- `viper.go` — the core `Viper` type: get/set, precedence, aliases, marshaling, reading/writing/merging config, environment binding, flag binding, key traversal

The goal (destination) is a functionally complete viper equivalent to its upstream behavior at this version, verified by ~100 named tests plus two runnable examples and the encoding sub-package codec tests.

## Behavioral contract

The implementation must satisfy these observable behaviors (grouped by concern). Test names in parentheses are the anchors.

### Codec registry (`encoding.go`)
- `NewCodecRegistry()` returns a non-nil, initialized `*DefaultCodecRegistry` (`TestDefaultCodecRegistry`).
- `RegisterCodec(format, codec)` stores a codec keyed by a **case-insensitive** (lowercased) format name and returns nil error.
- `Encoder(format)` / `Decoder(format)` resolve case-insensitively, first from registered codecs, then falling back to built-in codecs for `yaml`/`yml`, `json`, `toml`, and `dotenv`/`env`. When nothing matches they return a non-nil error and a nil encoder/decoder.
- `WithEncoderRegistry`, `WithDecoderRegistry`, `WithCodecRegistry` return `Option`s that install the given registry (or registries) on a `Viper`; a nil argument must be a no-op rather than overwriting with nil.
- The built-in encoding codecs must round-trip correctly (`internal/encoding/{json,toml,yaml,dotenv}` `TestCodec_Encode`/`TestCodec_Decode`).

### Error types (`errors.go`)
- Each error type produces a stable, human-readable message. In particular:
  - `FileNotFoundFromSearchError` reports the config name and, when locations are present, the searched locations.
  - `ConfigFileNotFoundError` is a deprecated alias that **unwraps to** `FileNotFoundFromSearchError` and delegates its message to that unwrapped error.
  - `FileNotFoundError`, `ConfigFileAlreadyExistsError`, `ConfigMarshalError`, `UnsupportedConfigError` each format their respective message including the relevant path/type/underlying error.
  - The `fileLookup()` marker methods exist so the file-lookup errors satisfy `FileLookupError`.
- `errors.Is`/`errors.As` chains through these types work (`TestUnwrapParseErrors`, `TestWrongFileNotFound`, `TestWrongDirsSearchNotFound*`).

### Config file discovery (`file.go`, `finder.go`)
- `findConfigFile` chooses between three strategies: a user-supplied `Finder`, the experimental `locafero`-based finder (when `ExperimentalFinder()` is enabled), or the legacy path/extension search — returning a `FileLookupError`-compatible error when nothing is found.
- The legacy search iterates `configPaths`, and within each path tries `configName + "." + ext` for every `SupportedExts`, plus the bare `configName` when a `configType` is set.
- `exists(fs, path)` returns true only for existing non-directory entries, false for not-exist, and propagates other errors.
- `Finders(...)` combines multiple finders; the combined finder skips nil finders, concatenates all results, and aggregates errors (joined) rather than short-circuiting (`TestFinders`, `ExampleFinder`, `ExampleFinders`).
- `WithFinder(nil)` is a no-op.

### Flag adapters (`flags.go`)
- `pflagValueSet.VisitAll` bridges pflag's visitor into viper's `FlagValue` visitor, wrapping each `*pflag.Flag`.
- `pflagValue` exposes `HasChanged` (flag `Changed`), `Name`, `ValueString` (value `.String()`), and `ValueType` (value `.Type()`). These power `TestBindFlagValue`, `TestBindFlagValueSet`, `TestBindPFlag*`, slice/string-to-string/int flag handling, and shadow behavior.

### Core Viper behavior (`viper.go`, `util.go`)
- **Get/Set/Default precedence**: overrides > flags (changed) > env > config > key/value store > defaults, with aliases resolved and keys handled case-insensitively (`TestOverrides`, `TestDefault`, `TestDefaultPost`, `TestNestedOverrides`, `TestCaseInsensitive*`, `TestBoundCaseSensitivity`).
- **Aliases**: including chained and (safely terminating) recursive aliases (`TestAliases`, `TestAliasesOfAliases`, `TestRecursiveAliases`, `TestAliasInConfigFile`, `TestUnmarshalingWithAliases`).
- **Nested keys / delimiters**: dotted paths, custom key delimiters, slice index access, shadowing detection in nested and flat maps (`TestFindsNestedKeys`, `TestParseNested`, `TestShadowedNestedValue`, `TestDotParameter`, `TestSliceIndexAccess`, `TestIsPathShadowedInFlatMap`, `TestKeyDelimiter`, `TestSubWithKeyDelimiter`, `TestFlagShadow`, `TestAllKeys`).
- **Environment binding**: `BindEnv`, `AutomaticEnv`, prefix, key replacer, empty-value handling both allowed and not (`TestEnv`, `TestMultipleEnv`, `TestEmptyEnv`, `TestEmptyEnv_Allowed`, `TestEnvPrefix`, `TestAutoEnv`, `TestAutoEnvWithPrefix`, `TestSetEnvKeyReplacer`, `TestEnvKeyReplacer`, `TestEnvSubConfig`, `TestAllKeysWithEnv`).
- **Reading**: `ReadInConfig`, `ReadConfig`, `SetConfigFile`, file-cache invalidation on `SetConfigName`, format detection for YAML/JSON/TOML/dotenv (`TestReadInConfig`, `TestReadConfig`, `TestReadConfigWithSetConfigFile`, `TestGetConfigFile`, `TestSetConfigNameClearsFileCache`, `TestYML`, `TestJSON`, `TestTOML`, `TestDotEnv`, `TestDirsSearch`).
- **Writing**: `WriteConfig`, `WriteConfigAs`, `SafeWriteConfig(As)` with already-exists errors and hidden-file handling (`TestWriteConfig`, `TestWriteConfigTOML`, `TestWriteConfigDotEnv`, `TestSafeWrite*`, `TestWriteHiddenFile`).
- **Merging**: `MergeConfig`, `MergeInConfig`, `MergeConfigMap`, override-type semantics, no-op merges (`TestMergeConfig*`).
- **Unmarshaling**: `Unmarshal`, `UnmarshalExact`, `UnmarshalKey`, decode-hook defaults, decoder options, automatic-env interaction, dot-separator backward compatibility, experimental bind-struct (`TestUnmarshal*`).
- **Sub / IsSet / SizeInBytes / AbsPathify** and map copy/insensitivise helpers (`TestSub`, `TestIsSet`, `TestSizeInBytes`, `TestAbsPathify`, `TestCopyAndInsensitiviseMap`).
- **File watching** works (`TestWatchFile`).
- **Remote** provider precedence and plumbing (`TestRemotePrecedence`) — the local `remote.go` shim and `remote/remote.go` must compile and provide expected fallbacks.

### Options
- All `With...`/`Experimental...` functions return `Option` values implemented via the existing `optionFunc` adapter, and mutate the appropriate `Viper` field (`experimentalBindStruct`, `experimentalFinder`, `finder`, registries, logger, etc.).

## Solution decomposition

Sub-goals, roughly in dependency order:

1. **Options plumbing.** Implement every `Option`-returning function as a closure over `*Viper` (using the provided `optionFunc`). Guard nil arguments where a nil would corrupt state. This unblocks compilation of many call sites.

2. **Error types.** Give each error a correct `Error()` string and wire `ConfigFileNotFoundError.Unwrap()` to `FileNotFoundFromSearchError`; implement the empty `fileLookup()` markers. Message text should match what tests/format expectations assume.

3. **Codec registry.** Implement init/register/lookup with lowercased keys and a built-in fallback switch. Encoder/Decoder wrap `codec(format)` and translate the not-found case into an error.

4. **Flag adapters.** Thin delegations to `pflag` — the only subtlety is faithfully forwarding each of the four accessors and the visitor.

5. **Finder + file discovery.** Implement `combinedFinder.Find` (skip nil, gather results, join errors), then `findConfigFile` dispatch, `findConfigFileWithFinder`, `findConfigFileOld`, `searchInPath`, and `exists`.

6. **Core Viper engine (`viper.go`) + `util.go` helpers.** The largest piece: value resolution, precedence, aliasing, nested-key traversal, env/flag binding, read/write/merge, unmarshal, sub, watch. Rely on the encoding registry and finder pieces above.

7. **Remote shims.** Make `remote.go` / `remote/remote.go` provide the interface implementations and fallbacks so remote-related code paths compile and behave.

## Solution space

- **Registry fallback for built-ins**: A hardcoded `switch` on lowercased format inside the internal `codec` lookup is one route; equally valid is pre-populating the `codecs` map with the built-in codecs during `init()`. Either satisfies case-insensitive lookup and the built-in defaults, as long as user-registered codecs can still override built-ins.
- **Error messages**: Exact wording is flexible where tests only check wrapping/`errors.Is`/`errors.As` behavior, but for tests that assert on message substrings you must include the relevant name/path/type. When in doubt, mirror upstream viper phrasing.
- **`ConfigFileNotFoundError` vs `FileNotFoundFromSearchError`**: The deprecated type may delegate both message and identity via `Unwrap`; alternatively it may format independently — but it MUST unwrap to the search error so `errors.As` chains used by tests succeed.
- **File discovery**: The experimental `locafero`-based finder and the legacy manual search are both required paths (selected by config), but the *manual* search may be written with either `filepath.Join`-per-extension loops or a helper; only the resulting found-file semantics matter.
- **Combined finder error handling**: Using `errors.Join` to aggregate is the natural approach; any scheme that returns all successful results and does not drop errors is acceptable.
- **Map/key helpers in `util.go`**: Implementation details (recursion vs iteration, in-place vs copy) are free as long as case-insensitivity, deep copying, and shadow detection produce the documented results.

## Known pitfalls

- **Nil-guarding options**: `WithFinder(nil)`, `WithEncoderRegistry(nil)`, etc. must be no-ops. Overwriting a valid registry/finder with nil breaks later lookups.
- **Case-insensitivity everywhere**: Format names, config keys, env-derived keys, and alias names are all treated case-insensitively. Forgetting to lowercase in the registry, or to insensitivise nested maps, breaks many tests.
- **Unwrap direction**: `ConfigFileNotFoundError` must unwrap *to* `FileNotFoundFromSearchError`, not the reverse; the two structs share identical fields, so conversion is straightforward but easy to get backwards.
- **Combined finder must not short-circuit**: It should continue past a finder that errors, collecting both results and errors, rather than returning on the first error.
- **`exists` semantics**: Return `false, nil` for not-exist (not an error), `false, err` for other stat errors, and treat directories as non-existent config files (`!IsDir()`).
- **Encoder/Decoder not-found**: Must return a non-nil error AND a nil interface value — returning a zero-value non-nil codec would mask the failure.
- **Recursive/chained aliases**: Alias resolution must terminate (no infinite loop) even when aliases reference each other.
- **Precedence order**: The get path must respect the full precedence hierarchy; a flag that has not "changed" must not override config/env values, while a changed flag should.
- **Search order in `searchInPath`**: Extensions are tried in `SupportedExts` order; the bare-name lookup only applies when an explicit `configType` is set.
- **Do not leave stubs**: Any remaining `_ = "STUB: not implemented"` body will return zero values and silently fail behavioral tests even though the code compiles.
- **Experimental flags gate behavior**: `experimentalFinder` and `experimentalBindStruct` fields must actually change discovery/unmarshal behavior when set, not merely be stored.

## Cheat surface

The following would technically make individual tests pass but do NOT constitute a correct solution and should be rejected:

- **Hardcoding expected test outputs** (specific error strings, specific found paths, specific decoded maps) instead of computing them from inputs.
- **Special-casing test fixture names/paths** inside library code.
- **Detecting the test environment** (env vars, file names, stack inspection) to branch behavior.
- **Leaving the built-in codec fallback out** and only "working" because tests happen to register codecs — the fallback for yaml/json/toml/dotenv is part of the contract.
- **Reproducing the golden diff verbatim** — the specification is about behavior; equivalent alternative implementations are expected and welcome, but copy-pasted stub-replacement lines that were merely memorized are not evidence of a correct independent solution.
- **Swallowing errors** (e.g., returning `nil` error where a not-found/marshal error is required) to make an assertion pass.
- **No-op'ing writes/merges** while returning success, when the test only checks the return code and not the resulting state — the state changes are required.

## Success criteria

- All listed `fail_to_pass` tests pass, including the core `viper` package tests, the two runnable examples (`ExampleFinder`, `ExampleFinders`), and the four internal encoding codec test pairs (`json`, `toml`, `yaml`, `dotenv`).
- The entire module compiles with no remaining `STUB` placeholders and no unused-import or type errors across all stubbed files (including `remote.go` and `remote/remote.go`).
- Behavior matches the Behavioral contract above: correct value precedence, case-insensitive keys/formats, alias resolution, env/flag binding, config read/write/merge, unmarshaling variants, finder combination, and error wrapping.
- No regressions are introduced (there are no separately listed pass_to_pass tests, but the whole suite building and running is expected).
- The solution is general (computes results from inputs and filesystem state) rather than tailored to specific test fixtures.