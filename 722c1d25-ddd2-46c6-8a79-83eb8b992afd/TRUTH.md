# TRUTH.md

## Problem

The repository `Zahgon/rust-signals` is a re-implementation of the well-known `futures-signals` crate. Every non-trivial function body across the crate's core modules has been replaced with a `panic!("STUB: not implemented")` placeholder (or an empty/todo body). The task is to restore correct, working implementations of every stubbed item so that the reactive-programming primitives — `Signal`, `SignalVec`, `SignalMap`, `Mutable`, `MutableVec`, `MutableBTreeMap`, `Broadcaster`, channels, cancelable futures, and the `map_ref!`/`map_mut!` macros — behave according to the crate's public contract.

The stubbed files are:
- `src/atomic.rs` — a null-pointer-optimized `AtomicOption<A>`.
- `src/future.rs` — `cancelable_future` and its handle/future types.
- `src/internal.rs` — internal `map_ref` machinery (`MapRef1`, `MapRefSignal`, `PollResult`, unwrap helpers).
- `src/lib.rs` — `block_on`/`spawn`-style test helpers and re-exports (mostly docs, plus a few utility fns).
- `src/signal/broadcaster.rs` — fan-out of one signal to many consumers.
- `src/signal/channel.rs` — `channel`/`Sender`/`Receiver` signal channel.
- `src/signal/macros.rs` — `map_ref!` / `map_mut!` declarative macros.
- `src/signal/mutable.rs` — `Mutable`, `MutableSignal`, `MutableSignalRef`, `MutableSignalCloned`, lock guards.
- `src/signal/signal.rs` — the `Signal` trait, `SignalExt` combinators, and all combinator adapters.
- `src/signal_map.rs` — `SignalMap` trait, `MutableBTreeMap`, `MapDiff`, and map combinators.
- `src/signal_vec.rs` — `SignalVec` trait, `MutableVec`, `VecDiff`, and vec combinators.

Success is defined by the enumerated `fail_to_pass` tests flipping to green while the crate continues to compile under its strict lint settings (`#![deny(warnings, ...)]`).

## Behavioral contract

The implementation must satisfy the observable semantics of the `futures-signals` reactive model. The key invariants:

**Poll semantics (the heart of everything).**
- A `Signal` is polled via `poll_change(Pin<&mut Self>, cx) -> Poll<Option<Item>>`. `Poll::Ready(Some(v))` means "the value changed to `v`" (also delivers the initial value on first poll); `Poll::Ready(None)` means the signal has terminated permanently; `Poll::Pending` means "no change yet, the waker was registered."
- A `SignalVec` is polled via `poll_vec_change -> Poll<Option<VecDiff<Item>>>`, and `SignalMap` via `poll_map_change -> Poll<Option<MapDiff<Key, Value>>>`. Each yields a stream of *diffs* describing incremental changes, not full snapshots.
- After a signal/stream returns `Ready(None)`, it must never be polled again by well-behaved consumers, and adapters that hold it should drop it and continue reporting done.
- Whenever a poll returns `Pending`, the current `cx.waker()` must have been arranged to be woken when new data is available. Whenever a poll returns `Ready(Some)`, the consumer is responsible for polling again; adapters must not "lose" a pending downstream item.

**`AtomicOption<A>`** must behave exactly like an atomic `Option<A>` but represent `None` as a null pointer (no boxing for `None`; box the value for `Some`). `new`, `swap`, `store`, `take`, and `Drop` must never leak or double-free, and must correctly reconstruct/free boxes created via `Box::into_raw`.

**`cancelable_future`** returns a `(DiscardOnDrop<CancelableFutureHandle>, CancelableFuture)` pair. Polling the future drives the inner future to completion, *unless* the handle is discarded (or dropped): once cancelled, the future must stop driving the inner future and instead complete by invoking the supplied `when_cancelled` callback exactly once, yielding its return value as the future's output. Cancellation must wake a currently-parked future so it observes the cancellation promptly.

**`Mutable`** is an `Arc + RwLock`-like cell that additionally supports change notification. `lock_ref`/`lock_mut` give read/write guards; mutating through a write guard (or `set`/`replace`/`set_if`/`set_neq`) must mark the value changed and wake all registered signal wakers. `signal()`, `signal_ref()`, and `signal_cloned()` produce signals that first deliver the current value, then deliver subsequent changes. When the last `Mutable` is dropped, its derived signals terminate (`Ready(None)`) after delivering any final value.

**`Broadcaster`** wraps one upstream signal and lets many independent signals observe the same value stream; each derived signal must independently receive the current value on first poll and every subsequent change, and be individually wakeable.

**`channel`** creates a `Sender`/`Receiver` pair where the `Receiver` is a `Signal` delivering the latest sent value (coalescing) and terminating when the `Sender` is dropped.

**`map_ref!` / `map_mut!` macros** combine N signals into one signal whose item is computed from the current values of all inputs by reference (`map_ref`) or mutable reference (`map_mut`). The combined signal yields a new value whenever *any* input changes, using the most recent values of the others, and terminates only when *all* inputs have terminated. The macros must support: single or multiple inputs, `let`-bindings for renaming inputs, pattern bindings, `move`/non-`move` closures, `.clone()` on inputs, and must produce `Send`/`Sync` results where inputs are.

**Combinators** (`map`, `map_future`, `eq`/`neq`, `dedupe`, `filter`/`filter_map`, `flatten`, `switch`, `switch_signal_vec`, `throttle`, `stop_if`, `to_stream`/`from_stream`, `sample`, `for_each`, etc.) each have precise diff/value semantics — see the `futures-signals` documentation for each — that the tests pin down.

## Solution decomposition

A correct solution can be built bottom-up, since higher layers depend on lower ones:

1. **`atomic.rs`** — Implement `AtomicOption` first (no dependencies). Convert `Option<A>` ↔ raw pointer (`Some` → boxed pointer, `None` → null); `swap` atomically exchanges pointers and reconstructs the old `Option`; `store`/`take` are expressed via `swap`; `Drop` frees any non-null pointer.

2. **`internal.rs`** — Implement `PollResult::merge` (done = AND of dones, changed = OR of changes), the `unwrap_ref`/`unwrap_mut` helpers (unreachable on `None`), and `MapRef1` (holds an optional signal + cached optional value; `poll` advances the inner signal and updates the cache, reporting changed/done; `value_ref`/`value_mut` expose the cache) and `MapRefSignal` (a signal built from a poll-closure). This is the runtime backbone the macros expand into.

3. **`future.rs`** — Implement the cancellation state machine (an `AtomicBool` cancel flag + a `Mutex<Option<Waker>>`), the handle's `Discard` impl (set flag, take & wake the stored waker), the future's `poll` (on cancel: drop inner future, run callback once → `Ready`; otherwise poll inner, on `Pending` store the waker), and the `cancelable_future` constructor wiring them together with `Arc`/`Weak`.

4. **`signal/signal.rs`** — Define the `Signal` trait and the large `SignalExt` combinator set with their adapter structs. Each adapter is a `pin_project`ed struct implementing `Signal` (or `Stream`) with the correct poll logic.

5. **`signal/mutable.rs`, `broadcaster.rs`, `channel.rs`** — Shared-state primitives built on `Arc<...>` with a set/collection of registered wakers; producing signals that read current state then await notification.

6. **`signal/macros.rs`** — The `map_ref!`/`map_mut!` recursive macro expansions that build a `MapRefSignal` closure over several `MapRef1` wrappers, merging their `PollResult`s and computing the output only when something changed and not-all-done.

7. **`signal_vec.rs` / `signal_map.rs`** — The `SignalVec`/`SignalMap` traits, the `VecDiff`/`MapDiff` enums, `MutableVec`/`MutableBTreeMap`, and their combinators (map, filter, flatten, `to_signal_*`, `sum`, `len`, `is_empty`, sorting/chain adapters, `switch_signal_vec`, etc.).

8. **`lib.rs`** — Re-exports and the small test-support utilities (e.g. a blocking executor helper for `block_on`-style tests, iteration helpers) plus module docs. Keep it warning-clean.

## Solution space

- **Reuse vs. re-derive:** The canonical reference is the published `futures-signals` crate at the matching version. A valid solution may mirror that crate's internal design closely, or take a different but behaviorally-equivalent internal representation (e.g. different waker-storage strategy in `Mutable`, `parking_lot` vs `std` mutexes, `Vec<Waker>` vs a slab). Only observable behavior is constrained.
- **`AtomicOption`:** The null-pointer optimization is required by the module's contract, but any implementation that (a) never leaks/double-frees and (b) presents correct `Option` values is acceptable. A generic `Atomic<A>` helper is optional (the reference leaves it commented out).
- **`cancelable_future`:** May be implemented from scratch (as here) or delegated to `futures_util::future::abortable`-style machinery, as long as the discard/cancel/callback-once semantics hold. The exact eagerness of cancellation (immediate vs. on next poll) is flexible provided the cancelled future eventually returns the callback result and stops driving the inner future.
- **Macros:** Any macro expansion that yields the correct combined-signal semantics and supports all the tested forms (idents, lets, patterns, move/no-move, clone, N-ary) is valid; the recursion shape is an implementation detail.
- **Combinators:** Each combinator's adapter can store state differently, but must match the documented diff semantics (see the test names, which map one-to-one onto specific combinators).
- **Wakers:** Storing a single waker vs. a list, and using `AtomicWaker` vs a mutex, are all acceptable as long as no wakeups are lost.

## Known pitfalls

- **Lost wakeups.** The most common failure: returning `Pending` without registering `cx.waker()`, or replacing a stored waker without ensuring the new context gets woken. Every `Pending` path must guarantee a future wake.
- **Polling after completion.** Continuing to poll an inner signal/future after it returned `Ready(None)` (or after cancellation) can panic (`unwrap` on `None`) or violate `Pin` guarantees. Adapters must `set(None)`/drop the inner and short-circuit to done.
- **Double-free / leak in `AtomicOption`.** Forgetting the null check in `Drop`, or reconstructing a `Box` from a null pointer, is UB. Only `from_ptr`/`Drop` non-null pointers, and only pointers created by `Box::into_raw`.
- **Cancellation ordering.** In `CancelableFuture::poll`, the cancel branch must drop the inner future *before* running the callback so the inner future can never later call `waker.wake()`, and the callback must run exactly once (take it out of its `Option`).
- **`map_ref`/`map_mut` "changed" logic.** The combined signal must yield only when at least one input changed, must reuse cached values of unchanged inputs, and must report `Ready(None)` only when *every* input is done — not on the first input's completion. Getting the AND/OR merge (done = AND, changed = OR) backwards breaks many `map_ref`/`map_mut` tests.
- **Initial value delivery.** `Mutable` signals, broadcaster signals, and channel receivers must deliver the *current* value on the first poll, not wait for the next change.
- **`VecDiff`/`MapDiff` correctness.** Vec/map combinators must translate upstream diffs into the correct downstream diffs (e.g. filtering must remap indices; flatten/switch must splice sub-streams; `drain`/`swap`/`truncate`/`reverse`/`move_from_to` must preserve ordering). Off-by-one index errors here fail the many `signal_vec` tests, including the panic-path tests (`test_drain_panic_*`).
- **Strict lints.** The crate denies warnings; unused imports, dead code, or missing `Debug` impls will fail the build and therefore every test. Keep the tree warning-clean.
- **`Pin` discipline.** Use `pin_project` projections correctly; never move pinned inner futures/signals; `unsafe_pin`-style helpers must only be used where the Pin contract is actually upheld.
- **Coalescing vs. queuing.** `Mutable` and `channel` coalesce to the latest value (intermediate values may be skipped), whereas `SignalVec`/`SignalMap` must not lose diffs — they must buffer and deliver every diff in order.

## Cheat surface

The following would make tests pass without genuinely implementing the contract and must be treated as invalid:

- **Hardcoding to tests.** Detecting specific test inputs/sizes and returning canned diffs or values, or special-casing the literal values used in `signal_vec`/`signal_map` tests.
- **Weakening tests.** Editing, deleting, `#[ignore]`-ing, or gating any of the `fail_to_pass` tests, or altering their assertions/expected outputs.
- **Faking async.** Making `poll_change` always return `Ready` (busy-loop that "works" only under the test executor), or spinning instead of registering wakers — any solution that only passes because the test executor polls repeatedly rather than because wakeups are correct.
- **Suppressing lints instead of fixing.** Blanket `#![allow(warnings)]` / `#[allow(dead_code)]` sprinkling to hide unfinished stubs, or leaving `panic!("STUB")`/`todo!()` on code paths the tests happen not to hit.
- **Leaking to avoid `Drop` correctness.** Using `mem::forget`/`Box::leak` in `AtomicOption` or elsewhere to dodge the double-free problem while "passing" — this violates the no-leak contract even if tests don't directly assert it.
- **Reintroducing removed artifacts** (e.g. the deleted spec archive) to satisfy anything.
- **Copying the reference diff verbatim** as a substitute for understanding — irrelevant to grading correctness, but note the spec describes the destination, not a required route.

## Success criteria

- The crate compiles cleanly under its declared lint configuration (`#![deny(warnings, missing_debug_implementations, macro_use_extern_crate)]`) with no remaining `panic!("STUB")`/`todo!` bodies on reachable paths.
- All listed `fail_to_pass` tests pass, covering: cancelable futures (`test_cancelable_future`), atomic/poll internals (`test_polls`), broadcaster suite (`test_broadcaster*`), channel/stream helpers (`test_block_on_stream*`, `test_from_stream`), the full `map_ref::*` and `map_mut::*` macro matrices (idents, lets, patterns, move/no-move, clone, send_sync), all `signal::*` combinator tests (`always`, `eq`/`neq`, `map`, `map_future`, `mutable*`, `option`, `result`, `stop_if`, `switch_signal_vec*`, `throttle*`, `sample_stream_cloned`), the `signal_map` suite (mutable BTreeMap ops, `to_signal_map`/`to_signal_cloned`, `map_value*`, key-existence tests), and the `signal_vec` suite (mutable Vec ops, diffs, `flatten`, `filter*`, `sum`/`len`/`is_empty`, chain/reverse/ord/drain/panic-path tests, `debug_*`).
- No previously-passing behavior regresses (the `pass_to_pass` set is empty, but the build and any existing doctests/examples must remain green).
- The implementation is generic and contract-driven — it works for arbitrary inputs of the appropriate types, not just the specific values exercised by the tests.