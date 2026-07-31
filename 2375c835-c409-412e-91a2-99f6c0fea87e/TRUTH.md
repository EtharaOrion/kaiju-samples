# TRUTH.md

## Problem

The `pymonad` package ships a family of monad implementations whose method bodies have been replaced with `pass` stubs (and, in a few cases, whole functions/return statements removed). The library will not function and its test suite fails until every stubbed member is given a correct implementation.

The affected modules fall into these groups:

- **Core abstractions**: `pymonad/monad.py` (the abstract `Monad` base class) and `pymonad/monoid.py` (the `Monoid` base class plus its zero/identity handling).
- **Concrete monads**: `pymonad/either.py`, `pymonad/maybe.py`, `pymonad/list.py`, `pymonad/io.py`, `pymonad/reader.py`, `pymonad/state.py`, `pymonad/writer.py`, `pymonad/promise.py`.
- **Utility**: `pymonad/tools.py` (currying and helper functions).
- **Operator-overloading variants**: `pymonad/operators/*.py`, which re-expose the concrete monads with infix operators (`&`, `>>`, `*`, `+`, etc.) layered on top.

The goal: implement every stub so that the listed `fail_to_pass` tests pass, without breaking imports or the algebraic laws (functor / applicative / monad / monoid) that the tests explicitly check.

## Behavioral contract

Each monad type stores two internal fields set by the base `__init__`: a `value` (the "interesting" result) and a `monoid` (the type-specific metadata: an error flag, a log, a state transition, a truth flag, etc.). All observable behavior must follow from correctly reading and reconstructing those two fields.

Cross-cutting requirements that the tests enforce:

- **`insert` (a.k.a. unit/return)** lifts a bare value into the monad in its "neutral/success" configuration. `Either.insert(x)` behaves like `Right(x)`; `Maybe.insert(x)` behaves like `Just(x)`; `IO`/`Reader`/`State`/`Writer`/`Promise`/`List` insert wraps the value in the trivial computation that yields it.
- **`map` (functor)** applies an ordinary function to the contained value while preserving the metadata/context, and must obey the identity and composition laws. Mapping over a "failure" context (Left / Nothing) returns the failure unchanged rather than applying the function.
- **`amap` (applicative apply)** applies a wrapped function to a wrapped value. It must be associative, homomorphic, and agree with `map` when the function is inserted. For failure-carrying monads, a failure in either the function position or the value position short-circuits to that failure.
- **`bind` (monad)** sequences a value into a function that returns a new monad of the same type; must satisfy left identity, right identity, and associativity. Failure contexts short-circuit and are propagated without calling the continuation.
- **`join`** flattens one level of nesting (used by the List monad and by `then`).
- **`then`** is the user-facing "do the sensible thing" combinator: it accepts either a plain function (behaves like `map`) or a Kleisli function returning a monad (behaves like `bind`). It must transparently dispatch between the two, typically by mapping and then attempting to flatten, recovering gracefully when the result is not nestable.
- **`__eq__` / `__repr__`** must match the exact string/equality forms the tests assert (see individual monads below).

Type-specific contracts:

- **Either**: constructed via `Left`/`Right`. `is_left`/`is_right` report which branch. `either(left_fn, right_fn)` extracts a bare value by dispatching on the branch. `repr` renders as `Left <value>` / `Right <value>`. The `Error` alias subclass behaves identically but with its own repr.
- **Maybe**: constructed via `Just`/`Nothing`. `is_just`/`is_nothing` report presence. `maybe(default, fn)` (aliased as `option`) returns the default when Nothing, else `fn(value)`. `repr` renders `Just <value>` / `Nothing` (and the `Option`/`Some` variant renders `Some <value>` / `Nothing`). Exceptions raised inside mapped/bound functions must NOT be silently converted to Nothing — errors propagate.
- **List**: an indexable, sliceable, `len`-able sequence-like monad (`ListMonad(...)` / `List`). It is also a `Monoid`: `identity_element` is the empty list monad, and combining concatenates. Indexing, slicing (including step), `len`, and `repr` must behave like the underlying sequence.
- **IO**: wraps a zero-argument (possibly impure) callable. `run()` executes it. `map`/`bind`/`amap` must be lazy — they build a new deferred computation and only execute when `run()` is called. `IO(fn)` is the public constructor and exposes `insert`/`apply` from the internal class.
- **Reader / Compose / Pipe**: `Reader` wraps a function of an environment. `Compose` builds a left-to-right feed-forward function via chained `.then(...)`; calling the composed object runs the pipeline. `Pipe` starts from a value, chains `.then(...)`, and yields the result via `flush()` or the unary `+` operator. `Compose` and `Pipe` deliberately DISABLE `apply` and `insert` (the corresponding tests expect these to be unavailable/raising).
- **State**: wraps a state-transition function `s -> (value, new_state)`; `run(state)` executes it; laws hold over threaded state.
- **Writer**: pairs a value with an accumulated monoid log; binding concatenates logs.
- **Promise**: wraps async-style computation; supports `then` with plain and Kleisli functions and a `catch`/error path; `insert` lifts a value into a resolved promise.
- **Monoid**: base class with an addition operation and an identity/zero. A shared `IDENTITY` sentinel must act as the neutral element on both sides (`x + IDENTITY == x == IDENTITY + x`), and `MZero`'s repr must match the asserted form.
- **Operators variants**: each `operators/*.py` re-declares the monad (or mixes in an operator base) so that `map`, `amap`, and `bind` are also reachable through infix operators while preserving identical algebraic behavior to the plain monad.

## Solution decomposition

1. **Fill in the `Monad` base class** (`monad.py`): implement `apply` (the applicative entry point that wraps a function so it can be `amap`-ed), the default `then` dispatch logic, and any shared helpers (`join`, operator hooks). Concrete subclasses rely on these.
2. **Implement `Monoid`** (`monoid.py`): the identity sentinel handling, the combine operation, and `MZero`'s repr, so `List` and `Writer` can build on it.
3. **Implement each concrete monad's four core operations** (`map`, `amap`, `bind`, and the type-specific extractor/constructor), reusing `insert` where already provided. Keep failure short-circuiting consistent.
4. **Implement `then`/`join`/`run`/`flush`** where each type needs a specialized version (List `join`, IO `run`, Pipe `flush`, etc.).
5. **Implement `tools.curry`** and any other helpers, since curried functions underpin many test constructions.
6. **Wire up the operator variants** so their operators route to the underlying `map`/`amap`/`bind`.
7. **Match reprs/equality** exactly to the strings the tests assert.

Recommended order: `monad.py` → `monoid.py` → `maybe.py`/`either.py` (simplest failure-carrying) → `list.py` → `io.py`/`reader.py` → `state.py`/`writer.py`/`promise.py` → operator variants → `tools.py` (may be needed early if tests import it).

## Solution space

- **Short-circuit style**: failure propagation in Either/Maybe can be written with early returns, ternary expressions, or by delegating to `map`/`bind`. Any form that returns the *same* failure object (or an equal one) is acceptable.
- **`then` dispatch**: valid approaches include (a) map-then-attempt-join with an exception guard, (b) inspecting whether the applied result is already a monad instance, or (c) a helper that runs the function and normalizes the result. Both the "try to flatten, fall back to plain map" and the "type-check first" strategies pass.
- **IO laziness**: can be expressed with nested closures, or a small helper that defers execution. The only hard requirement is that no impure work happens until `run()`.
- **List representation**: may subclass `list`, wrap a Python list in `value`, or use a sequence field — as long as indexing/slicing/`len`/`repr`/concatenation behave.
- **Operator variants**: may use a shared mixin providing `__and__`/`__mul__`/`__rshift__`, or redefine operators per class. Either satisfies the operator tests.
- **`curry`**: any correct fixed-arity currying that also lets `curry` itself be partially applied (usable as `@curry(n)` decorator) is fine.
- **Docstrings/comments** are irrelevant to correctness; omit or paraphrase freely.

## Known pitfalls

- **Do not swallow exceptions in Maybe.** Two Maybe tests explicitly assert that exceptions raised inside mapped/bound functions propagate rather than becoming `Nothing`. Wrapping map/bind in a blanket `try/except` that returns `Nothing` will fail them.
- **`then` must catch only the flattening error**, not arbitrary errors from user functions. Catch a narrow set (e.g. the error raised when the result isn't a nested monad) so genuine user exceptions still surface.
- **Applicative short-circuit order**: for Either/Maybe, if the function side is the failure, return that failure; the tests distinguish "failure in first arg" vs "failure in second arg", so check both positions.
- **Compose/Pipe must NOT expose working `apply`/`insert`.** Several tests assert these are disabled; naively inheriting them from `Reader`/`Monad` will make "disabled" tests fail.
- **Reader composition direction**: `Compose`/`Pipe` feed left-to-right (first `.then` runs first). Reversing the order breaks the composition tests.
- **`repr` exactness**: `Left`/`Right`/`Just`/`Nothing`/`Some`/`MZero` and List reprs are asserted as literal strings — match spacing and words precisely.
- **Monoid IDENTITY sentinel**: combining with the shared identity must return the other operand unchanged on both sides; forgetting one side breaks the `*_with_IDENTITY` tests.
- **`insert` neutrality**: e.g. `Either.insert` must be a Right (success) with the correct metadata tuple; an incorrect metadata flag silently makes it a Left and breaks identity laws.
- **Preserve laziness/threading**: IO and State must build new computations rather than executing eagerly, or associativity/right-identity tests observe side effects at the wrong time.
- **Reconstruct with `self.__class__`** (not a hard-coded class) so operator-variant subclasses keep their own type through `map`/`amap`/`bind`.

## Cheat surface

The following would technically flip tests but do NOT constitute a real solution and should be rejected:

- Hard-coding expected return values or reprs to match specific test inputs instead of computing them from `value`/`monoid`.
- Special-casing the exact literals used in tests (e.g. detecting the test's numbers/strings) rather than implementing general `map`/`bind`/`amap`.
- Editing, deleting, weakening, or skipping the tests themselves, or altering the assertions/law checks.
- Catching all exceptions in Maybe to make error tests appear to pass while actually violating the "exceptions propagate" contract (this would fail those tests anyway, but any attempt to game them is disqualifying).
- Making `apply`/`insert` on Compose/Pipe fake-fail by string-matching test names.
- Implementing only the subset of methods each named test touches while leaving the shared law-checking helpers broken for other inputs.

A legitimate solution implements each operation from the underlying `value`/`monoid` data in a way that satisfies the algebraic laws for arbitrary inputs.

## Success criteria

- Every module in the stub list imports cleanly (no `pass`-only bodies left that break attribute access), and `import pymonad.tools` succeeds.
- All listed `fail_to_pass` tests pass, covering: functor identity/composition, applicative associativity/homomorphism/agreement-with-map, monad left-identity/right-identity/associativity, `then` with both plain and Kleisli functions, `insert`, extraction methods (`either`, `maybe`/`option`, `is_left`/`is_right`/`is_just`/`is_nothing`), List indexing/slicing/len/repr and its monoid laws, IO/Reader/State/Writer/Promise behavior, Compose/Pipe composition with `apply`/`insert` disabled, Promise `catch`, and the operator-variant functor/applicative/monad tests.
- The monoid `IDENTITY`/`MZero` identity and repr tests pass.
- No previously passing behavior regresses; the algebraic laws hold for the general (not just tested-literal) case.