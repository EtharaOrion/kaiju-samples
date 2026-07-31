# TRUTH.md

## Problem

`Zahgon/css-select` is a TypeScript implementation of a CSS selector engine (a fork of `css-select`). It compiles CSS selector strings into predicate/query functions that run against a DOM-like tree through a pluggable *adapter* interface. Several core source files were reduced to stubs that throw `new Error("STUB")` in the meaningful branches. The task is to restore the real behavior so that the full selector engine works end-to-end.

The public API (`selectAll`, `selectOne`, `is`, `compile`, `compileToken`, `prepareContext`, etc.) must correctly evaluate:
- basic selectors (tag, id, class, universal, `*`),
- attribute selectors in all operator forms (`[a]`, `[a=b]`, `[a~=b]`, `[a|=b]`, `[a^=b]`, `[a$=b]`, `[a*=b]`, `[a!=b]`) including case-insensitivity flags,
- combinators (descendant, child `>`, adjacent `+`, general sibling `~`, and the non-standard parent `<`),
- structural, UI-state, and content pseudo-classes/filters (`:first-child`, `:nth-child`, `:has`, `:not`, `:is`/`:matches`/`:where`, `:contains`, `:icontains`, `:lang`, `:enabled`, `:disabled`, `:checked`, `:read-only`/`:read-write`, `:empty`, `:scope`, etc.),
- options such as `xmlMode`, `context`, `relativeSelector`, `cacheResults`, and custom `pseudos`/`adapter` methods.

Correctness is judged by the listed `fail_to_pass` tests in `test/api.ts`, `test/attributes.ts`, `test/nwmatcher.ts`, `test/qwery.ts`, `test/pseudo-classes.ts`, and `test/sizzle.ts`.

## Behavioral contract

Every compiled selector produces a boolean predicate over an element (for matching) or is composed into query functions returning arrays/single elements (for selecting). Predicates are chained via a `next` continuation: a rule checks its own condition AND then calls `next(element)`. All node access happens through `options.adapter` (methods like `getName`, `getAttributeValue`, `hasAttrib`, `getChildren`, `getSiblings`, `getParent`, `isTag`, optional `prevElementSibling`, `isHovered`, `equals`).

Required observable behaviors:

1. **Attribute rules** (`src/attributes.ts`) — for each operator, read the attribute via `adapter.getAttributeValue`; return `false` when the attribute is absent (`null`); otherwise apply the operator's comparison and chain `next`:
   - `equals`: exact string equality; when case-insensitive, compare lowercased values (and lengths).
   - `hyphen` (`|=`): value equals the attribute, or the attribute begins with `value` immediately followed by a `-`.
   - `element` (`~=`): value appears as a whitespace-separated token; a value containing whitespace can never match (return the always-false function); implement via a word-boundary regex, honoring case-insensitivity.
   - `exists`: `adapter.hasAttrib`.
   - `start` (`^=`): prefix match; empty value → always-false.
   - `end` (`$=`): suffix match; empty value → always-false.
   - `any` (`*=`): substring match; empty value → always-false.
   - `not` (`!=`): logical negation of equals; empty value matches any *present non-empty* attribute; a missing attribute is treated as "not equal" (so it matches).
   Case-insensitivity is decided by a helper (`shouldIgnoreCase(data, options)`) that considers explicit flags and xml/quirks mode.

2. **General selectors / combinators** (`src/general.ts`):
   - `tag`: element name equals the token name (respecting how names are normalized) AND `next`.
   - descendant (uncached path and `WeakMap`-cached path): walk up ancestors via the element-parent helper; succeed if `next` matches any ancestor. The cached variant memoizes per-ancestor `{matches}` results so shared ancestors are not re-tested, but must still return correctly for the queried element.
   - `_flexibleDescendant`: like descendant but *includes the element itself* (used when querying arrays).
   - parent (`<`): true if any tag child satisfies `next`.
   - child (`>`): the direct element-parent satisfies `next`.
   - sibling (`~`): scanning preceding siblings up to (but not including) the element, any tag sibling satisfies `next`.
   - adjacent (`+`): the immediately preceding element sibling satisfies `next`; use `adapter.prevElementSibling` if provided, otherwise find the last tag sibling before the element.
   - universal: matches any element (chaining `next`).

3. **Compilation** (`src/compile.ts`):
   - `absolutize` must detect whether the context represents document-level nodes: the context counts as "has parents" only if every context element is either the internal placeholder element OR is a tag with a non-null element-parent. This gates whether descendant traversals are absolutized.
   - When `relativeSelector` is disabled, a selector whose first token is a traversal must throw an error.
   - `or` combines two predicates with logical OR.

4. **Caching** (`src/helpers/cache.ts`): `cacheParentResults` returns `next(element) && matches(element)` when caching is off or `WeakMap` is unavailable; otherwise it memoizes match results per element and short-circuits by climbing to already-cached ancestors, propagating their cached result down.

5. **Selector helpers** (`src/helpers/selectors.ts`):
   - `getQuality`: for compound/list pseudo data, the quality contribution is the minimum quality among the nested sub-selectors.
   - `includesScopePseudo`: true when the token is a pseudo named `scope`, or a pseudo whose nested selector data recursively includes a scope pseudo.

6. **Index/API** (`src/index.ts`): `defaultEquals` is reference identity (`a === b`). The exported `compile`, `_compileUnsafe`, `_compileToken`, `prepareContext`, `selectAll`, `selectOne`, `is` must wire options with defaults, normalize the query, respect contexts, deduplicate results, and preserve document order.

7. **Pseudo-selectors** (`src/pseudo-selectors/*`): filters (`:contains`, `:icontains`, `:lang`, structural nth filters, etc.), the pseudo-class registry/dispatch (throwing on unknown pseudo-classes and on wrong parameter arity), pure pseudos (`pseudos.ts`), and subselects (`:not`, `:has`, `:is`/`:matches`/`:where`) with correct handling of unsatisfiable vs. universally-valid inner selectors, `:has` caching, xmlMode propagation, and option pass-through to sub-selectors.

Error cases that must throw: pseudo-elements, column combinator, namespaced tags/attributes and universal selector when unsupported, a parameter supplied to a parameterless pseudo, a user-provided pseudo receiving the wrong presence/absence of a parameter, and unknown pseudo-classes.

## Solution decomposition

Sub-goals, roughly in dependency order:

1. **Primitive equality & defaults** (`index.ts`): identity `defaultEquals`, default options object, and the compile/select entry points that thread options and adapters.
2. **Attribute operators** (`attributes.ts`): eight operator functions, each with a case-sensitive and (where applicable) case-insensitive branch, plus early always-false returns for degenerate values.
3. **Combinator predicates** (`general.ts`): tag match plus the traversal predicates, including both cached and uncached descendant paths and the two adjacent-sibling strategies.
4. **Compilation plumbing** (`compile.ts`): context-has-parents detection, relative-selector guard, and the `or` combinator.
5. **Result caching** (`helpers/cache.ts`): parent-result memoization with ancestor short-circuiting.
6. **Static analysis helpers** (`helpers/selectors.ts`): quality scoring for nested selectors and scope-pseudo detection.
7. **Pseudo-selector subsystem** (`pseudo-selectors/*`): filters, registry dispatch with arity validation, pure pseudos, and subselect compilation with satisfiability optimization and option/xmlMode propagation.

## Solution space

- **Ancestor traversal** may be written with `while`, `do/while`, or recursion; either the shared element-parent helper or direct `adapter.getParent` + `adapter.isTag` filtering is acceptable, as long as only tag ancestors are considered and the queried element is included/excluded exactly where the semantics require.
- **String operators** may be implemented with native string methods (`startsWith`/`endsWith`/`includes`/`substr`/`substring`/`slice`) or with regular expressions, provided edge cases (empty value, whitespace-containing `~=` value, absent attribute) yield the correct result. `substr` vs `slice` is a free choice.
- **Case-insensitivity** can lowercase both sides or use case-insensitive regex flags; both are valid.
- **The always-false / always-true short circuits** may use the `boolbase` helpers or equivalent inline constant functions.
- **Descendant caching** can use `WeakMap<Element, {matches:boolean}>` or a plain per-element memo; the reference shares a mutable result object across ancestors, but any implementation that returns identical match results and avoids redundant work passes. A correct-but-slower non-caching implementation also satisfies functional tests (though the "should cache results" tests assert caching behavior — see pitfalls).
- **Adjacent sibling** may rely on the optional `prevElementSibling` adapter method when present; when absent, scanning siblings for the last preceding tag is required. Both branches must exist because tests exercise adapters with and without that method.
- **`getQuality` nested minimum** can be computed with `Math.min(...map(...))` or a manual reduce; equivalent numeric results are fine.

## Known pitfalls

- **Missing-attribute handling differs per operator.** Most operators must return `false` for a `null` attribute, but `!=` must *match* a missing attribute (a missing attribute is "not equal" to a non-empty value), and `!=` with empty value must match only *present, non-empty* attributes. Getting this backward breaks the `no matches` and `!=` attribute tests.
- **Empty/degenerate values:** `^=`, `$=`, `*=` with an empty value must never match; `~=` with a whitespace-containing value must never match. Forgetting these produces false positives.
- **Case-insensitive length check:** for `=` and `!=` case-insensitive branches, comparing lowercased strings without also checking length is still fine, but the reference guards length first; don't compare a truncated `substr` without a length/boundary check for `^=`/`|=`.
- **`|=` boundary:** must accept exact equality *or* prefix-plus-hyphen, not any prefix.
- **Descendant must skip non-tag ancestors/children** — always filter through `adapter.isTag`; iterating raw children/siblings without this yields wrong matches and can crash.
- **Sibling/adjacent stop condition:** stop scanning at the element itself using `adapter.equals`/`options.equals` (not `===`), because custom `equals` and repeated siblings must be handled (there is a "siblings repeat" test). Use `break` at the boundary, not `continue`.
- **Chaining `next`:** every predicate must AND its result with `next(element)`; dropping `next` makes combinators and compound selectors silently over-match.
- **`_flexibleDescendant` includes the element itself**, unlike ordinary descendant — using the ordinary logic breaks array-context queries (`should query array elements directly`).
- **Context "has parents" detection** must account for the internal placeholder element, otherwise scoped/root selections (`#709`, document-root, template-context tests) misbehave.
- **Relative-selector guard** must inspect only the *first* token of each branch and only throw when it is a traversal; throwing too eagerly breaks normal selectors.
- **Caching short-circuit correctness:** when climbing to a cached ancestor, the cached boolean must be propagated to the current element's cache entry; returning the ancestor's raw value without recording it for the element causes inconsistent results (the "cache results" / "skip caching" tests check both modes).
- **Pseudo arity errors** must be thrown, not swallowed: a parameter on a parameterless pseudo, and a missing/extra parameter on user pseudos, are explicit error cases. Unknown pseudo-classes must throw (`#741`).
- **Pseudo-elements, column combinators, namespaced tags/attributes, and universal namespace** must raise errors rather than being treated as matches.
- **Satisfiability optimization in subselects:** unsatisfiable inner selectors should collapse to the always-false function and universally-valid ones should be promoted/simplified — but the *observable* match results must remain correct (`in :not`, `in :has`, `in :is`, `promote rootFunc`, `skip unsatisfiable` tests).
- **Option propagation:** sub-selectors (inside `:has`, `:not`, `:is`) must receive the same options (including `xmlMode` and custom adapter/pseudos), or nested queries misbehave.

## Cheat surface

The following would make specific tests pass without implementing the real engine and must be treated as cheating:

- Special-casing exact selector strings or attribute names/values used in tests instead of implementing general operator logic.
- Hard-coding expected element counts, ids, or arrays for particular test fixtures.
- Detecting the test's specific DOM shape (e.g., known tag names) to short-circuit combinator logic.
- Replacing `defaultEquals` with something that only works for the test adapter, rather than reference identity.
- Making error-path functions detect the exact throwing test input rather than validating pseudo arity / unsupported constructs generally.
- Stubbing pseudo-classes to return `true`/`false` matching only the expected fixtures instead of computing structural/content conditions.
- Bypassing the adapter and reading node properties directly in a way that only works for the bundled DOM handler.

A correct solution must remain adapter-agnostic, driven entirely by generic operator/combinator/pseudo logic and the provided options.

## Success criteria

- All listed `fail_to_pass` tests across `test/api.ts`, `test/attributes.ts`, `test/nwmatcher.ts`, `test/qwery.ts`, `test/pseudo-classes.ts`, and `test/sizzle.ts` pass.
- No `Error("STUB")` remains reachable in the implemented files.
- Attribute operators behave correctly for present/absent attributes, empty/whitespace values, and both case sensitivities.
- All combinators (descendant, child, adjacent, sibling, parent, universal) and tag/id/class/attribute matching return document-ordered, de-duplicated results, using the adapter and `options.equals` throughout.
- Caching toggles honor `cacheResults`, produce identical match results with and without caching, and avoid redundant recomputation when enabled.
- Pseudo-classes, filters, and subselects (including `:has`, `:not`, `:is`/`:matches`/`:where`, `:lang`, `:contains`/`:icontains`, structural nth, UI-state) evaluate correctly and propagate options/xmlMode.
- All specified error conditions (unknown pseudo-class, pseudo-element, column combinator, namespaced tag/attribute, universal namespace, pseudo arity mismatches, relative-selector-when-disabled) throw.
- The solution stays generic (no fixture-specific hacks) and works through the adapter abstraction, so alternative valid implementations of the same behavior also pass.