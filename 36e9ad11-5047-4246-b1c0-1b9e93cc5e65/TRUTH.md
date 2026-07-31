# TRUTH.md

## Problem

The repository `Zahgon/transitions` is a Python finite-state-machine library whose core and extension modules have been reduced to stubs. Every stubbed method body (typically `pass` or a placeholder) must be restored to a fully working implementation so that the library behaves as a complete state machine framework again.

The affected surface spans:

- **`transitions/core.py`** — the foundational engine: `State`, `Condition`, `Transition`, `EventData`, `Event`, and `Machine`.
- **`transitions/extensions/`** — layered feature sets built on the core:
  - `nesting.py` (hierarchical/nested states),
  - `locking.py` (thread-safe machine),
  - `asyncio.py` (async/await-driven machine and events),
  - `states.py` (timeout, tags, volatile, error states, etc.),
  - `markup.py` (serialize a machine to a dict/markup),
  - `factory.py` (assemble concrete machine classes from mixins),
  - `diagrams*.py` (graph rendering backends: graphviz, pygraphviz, mermaid, plus shared base),
  - `experimental/utils.py` (decorator/type-hint helpers).

The `fail_to_pass` set is dominated by `tests/test_async.py` (sync `TestTransitions`, `TestAsync`, `TestAsyncGraphMachine`) and `tests/test_add_remove.py`, but the intent is that the *entire* existing test suite of the library passes. Because the async and graph test classes subclass and re-run the synchronous behavioral tests, correctness of `core.py` is a prerequisite for almost everything.

The goal is to reproduce the documented, historically-known behavior of the `transitions` library — not to invent new semantics.

## Behavioral contract

The observable behavior the implementation must satisfy:

### State
- `name` property: for a plain string state returns the string; for an `Enum` state returns the enum member's `.name`.
- `value` property: returns the underlying stored name object (the string, or the enum member itself for enum states).
- `enter(event_data)` / `exit(event_data)`: run the state's `on_enter` / `on_exit` callback lists through the machine's callback dispatcher; emit log output but no return value contract.

### Condition
- `check(event_data)`: resolves `self.func` against the model via the machine's callable resolver, invokes it (passing the `EventData` when `send_event` is enabled, otherwise the unpacked args/kwargs), and returns whether the boolean result equals `self.target`.

### Transition
- `execute(event_data)`: run `prepare` callbacks, evaluate all conditions (short-circuit to `False` if any fails), then run `before_state_change` + transition `before` callbacks, perform the state change **only if `dest` is not `None`** (a `None` dest = internal transition with no state change), then run transition `after` + machine `after_state_change`. Returns `True` on success, `False` if conditions blocked it.
- `_change_state(event_data)`: exit the source state, set the model's new state, refresh the `EventData.state`, enter the destination state, and if the destination is a *final* state, fire the machine's `on_final` callbacks.
- `_eval_conditions`: returns `True` only if every condition passes.

### Event
- `trigger(model, *args, **kwargs)`: builds an `EventData`, wraps `_trigger` in a partial, and hands it to `Machine._process` (which decides queued vs. immediate execution). Returns the transition success boolean.
- `_trigger(event_data)`: resolves the model's current state; if the state is a valid source, processes the transitions. Any exception during processing routes to `on_exception` callbacks if configured, otherwise re-raises. `finalize_event` callbacks always run (in a `finally`), and exceptions inside finalize are logged, not propagated. Returns `event_data.result`.
- `_process`: run machine `prepare_event` callbacks, iterate the transitions registered for the current state name, execute each until one returns `True`, then set `result = True` and stop.
- `_is_valid_source`: if the current state has no transitions for this event, either warn and return `False` (when invalid triggers are ignored, honoring per-state override then machine default) or raise `MachineError`; otherwise return `True`.

### Machine
- Manage the collection of states, events, and models. When constructed without an explicit model it acts as its own model.
- Provide `resolve_callable`, `callbacks` (dispatch a list of callbacks), `get_state`, `set_state`, `get_model_state`, state/transition/trigger addition and removal, auto-transition generation (`to_<state>`), ordered transitions, `may_<trigger>` guard methods, model addition/removal with attribute decoration, and `_process` (immediate vs. queued execution).
- Adding/removing models must not leak references — removed models must be garbage-collectable (weak references where appropriate).
- Initial-state handling: models added with or without an explicit initial state must land in a consistent, well-defined state.

### Extensions
- **nesting**: nested/parallel states, dotted state names, hierarchical enter/exit, `NestedState`/`NestedEvent`/`HierarchicalMachine` semantics, `may_` and auto-transitions across nesting.
- **locking**: wrap machine operations with a reentrant context manager so triggers are thread-safe; preserve full core behavior otherwise.
- **asyncio**: async variants of `Event`, `Transition`, `State`, and `Machine` where callbacks/conditions may be coroutines; support cancellation, timeouts, per-model queued processing, task cleanup, and exception/finalize routing mirroring the sync contract. All synchronous behavioral tests re-executed against the async machine (awaited) must pass identically.
- **states**: mixins like `Timeout`, `Tags`, `Volatile`, `Error`, `Retry` adding their documented per-state features.
- **markup**: `MarkupMachine` serializes states/transitions/models to a dict, with optional inclusion of auto-transitions and reference vs. name forms of callbacks.
- **factory**: compose the concrete product classes (locked, nested, async, graph, and their combinations) from the mixins and expose them via a lookup table.
- **diagrams**: `GraphMachine` and backend adapters must build a graph model of the machine and render/roll up nested graphs; `TestAsyncGraphMachine` requires the graph machine to also satisfy all behavioral tests.
- **experimental/utils**: decorator helpers (e.g., adding transitions/state config via type hints or decorators) used by experimental tests.

## Solution decomposition

Sub-goals, roughly in dependency order:

1. **Core engine first.** Implement `State`, `Condition`, `Transition`, `EventData`, `Event`, `Machine` in `core.py`. Everything else depends on this. Without correct `execute`/`_trigger`/`_process`/`callbacks`/`resolve_callable`, no test passes.
2. **Callback dispatch semantics.** Ensure `callbacks` iterates and invokes each resolved callback, and that `resolve_callable` correctly binds string names to model/machine methods and passes `EventData` vs. unpacked args based on `send_event`.
3. **State change ordering.** Exit → set state → update event data → enter → final check. Getting the order or the `dest is None` internal-transition case wrong breaks internal-transition and on_final tests.
4. **Error/finalize flow.** Correct `try/except/finally` structure in `_trigger` so `on_exception` and `finalize_event` behave per contract.
5. **Model lifecycle & GC.** `add_model` / `remove_model` decoration and weak-reference handling so garbage-collection tests pass.
6. **Extensions layered on core.** Implement nesting, locking, states, markup, then factory (which wires them), then diagrams, then asyncio. asyncio and diagrams both re-run the whole behavioral test battery.
7. **Async parity.** Mirror the sync control flow but with `await` on coroutine callbacks/conditions and proper task/queue/timeout management.
8. **Diagram backends.** Build graph representations without breaking machine behavior; the async-graph combination must still pass all behavioral tests.

## Solution space

Valid alternative routes that should NOT be penalized:

- **Log messages**: exact wording, log level, and whether logging happens at all is not behaviorally asserted (except where a test specifically captures logs). Any reasonable/absent logging is acceptable.
- **Docstrings and comments**: presence, absence, or wording is irrelevant to correctness.
- **Control-flow shape**: e.g., using explicit loops vs. `all()`/generator expressions for condition evaluation; using `itertools.chain` vs. list concatenation for combining callback lists; early-return vs. flag variables — all acceptable if the resulting order and short-circuit behavior match.
- **Weak-reference strategy**: any mechanism (weakref proxies, weakref sets, explicit cleanup) that lets removed models be collected and keeps `weakproxy_model` working is fine.
- **Queued processing**: implementing the queue as a list, deque, or per-model queue is acceptable provided ordering and re-entrancy semantics match.
- **Async implementation details**: how coroutine-vs-function detection, task tracking, cancellation, and timeouts are realized may differ, as long as the observable async test behavior (ordering, cancellation, timeout, cleanup) holds.
- **Factory wiring**: the exact structure of the class-lookup table may vary as long as the correct combined product classes are produced for each feature combination.
- **Diagram internals**: node/edge construction details and styling may differ; only the machine-behavior tests and any explicit graph-structure assertions constrain it.
- **Helper factoring**: introducing private helpers or inlining is a free choice.

The golden diff is one route; any implementation producing the same externally observable state-machine semantics is correct.

## Known pitfalls

- **Internal transitions (`dest is None`)**: forgetting to skip the state change when `dest` is `None` will corrupt internal-transition tests and may raise on `get_state(None)`.
- **Condition target polarity**: `unless` conditions use `target=False`; comparing the predicate result to `self.target` (not just truthiness) is essential.
- **`send_event` branching**: conditions and callbacks must pass the `EventData` object when `send_event` is on, and unpacked `*args, **kwargs` when off. Mixing these breaks the send-event test families.
- **EventData refresh after state change**: after `set_state`, the `EventData.state` must be updated to the new state before entering it, otherwise `on_final` and enter-callback logic read the stale state.
- **Finalize must always run**: `finalize_event` callbacks belong in a `finally` and must not mask the original result/exception; exceptions raised *inside* finalize must be swallowed (logged), not propagated.
- **on_exception vs. re-raise**: only route to `on_exception` when it is configured; otherwise the exception must propagate (tests assert both paths).
- **Short-circuit in `_process`**: stop at the first successful transition; running further transitions changes state incorrectly.
- **Model GC leaks**: strong references held in machine internals prevent collection — the garbage-collection and remove-model tests will fail if models are retained.
- **Auto-transition and `may_` generation**: these must respect `auto_transitions` and correctly report feasibility (including exceptions/invalid-state cases in `may_transition_with_*`).
- **Async parity is not optional**: `TestAsync` and `TestAsyncGraphMachine` re-run the *sync* behavioral tests against async machines; a core detail that only "mostly" works will fail dozens of async tests.
- **Layer ordering / MRO**: extensions mix into core; factory must combine mixins so that overridden methods (nested, locked, async, graph) chain correctly.
- **Enum states**: `name` vs. `value` handling for enum members differs from strings; both must be honored.

## Cheat surface

Ways a solution could appear to pass without genuinely implementing the library — these should be treated as failures:

- **Hard-coding test expectations**: special-casing specific state names, trigger names, or model classes used in the tests instead of implementing general logic.
- **Skipping/deselecting tests**: modifying test files, adding `skip`/`xfail` markers, editing `conftest.py`, or changing pytest configuration to avoid running the required tests.
- **Weakening assertions elsewhere**: altering shared test helpers so behavioral checks become vacuous.
- **Stubbing extensions to delegate to trivial no-ops** that happen to satisfy only the listed tests but break the general contract (e.g., an async machine that ignores coroutine callbacks, or a graph machine that silently drops graph construction while claiming success).
- **Catch-all exception suppression** to make error/finalize tests pass by hiding failures rather than routing them correctly.
- **Returning constant `True`/`False`** from `execute`/`check`/`_is_valid_source` to satisfy a subset of assertions without honoring conditions and validity rules.
- **Re-adding or depending on the deleted `spec.pdf.bz2`** or any external artifact instead of implementing behavior.

## Success criteria

- All tests in the `fail_to_pass` list — every case in `tests/test_add_remove.py::TestTransitionsAddRemove` named above and every listed case across `tests/test_async.py`'s `TestTransitions`, `TestAsync`, and `TestAsyncGraphMachine` classes — pass.
- The broader existing test suite of the library (core, nesting, locking, states, markup, diagrams, experimental) continues to pass, since the fixes to `core.py` and the extensions are shared foundations; no previously-passing behavior regresses.
- No test files, fixtures, or pytest configuration are modified to force passes.
- The implemented behavior generalizes: state entry/exit ordering, condition polarity, send-event dispatch, internal transitions, error/finalize routing, queued and async processing, model lifecycle/GC, auto-transitions, `may_` guards, and (for graph/async variants) full behavioral parity all hold for arbitrary inputs, not just the test cases.
- Removed models are garbage-collectable; weakproxy models work; no reference leaks.