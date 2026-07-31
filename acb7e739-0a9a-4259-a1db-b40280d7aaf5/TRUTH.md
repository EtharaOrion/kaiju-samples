# TRUTH.md

## Problem

The `nexosim` crate (a Rust discrete-event simulation framework) has had the body of essentially every function, method, and trait implementation across ~75 source files replaced with `panic!("STUB: not implemented")` (and in some cases `#[allow(unreachable_code)] loop {}` placeholders after the panic to satisfy return types). The public and internal type definitions, struct/enum layouts, trait signatures, module structure, doc-comments, and imports remain intact; only the *implementations* are missing.

The task is to restore correct, working implementations of every stubbed body so that the crate compiles and the full test suite (unit tests inside `nexosim/src/**` plus integration tests such as `injector`, `model_scheduling`, `serialization`, `simulation_*`) passes. This spans the whole engine:

- **Low-level concurrency utilities**: MPSC recyclable-box queue, single-slot SPSC value passing (`slot`, `shared_cell`, `sync_cell`), scoped thread-locals, bit-scanning, RNG, priority queues (plain and indexed), cached RW-lock, sequential futures, serialization helpers.
- **Task/executor layer**: a custom async task (`task.rs`, `cancel_token`, `promise`, `runnable`, `util`), single-threaded and work-stealing multi-threaded executors with an injector and pool manager.
- **Model/port layer**: models, contexts, input/output ports, broadcasters and senders (both for output ports and for external sources), event/query sinks, event slots/queues.
- **Simulation layer**: mailbox, scheduler, injector, queue items, sim init, the `Simulation` driver, time (monotonic time, clocks, ticker), tracing.
- **Server / gRPC layer**: registries, services (bench/build/controller/monitor/scheduler), run loop, generated protobuf code, key registry.

Because all of these interoperate, a correct solution must make them mutually consistent — a partial implementation that leaves any `panic!("STUB…")` reachable on a tested path will fail.

## Behavioral contract

A correct solution must satisfy, at minimum, the following observable behaviors:

- **No reachable stub panics.** Every code path exercised by the listed `fail_to_pass` tests must run real logic instead of `panic!("STUB: not implemented")`. Placeholder `loop {}` tails must be removed.
- **Constructors build valid state.** `new`-style constructors (`Inner::new`, `Receiver::new`, `Queue::new`, RNG/seeded constructors, priority-queue constructors, executor constructors, etc.) must fully initialize their fields (queues, wakers, signalling primitives, buffers, capacities, generation counters) rather than panicking.
- **Channel/queue semantics (MPSC):**
  - `Queue::new(capacity)` allocates a ring buffer; capacity 0 or `> usize::MAX/2 + 1` must be rejected (panic in constructor is acceptable and expected by contract, but the *tested* capacities 1/2/3 must work).
  - `push` returns `Ok` when a slot is free, `Err(Full(msg))` (returning the item so the caller can retry) when full, and `Err(Closed)` when closed. `pop` returns `Ok(msg)`, `Err(Empty)`, or `Err(Closed)`.
  - `len()` reports the number of queued items; `close()`/`is_closed()` behave idempotently.
  - Borrowed messages (`MessageBorrow`) free their slot and re-arm the stamp on `Drop`, recycling the box back into the slot so producers can reuse the allocation. `Deref`/`DerefMut` expose the message.
  - Tests `queue_spsc_*`, `queue_mpsc_*`, `queue_len`, `queue_closed_by_consumer`, `queue_closed_by_sender` pin these semantics (including closing from either side and observing the right error/loss behavior).
- **Sender/Receiver async protocol:** sending waits on the sender signal until a slot frees or the channel closes; receiving waits on the receiver waker until a message arrives or the channel closes. A per-thread in-flight message counter (`THREAD_MSG_COUNT`) is incremented on successful send and decremented on receive; this is used to detect deadlock (all-in-flight-consumed) at step boundaries. Dropping the `Receiver` closes the queue and wakes all blocked senders. `channel_id`/`channel_id()` must yield a stable, unique-per-live-channel identifier derived from the shared allocation address.
- **Single-slot passing (`slot`, `shared_cell`):** a writer can deposit a value once; a reader can `read`/`try_read` it; dropping either side is observable to the other. Multi-threaded variants must be race-free (no data loss, no double free), matching `slot_*` and `shared_cell_*` tests.
- **Scoped thread-local (`scoped_thread_local`):** `set` installs a value for the duration of a closure and restores the previous binding afterward, **even if the closure panics** (`scoped_local_key_panic_resets`). Accessing while unset must error/panic per the API (`scoped_local_key_unset`), and `is_set`/`with` behave accordingly.
- **Async task engine:** tasks support scheduling, waking (including `will_wake`, multiple wakes coalescing, wake-and-forget), cancellation in every lifecycle state (unscheduled/scheduled/completed), and correct drop behavior for runnables, promises, and reference cycles — single- and multi-threaded (`_mt`) variants included. Promises resolve to the task output; cancellation makes the promise observe cancellation.
- **Executors:** both single-threaded and multi-threaded executors run submitted futures to completion and correctly drop cyclic task graphs without leaking or aborting (`executor_drop_cycle_st/_mt`). The multi-threaded executor's injector and pool manager must balance/steal work and terminate cleanly.
- **Broadcasters/senders (output ports and sources):** broadcasting an event delivers to all connected inputs; broadcasting a query gathers all replies; `filter_map`-style connections drop/transform items correctly (`broadcast_event_*`, `broadcast_query_*`, `*_filter_map`). Empty broadcasts complete trivially.
- **Event sinks/slots/registries:** `EventSlot` holds the latest value with correct single- and multi-threaded read/drop semantics; the event-sink registry supports add-and-take (`add_and_take`).
- **Priority queues:** the plain `priority_queue` and `indexed_priority_queue` maintain heap order under insert/extract, handle equal keys deterministically, support removal/update by index with validity checks (`extract_valid`/`extract_invalid`), and survive fuzz/interleaved sequences.
- **RNG:** `gen_bounded` produces a (approximately) uniform distribution passing a chi-squared test (`rng_gen_bounded_chi2`); the generator is seedable and deterministic.
- **Bit utility:** `find_bit` locates the correct bit position across fuzzed inputs (`find_bit_fuzz`).
- **Time & clocks:** `MonotonicTime` arithmetic; a system clock that synchronizes wall-clock to simulation time (`smoke_system_clock`); clock readers usable across threads (`clock_reader_st/_mt`); a `Ticker` that advances simulation time in fixed ticks, handling sub-tick increments, exact ticks, steps larger than one tick, references in the past, and very large steps.
- **Serialization:** queue items serialize with an auto-generated key (`serialize_auto_key`); model serialization round-trips across the `serialization::*` integration tests (init, output, schedule, key, hashmap, generics, generic env, relative order).
- **Full simulation behaviors** (integration tests): event/model/global injectors deliver events and queries in tick and tickless modes, single- and multi-threaded; model self-scheduling (one-shot, periodic, keyed, cancellation, same-time keyed) works; clock synchronization respects tolerance (including zero tolerance); deadlock detection fires on mailbox overflow and query loopbacks (direct, multiple, transitive); halt/resume, message loss, missing-recipient errors, model panics, timeouts (triggered/untriggered), and ticked-mode scheduling/halting all behave as their tests assert.

## Solution decomposition

Because everything is interdependent, implement bottom-up so each layer is testable before the next depends on it:

1. **`loom_exports` / primitives.** Restore the thin re-export shims (atomics, `UnsafeCell`, asserts, sync primitives) so lower layers compile under both normal and `loom` builds. These bodies are mostly trivial forwarding.
2. **Pure utilities.** `util/bit.rs`, `util/rng.rs`, `util/priority_queue.rs`, `util/indexed_priority_queue.rs`, `util/traits.rs`, `util/unwrap_or_throw.rs`, `util/serialization.rs`. Each is self-contained and has dedicated unit tests — do these first and confirm green.
3. **Concurrency utilities.** `util/slot.rs`, `util/shared_cell.rs`, `util/sync_cell.rs`, `util/cached_rw_lock.rs`, `util/seq_futures.rs`, `util/task_set.rs`, `macros/scoped_thread_local.rs`. Get the `slot_*`, `shared_cell_*`, `scoped_local_key_*` tests green.
4. **Channel.** `channel/queue.rs` (ring buffer, stamps, recyclable boxes, borrow drop), then `channel.rs` (Inner, Sender/Receiver/Observer, async send/recv, close semantics, `THREAD_MSG_COUNT`). Confirm `channel::queue::tests::*`.
5. **Task & executor.** `executor/task/*` (cancel token, promise, runnable, util, task core), then `st_executor.rs`, `mt_executor.rs` + `injector.rs` + `pool_manager.rs`, then `executor.rs`. Confirm `executor::task::tests::*` and `executor::tests::*`.
6. **Model & ports.** `model.rs`, `model/context.rs`, `ports/input/*`, `ports/output/*` (broadcaster, sender), `ports/sink/*`, `ports/source/*`. Confirm broadcaster and event-slot tests.
7. **Time.** `time/monotonic_time.rs`, `time/clock.rs`, `time/ticker.rs`, `time.rs`. Confirm time tests.
8. **Simulation core.** `simulation/mailbox.rs`, `simulation/scheduler.rs`, `simulation/injector.rs`, `simulation/queue_items.rs`, `simulation/sim_init.rs`, `simulation.rs`, plus `endpoints/*`, `path.rs`, `tracing.rs`, `dev_hooks.rs`. This unlocks the big integration tests.
9. **Server layer.** `server/*` (registries, services, run, codegen, key_registry). Required for the crate to compile even though few tests target it directly; keep behavior faithful to the trait/service signatures.
10. **`lib.rs`.** Restore any glue (re-exports, top-level free functions) so the public API matches.

At each step, run the corresponding unit tests before moving up.

## Solution space

- **Multiple valid implementations exist.** The golden diff is one route; any implementation that satisfies the behavioral contract and passes the tests is acceptable. In particular:
  - The MPSC queue may use different stamp/index encodings, a different power-of-two vs. exact-capacity strategy, or a different box-recycling scheme, as long as `push`/`pop`/`len`/`close` semantics and the `Full(msg)` retry contract hold.
  - Channel identifiers may be derived from any stable, collision-free-per-live-instance source (e.g. pointer address of the shared allocation); tests only require stability and uniqueness among simultaneously-live channels.
  - Signalling can use the provided `async_event::Event` / `diatomic_waker` primitives or an equivalent notification mechanism, provided wakeups are not lost and closing wakes all waiters.
  - RNG may be any generator whose bounded output passes the chi-squared uniformity test; the exact algorithm is unconstrained.
  - Priority queues may be array-based binary heaps or another structure, as long as ordering, equal-key handling, and index validity semantics match.
  - The executor may use different work-stealing/backoff strategies as long as futures run to completion, cyclic drops are safe, and shutdown is clean.
- **What is NOT free:** field layouts, trait method signatures, module paths, and public type names are fixed by the surrounding (non-stubbed) code and by tests — you must conform to them. `Drop` implementations that close channels / notify waiters are semantically required, not optional stylistic choices.

## Known pitfalls

- **Leaving any stub reachable.** A single un-implemented body on a tested path (e.g. a `Debug` impl, a `Display` impl, or a rarely-called helper) will panic the test. All `panic!("STUB…")` and trailing `loop {}` placeholders must be replaced.
- **Panic-safety of scoped thread-locals.** The previous binding MUST be restored even when the guarded closure panics (guard/`Drop`-based restoration), or `scoped_local_key_panic_resets` fails.
- **Lost wakeups / missed close notifications.** On `close` and on `Receiver`/`Sender` drop you must notify *all* blocked senders (and the receiver). Failing to wake waiters causes hangs (test timeouts), and forgetting to close on drop causes deadlock-detection or message-loss tests to misbehave.
- **In-flight message accounting.** Increment on successful send, decrement on receive, using wrapping arithmetic. Mismatched counts break deadlock detection (`simulation_deadlock::*`) and clean step completion.
- **Recyclable-box discipline.** The queue slot must receive the vacated box back on `MessageBorrow` drop and re-publish the stamp with release ordering; the receiver must vacate/reuse its future box. Getting ordering or box ownership wrong causes UB, double-frees, or loom failures.
- **Memory ordering.** Stamps/positions in the queue and in slots require correct `Acquire`/`Release` pairing; the code is designed to be loom-checkable, so sloppy `Relaxed` usage may pass normal tests but is incorrect.
- **Capacity edge cases.** Capacity 1/2/3 are explicitly tested; off-by-one in ring-buffer full/empty detection is a classic failure here.
- **Broadcaster with zero recipients / filtered-out items.** Must complete immediately without awaiting a nonexistent reply, and `filter_map` connections must correctly skip items.
- **Cyclic task drops.** The executor must be able to drop tasks that reference each other without infinite recursion or aborting (`*_drop_cycle*`).
- **Ticker arithmetic.** Sub-tick, exact-tick, multi-tick, past-reference, and very-large-step cases each stress rounding/overflow in tick computation.
- **`_mt` vs `_st` parity.** Many behaviors are tested in both single- and multi-threaded executors; logic must be free of executor-specific assumptions (e.g., don't rely on same-thread execution ordering).

## Cheat surface

The following would technically make listed tests pass but do **not** constitute a correct solution and should be treated as cheating / rejected:

- **Weakening or deleting tests**, changing `#[should_panic]` expectations, adding `#[ignore]`, or editing the integration test files under `nexosim/tests/**` or the in-module `#[cfg(test)]` blocks.
- **Special-casing test inputs**: detecting the exact values/sizes/seeds used by a test and returning hard-coded answers (e.g. returning a fixed permutation for the priority-queue fuzz test, or a canned distribution for the RNG chi² test) instead of implementing general logic.
- **Stubbing out safety**: making `close`/`Drop`/deadlock-detection into no-ops that merely avoid a panic, or swallowing errors, so a test that expects an error/loss/deadlock still "passes" for the wrong reason.
- **Replacing `panic!("STUB")` with a different silent placeholder** (e.g. returning `Default`/empty) that happens to slip past a specific assertion without implementing the behavior.
- **Loosening the RNG uniformity test threshold** or reducing loop/iteration counts in tests to dodge statistical/fuzz checks.
- **Making tests pass by disabling features / removing `#[test]` attributes / conditional compilation** that excludes failing tests.
- **Reintroducing panics behind `catch_unwind` in the library** solely to convert a stub panic into a test-visible success.

Legitimate solutions implement general, correct algorithms whose behavior is independent of the particular test vectors.

## Success criteria

- The crate compiles cleanly (all modules, no remaining `panic!("STUB: not implemented")` or `#[allow(unreachable_code)] loop {}` placeholders on any path), with no new warnings-as-errors introduced by missing `Debug`/`Display`/trait impls.
- Every test in the `fail_to_pass` list transitions from failing to passing, including all `_st`/`_mt` pairs, the fuzz/statistical tests (`indexed_priority_queue_fuzz`, `find_bit_fuzz`, `rng_gen_bounded_chi2`), and the full `simulation_*`, `injector::*`, `model_scheduling::*`, and `serialization::*` integration suites.
- No previously-passing test regresses (the crate's other tests and doctests, if any, continue to pass).
- Tests, benchmarks, and non-stubbed source remain unmodified; all changes are confined to filling in the stubbed implementations listed in the task.
- Behavior is correct in general (not input-specific), race-free in the multi-threaded/loom-checkable paths, and panic-safe where the contract requires it (scoped thread-locals, drop-time channel closure, cyclic task drops).