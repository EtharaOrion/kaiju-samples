# TRUTH.md

## Problem

The `graphql-jit` library compiles GraphQL queries into optimized JavaScript executor functions instead of walking the AST at runtime. In the current state of the repository, the core implementation modules have been *gutted*: nearly every function body has been replaced with `throw new Error("STUB")` (and several benchmark schema resolvers likewise). The task is to restore correct implementations of the stubbed modules so that the JIT compiler once again produces a working `compiledQuery` whose `.query(root, context, variables)` result matches what `graphql-js`'s reference `execute` would produce.

Stubbed production modules of interest: `src/ast.ts`, `src/compat.ts`, `src/error.ts`, `src/execution.ts`, `src/generate.ts`, `src/inspect.ts`, `src/json.ts`, `src/memoize.ts`, `src/non-null.ts`, `src/resolve-info.ts`, `src/runtime.ts`. The `src/__benchmarks__/*` files are stubbed test schemas/harness and are only exercised indirectly (they must compile and expose valid resolvers, but no benchmark tests are in scope).

The behavior is validated by four test suites: `directives.test.ts`, `execution.test.ts`, `variables.test.ts`, and `resolve-info.test.ts`.

## Behavioral contract

The public entry point is `compileQuery(schema, document, operationName?, options?)`. It returns either a *compiled query object* or an *execution-result-shaped error object*.

**Compilation / entry-point guards**
- If no `document` is passed, it must return an error result whose `errors[0].message` reports a missing document (not throw an uncaught error into the test).
- If no `schema` is passed, it must throw/return an error stating the schema is required.
- If `options.resolverInfoEnricher` is provided but is not a function, compilation must fail with a clear message that the enricher must be a function.
- With `options.debug` truthy, the returned object additionally exposes the generated source under an intentionally ugly property name (`__DO_NOT_USE_THIS_OR_YOU_WILL_BE_FIRED_compilation`) — a string of the compiled function body.
- `isCompiledQuery(x)` must return `true` for a successfully compiled query object and `false` for a plain execution result (i.e. it distinguishes by the presence of the callable `query` member).
- The produced `query` function should carry a meaningful bound function `name`.

**Operation selection**
- With no `operationName`: use the single operation if there is exactly one; use the inline/anonymous operation appropriately.
- Return a GraphQL error if there is no operation, if `operationName` is omitted while multiple operations exist, or if a named `operationName` matches nothing.
- Route to the query, mutation, or subscription root type according to the operation type.

**Execution semantics (parity with graphql-js)**
- Field ordering in the response must follow selection-set order regardless of async resolution order.
- Parallel/duplicate fragment selections merge into one collected field set.
- `root` value and `context` thread correctly to resolvers; `info` reflects current execution state (path, field nodes, parent type, return type, etc.).
- Arguments are coerced and threaded to resolvers; unset arguments are absent (not `undefined` keys); default argument values apply when omitted; `NaN`/`Infinity`/`-Infinity` literals are accepted.
- Field names that are JS keywords or literally `parent` must work as output keys and internal variable names.
- Errors from resolvers (sync throw or promise rejection) null out the correct subtree and are recorded in `errors` with a `path`. For non-nullable fields the error propagates upward and the full response `path` is included.
- `isTypeOf` failures produce the appropriate runtime error.
- Non-executable definitions (e.g. type system definitions mixed into the document) are ignored.
- Illegal / unknown fields do not appear in output.

**Directives (`@skip` / `@include`)**
- Recognize the directive by matching `it.name.value` against `GraphQLSkipDirective.name` / `GraphQLIncludeDirective.name`, and find the `if` argument by `it.name.value === "if"`.
- `@skip(if:true)` and `@include(if:false)` omit the field/fragment/inline-fragment (including anonymous inline fragments) at compile time so the resolver is never invoked; `@skip(if:false)` / `@include(if:true)` keep it.
- Both may combine (skip wins to omit).
- `if` may be a literal boolean or a variable; variable value is read at runtime. Directive `if` default values apply.
- Error scenarios must raise `GraphQLError`s at compile time: missing `if` argument (message names the directive and the missing `if`); non-boolean literal type; a variable used for `if` that is not declared in the operation; a variable whose declared type is not `Boolean`.
- Skip/include semantics must propagate correctly through nested fragments and inline fragments, and when the *same underlying field node* is reachable via multiple paths (e.g. two inline fragments/spreads) with differing directives — each path is evaluated independently and merged (issue‑166 scenarios).

**Variable & input coercion (`variables.test.ts`)**
- Coerce inline literal input objects and runtime variable values against input types: scalars, enums, lists (incl. single-value→list wrapping, nested lists, nulls inside lists), input objects (nested), non-null wrappers.
- Missing variable → `undefined`; explicit `null` → `null`; default values apply only when the variable is truly omitted; explicit null overrides defaults.
- Custom scalar `parseLiteral`/`parseValue` runs; when a custom scalar throws, the produced GraphQL error must preserve `originalError`.
- Produce field/coercion errors (not crashes) for: wrong types, missing nested non-null, omitted nested non-null, unknown input-object fields, non-null violated by null, oversized (64-bit) integers, invalid/unknown types used as values, arrays passed where scalars expected, random enum values / strings.

**Resolve-info enrichment (`resolve-info.test.ts`)**
- Without an enricher, `info` is the standard resolve-info object.
- A `null` enricher is treated as "no enricher".
- A non-function enricher fails compilation (see above).
- The enricher's returned object is merged into the resolve info: it can add new properties and can overrule existing resolve-info properties.

## Solution decomposition

- **`src/ast.ts`** — Collection/coercion of the operation AST:
  - Directive matching predicates (skip/include by directive name, `if` argument by name, variable-definition lookup by variable name).
  - `getArgumentDefs`: build a name→argNode map (`keyMap` keyed by `arg.name.value`), then for each arg definition coerce literal values, track variables referenced by AST values, and record `MissingVariablePath`s (mapping each referenced variable's `valueNode`/`path`).
  - Skip/include compilation producing runtime boolean expressions plus compile-time validation of the `if` argument.
- **`src/compat.ts`** — Thin wrappers smoothing over graphql-js version differences (type predicates, field/argument access, error construction). Must return the shapes the rest of the code expects.
- **`src/inspect.ts`** — Human-readable value stringification used in error messages (objects, arrays, functions, symbols, cyclic guards). Error text parity matters for some assertions.
- **`src/error.ts`** — Constructing/attaching GraphQL errors with correct `path`, `locations`, `nodes`, and crucially preserving `originalError` for wrapped resolver/scalar failures.
- **`src/json.ts`** — Fast serializer (`stringify`) used by the compiled query; must round-trip to the same JSON as `JSON.stringify` for result objects.
- **`src/memoize.ts`** — Memoization helper used to cache per-type/field compilation work.
- **`src/non-null.ts`** — Non-null propagation helpers (null a subtree, bubble to nearest nullable ancestor, record error with full path).
- **`src/resolve-info.ts`** — Building the resolve-info object and applying the optional enricher (merge semantics, validation that it is a function).
- **`src/runtime.ts` / `src/generate.ts`** — Runtime support invoked by generated code and generation of the executor source respectively.
- **`src/execution.ts`** — Orchestrator: `compileQuery`, `isCompiledQuery`, operation selection, field collection, code generation wiring, `query`/`stringify` members, debug source exposure, and all entry-point guards.
- **`src/__benchmarks__/*`** — Restore schema resolvers to return the underlying data (mostly `Promise.resolve(obj.field)` / calling `article(id)` / `getPic(...)`), define the `Author` field thunk, and the benchmark harness (compile each bench, compare JIT vs graphql-js output, build a `Benchmark.Suite`, chain runs on completion, `isNotNull` = `a != null`).

## Solution space

- The generated-code strategy is internal: an implementation may generate slightly different JavaScript source than the golden version. Only observable behavior (result equality with graphql-js, error shapes, debug string existence) is tested — not the exact generated text. Tests that inspect the debug compilation only check that a string is returned.
- `isCompiledQuery` may be implemented by checking for a callable `query` property or by a branded flag, as long as it discriminates compiled objects from execution results.
- Variable/argument coercion may reuse graphql-js's `coerceInputValue`/`valueFromAST`-style helpers or hand-rolled coercion, provided the same errors and default-value semantics result.
- Skip/include may be resolved fully at compile time (pruning the selection set) or via runtime guards for variable-driven cases; either is acceptable as long as skipped resolvers are never invoked.
- The benchmark resolvers can return values directly or wrapped in promises; the harness structure is not asserted by any in-scope test, so latitude exists there — it only needs to type-check and compile.
- `json.ts` may delegate to `JSON.stringify` or implement a custom fast path; equality of output is the only requirement.
- The resolve-info enricher merge can be a shallow object spread or explicit assignment; the requirement is that enricher keys win and additive keys appear.

## Known pitfalls

- **Skipped resolvers must not run.** Omission has to happen before resolver invocation (a test spies that the resolver is not called), so filtering at execution time after calling is wrong.
- **Directive error timing.** Missing/invalid `if`, undeclared variable, and non-Boolean variable type must raise `GraphQLError`s during compilation, with the directive name embedded in the "missing required arguments: 'if'" message.
- **Same field node via multiple paths** (issue‑166): do not de-duplicate field nodes in a way that drops per-path skip/include; merging must respect each path's directive conditions.
- **Field ordering** must be deterministic by selection order even when some resolvers are async and settle out of order.
- **Non-null propagation**: an error in a non-null field must null the nearest nullable ancestor and include the *full* path; forgetting propagation yields wrong `data`/`errors`.
- **`originalError` preservation**: wrapping a custom-scalar or resolver exception must keep the original error reachable, or `variables.test.ts`'s custom-scalar test fails.
- **Unset arguments** must be absent from the args object, not present as `undefined` keys.
- **JS-keyword / `parent` field names** must be safely used as object keys and as generated variable identifiers (escape or alias them).
- **`NaN`/`Infinity`/`-Infinity`** literals must survive coercion into resolver arguments.
- **64-bit integer inputs** must be rejected (Int is 32-bit), producing a coercion error rather than silently truncating.
- **Operation-selection edge cases** (no op, multiple ops without a name, unknown name) must yield errors, not throws that escape the compiler.
- Do not let `compileQuery` throw for a missing document — it must surface as an error result the test can read.

## Cheat surface

- Do **not** hardcode expected response objects, error strings, or directive outcomes keyed to specific test queries. The compiler must genuinely collect fields, coerce inputs, and evaluate directives.
- Do **not** detect the test environment, test names, or bypass compilation to return canned results.
- Do **not** stub `isCompiledQuery` to always return a constant; it must discriminate real compiled queries from execution results.
- Do **not** satisfy directive tests by simply always-including or always-excluding; both `@skip`/`@include` truth tables plus variable/default handling are exercised.
- Do **not** swallow coercion/validation errors to make tests pass; the specific error messages, `path`s, and `originalError` linkage are asserted.
- Re-deriving results by internally delegating the entire `query` execution to graphql-js's `execute` (instead of running compiled/generated code) would defeat the library's purpose; the debug compilation must reflect real generated code, and behavior must come from the compiled path.

## Success criteria

- All listed `fail_to_pass` tests in `directives.test.ts`, `execution.test.ts`, `variables.test.ts`, and `resolve-info.test.ts` pass.
- The project type-checks/builds (no remaining `throw new Error("STUB")` in the implemented modules; benchmark schemas expose valid resolvers and compile).
- `compileQuery` returns a working compiled object whose `.query(...)` output is JSON-equal to graphql-js `execute` for the covered queries, with matching `errors` (messages, paths, and preserved `originalError`).
- Entry-point guards (missing document/schema, bad enricher), `isCompiledQuery`, debug-source exposure, and bound-function naming behave as described.
- No previously passing behavior regresses (though none are explicitly listed, the implemented modules must remain internally consistent).