# TRUTH.md

## Problem

The `jsons` library (a Python JSON (de)serialization framework) has been "stubbed": many of its internal modules and public helper methods have had their bodies removed (replaced with `pass`, missing docstrings, or empty implementations). As shipped, importing and exercising the library fails or produces wrong results, so the entire test suite for (de)serialization of primitives, collections, datetimes, dataclasses, attrs classes, enums, paths, custom serializers, decorators, forking, multitasking, and the `JsonSerializable` mixin is red.

The task is to restore the missing behavior across the stubbed modules so that the library's public API (`jsons.dump`, `jsons.load`, `jsons.dumps`, `jsons.loads`, `jsons.dumpb`, `jsons.loadb`, `jsons.transform`, the `@dumped`/`@loaded` decorators, key transformers, the `JsonSerializable` base class, exception classes, verbosity flags) works end-to-end and every listed `fail_to_pass` test passes.

A GitHub Actions workflow file (`.github/workflows/pythonapp.yml`) is also expected to exist (CI matrix installing test extras and running the test/coverage targets), but it is not exercised by the test suite.

## Behavioral contract

The restored library must satisfy these observable behaviors (as asserted by the tests):

- **Round-trip fidelity**: for supported types, `load(dump(x), type(x)) == x`. This holds for primitives (int, float, str, bool, None), lists, tuples (incl. `NamedTuple`), sets, deques, dicts (incl. special/hashed keys and enum keys), `OrderedDict`, `defaultdict`, `ChainMap`, `Counter`, complex numbers, `Decimal`, `datetime`/`date`/`time`/`timedelta`/`timezone`/`ZoneInfo`, `UUID`, `pathlib` path types, enums/IntEnums, plain objects, dataclasses, and attrs classes.

- **Type inference on dump**: when no `cls` is passed, the object's runtime class selects the serializer; the most specific registered serializer for the class (walking its MRO) is used.

- **Type resolution on load**: `load` uses (in priority order) an explicit `cls` argument, a class embedded in verbose metadata, and a type inferred from generic parameters. Verbose (announced) metadata takes precedence over an inferred generic type parameter, while an explicit `cls` normally takes precedence over inference.

- **Verbose mode**: dumping with a verbosity level that announces classes embeds a `-meta` structure recording the fully-qualified class name (and, for deeper levels, nested type info); loading such a structure reconstructs the correct type even without an explicit `cls`.

- **None handling**: loading `None` succeeds only when the target type admits `None` (e.g. `Any`, `object`, `None`, `NoneType`, or an `Optional`/`Union` including `NoneType`); otherwise a deserialization error is raised.

- **Strictness & warnings**: in non-strict list/collection loading, per-element failures produce warnings (respecting a suppress-warnings mechanism) rather than aborting; in strict mode failures propagate. Partially-deserialized dicts behave differently in strict vs non-strict mode.

- **Error reporting**: deserialization errors carry the offending source, the target class, and (for lists) point at the failing index; loading malformed JSON strings/bytes raises the library's decode/deserialization errors; missing required constructor args raise a signature-mismatch error; supplying too many args raises an error.

- **datetime offset formatting**: naive datetimes are treated as local time and emit a warning (keyed so it can be suppressed); tz-aware datetimes serialize with a correct ISO offset string, with support for microseconds and stripped microseconds.

- **Key transformers**: camelCase/snake_case/PascalCase/lispcase transformers convert dict keys on dump/load and round-trip via case transformers.

- **Custom serializers/deserializers**: registering custom functions for a type overrides default behavior; forks isolate registrations.

- **Forking**: `fork()` creates an independent registry (a subclass of the state holder) whose serializer/deserializer changes do not leak into the parent; forks of forks are supported and get distinct names.

- **`JsonSerializable` mixin**: instances expose a `json` property equivalent to `dump(self)`; the class exposes `from_json`/`load` equivalent to `load(...)` with that class; `with_dump`/`with_load` return a (optionally forked) class whose `dump`/`load` methods are pre-bound with supplied keyword arguments; `fork` produces an isolated subclass.

- **Decorators**: `@dumped`/`@loaded` transform a function's arguments and/or return value, supporting sync and async functions, methods, and whole classes; supplying a wrong loader/dumper raises appropriately.

- **`transform`**: converts an object from one type to another (optionally via an attribute/key mapper) by dumping then loading.

- **Multitasking**: dumping/loading lists can be split across threads or processes; results are placed back in original order.

- **`Flag` compatibility enum**: supports combining members with `|` and reconstructing a (possibly composite/pseudo) member from an integer value, including composite names joined by `|`.

- **Compatibility helpers**: `get_type_hints` works across Python versions (tolerating classes without explicit constructors, resolving forward refs via the defining module's namespace, and merging `__init__` hints on 3.10+ while dropping the `return` key); helpers extract union params, tuple-ellipsis, and the naked/origin class of generic types across versions.

## Solution decomposition

Sub-goals, roughly one cluster per stubbed module:

1. **Common core (`_common_impl.py`)**: class-name resolution (fully-qualified and plain), resolving a class from a string (including generic `Origin[Sub, ...]` strings), precedence logic between explicit/meta/inferred classes, and the `None`-compatibility predicate. `get_class_name` must handle `None` and objects lacking `__name__`.

2. **Compatibility (`_compatibility_impl.py`)**: the `Flag` enum's `_get_inst` (reconstruct a member or synthesize a composite pseudo-member from a value), plus version-tolerant `get_type_hints`, union-param/tuple-ellipsis/naked-class extraction.

3. **Serializer/deserializer registry (`_lizers_impl.py`)**: setting and MRO-aware lookup of (de)serializers, honoring forks.

4. **Dump/Load orchestration (`_dump_impl.py`, `_load_impl.py`)**: pick serializer/deserializer, thread through kwargs, track initial-vs-nested calls, clear caches on the initial load, validate JSON input types, and raise correct exceptions.

5. **Type-specific impls** wired through the registry: datetimes (`_datetime_impl.py` offset strings, warnings), and the many per-type serializers/deserializers (mostly already present, but dependent on the restored core).

6. **Key transformers (`_key_transformers.py`)**: regex-based case conversions.

7. **Validation (`_validation.py`)** and **extra helpers (`_extra_impl.py`)**.

8. **Fork implementation (`_fork_impl.py`)**: create uniquely-named isolated subclasses of the state holder.

9. **Multitasking (`_multitasking.py`)**: `_fill` populates the target list by applying the func to each slice element and storing results at their indices; slicing/starting tasks distributes work.

10. **Caching (`_cache.py`)**: wrapper registering cached functions for centralized clearing.

11. **Public helper classes**: `JsonSerializable` (`with_dump`, `with_load`, `fork`, `json` property, `from_json`), verbosity flag definitions (`classes/verbosity.py`), decorators (`decorators.py`), transform (`_transform_impl.py`), and exception classes (`exceptions.py`).

## Solution space

- **`Flag._get_inst`**: valid to `try` `cls(value)` and, on failure, build a pseudo-member via `object.__new__(cls)` setting `_value_`/`_name_` (composite name joined from contained members). Alternative acceptable implementations may compute membership differently as long as combined values reconstruct the right composite member and name.

- **`with_dump`/`with_load`**: valid to attach a wrapper method that merges preset kwargs with call-time kwargs (call-time vs preset precedence should match what tests expect) and to return either the same class or a fresh fork depending on the `fork` flag. The wrapper may be a closure, `functools.partial`, or a bound helper.

- **Fork naming**: any scheme producing distinct, isolated subclasses (incrementing counter, uuid, provided name) is acceptable as long as parent/child registries don't share mutable state.

- **`get_type_hints` compatibility**: acceptable to branch on `sys.version_info`, catch `AttributeError`/`NameError`, and resolve forward refs via the module namespace — as long as dataclasses/namedtuples with postponed/`from __future__ import annotations` annotations resolve correctly and the 3.10 `return` key is dropped.

- **Multitasking `_fill`**: a simple loop over the index range applying `func` and assigning into the shared list is sufficient; equivalent vectorized or comprehension-based fills are fine provided ordering is preserved and the `tasks` kwarg is threaded through.

- **Key transformers**: regex or manual string splitting both acceptable.

- **Caching**: any mechanism that lets the initial load/dump clear all per-call caches works; using `lru_cache` with a central clear registry is one route.

- Docstrings/module comments are non-functional; their exact wording is irrelevant to correctness.

## Known pitfalls

- **Cache clearing**: forgetting to clear caches at the end of the *initial* (non-nested) call causes stale results across independent operations and cross-test contamination. Only the outermost call should clear.

- **Initial vs nested detection**: kwargs must carry an `_initial` flag; mishandling it breaks both caching and verbose metadata behavior.

- **Precedence bugs**: swapping the order of explicit/meta/inferred class selection breaks verbose loading and generic type-parameter inference (verbose meta must beat inferred generic parameter).

- **`None`/`Any` handling**: an overly strict `can_match_with_none` rejects valid `Optional` loads; an overly loose one silently accepts invalid `None`s. Must recognize `Any`, `object`, `None`, `NoneType`, and optional/union names.

- **`get_class_name` on edge inputs**: must not crash on `None` or on objects/callables without `__name__` (e.g. lambdas, partials, instances).

- **Naive datetime warning key**: the warning must be emitted with the correct suppression key so `test_suppress_warnings` can silence it, and offset formatting must still succeed.

- **Flag pseudo-members**: must set both `_value_` and `_name_`; the composite name must join contained members with `|` in a deterministic order or tests comparing names fail.

- **Fork isolation**: sharing the class-level lists between parent and fork (mutating in place instead of copying) leaks registrations and fails fork tests.

- **Multitasking ordering**: results must be written to the correct absolute index; with processes, a `Manager` list is needed for cross-process sharing.

- **Exception types & payloads**: wrong-JSON, wrong-bytes, and unfulfilled-arg tests assert specific exception classes carrying source/target info; generic exceptions will fail them.

- **List error index**: non-strict failures must warn (and be suppressible) while strict failures must point at the offending index.

## Cheat surface

- Do **not** special-case test inputs or hardcode expected outputs; the implementation must be generic across all listed types.
- Do **not** delete, skip, `xfail`, or weaken tests, nor edit test files, to make them pass.
- Do **not** stub functions to return canned values that satisfy only the specific assertions.
- Do **not** disable warning machinery globally to fake the suppress-warnings tests; suppression must be a genuine keyed mechanism.
- Do **not** make forks alias the parent registry to trivially "pass" while breaking isolation semantics.
- Restoring behavior must come from real (de)serialization logic, not from catching all exceptions and returning the input unchanged.

## Success criteria

- Every test in the `fail_to_pass` list passes, spanning: attrs, case transformers, chain maps, common/compatibility impl, complex numbers, counters, custom serializers, dates/datetimes/times/timedeltas/timezones/zoneinfo, decimals, decorators (sync/async/method/class), defaultdicts, deques, dicts (special/hashed/enum keys, generics, key transformers, strict), dumpb/loadb, dumps/loads, enums/intenums, exceptions, forking, iterables, `JsonSerializable`, lists (multithread/multiprocess, verbose, error-index, warn-on-fail, fork propagation), objects (deep/verbose/slots/strip variants/inner classes/parent-type), ordered dicts, paths (posix/windows/pure/relative, cross-platform), performance (strict and non-strict), primitives (with casting), sets, specific-version behaviors (dataclasses with future imports/postponed annotations, namedtuples, uuid), str→datetime coercion, suppress-warnings, transform (with mapper), and tuples/namedtuples.
- No previously passing behavior regresses (imports succeed; the public API remains intact).
- The library performs genuine, general (de)serialization; forks are isolated; caches are cleared appropriately; warnings are suppressible; and cross-version type-hint resolution works.
- The CI workflow file exists (not required by tests but part of the intended deliverable).