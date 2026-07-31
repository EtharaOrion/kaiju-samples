# TRUTH.md

## Problem

The `riker` crate is a Rust actor-system framework whose implementation files have been reduced to compilable stubs. Nearly every function body has been replaced with `panic!("STUB: not implemented")` (or trivial placeholders), while type definitions, field declarations, trait signatures, module structure, and public re-exports remain intact.

The task is to restore the real implementation of every stubbed function across the actor, kernel, and system layers so that the crate builds and its integration/unit test suite passes. The specification document that originally accompanied the crate (`spec.pdf.bz2`) is removed as part of the solution; behavior must be inferred from the existing type signatures, the tests, and standard actor-model semantics.

The destination is a fully working actor runtime that supports: creating actors under a hierarchical supervision tree, sending user and system messages through mailboxes processed by a kernel/dispatcher, publishing/subscribing on channels (including dead letters and system events), path-based actor selection, supervision strategies (restart/stop/escalate), scheduled/timed message delivery, futures execution on the system's thread pool, structured/standard logging, and clean system shutdown.

## Behavioral contract

Group the required behavior by the `fail_to_pass` test clusters. Each cluster describes observable end-to-end behavior that must hold; internal routing details are implementation choices.

### Actor lifecycle (`actor_create`, `actor_stop`, `actor_tell`, `actor_try_tell`)
- An `ActorSystem` can be constructed and `actor_of::<A>(name)` (and `actor_of_props`) returns a typed `ActorRef` for an actor placed under the user guardian.
- Duplicate names at the same path, invalid names (validated by `src/validate.rs`), or actors that panic in `pre_start` produce the appropriate `CreateError` variant (`AlreadyExists`, `InvalidName`, `Panicked`, `System`) rather than a live ref.
- Sending a message via `tell` enqueues an envelope (message + optional sender) into the actor's mailbox; the actor's `recv` is eventually invoked exactly once per message, with at most one message processed at a time per actor.
- `try_tell` on a `BasicActorRef`/`Option<ActorRef>` succeeds when the concrete message type matches the actor's message type and yields a `TryMsgError` (or equivalent failure) when the type does not match or the option is `None`.
- Stopping an actor (`system.stop(actor)` / `ctx.stop`) drives it and its subtree to termination: children are stopped first, `post_stop` runs, and the actor is removed from its parent's child set. After termination, further `tell`s are effectively dropped (dead-lettered).

### Channels and events (`channel_publish`, `channel_publish_subscribe_all`, `channel_system_events`, `channel_dead_letters`)
- A `Channel<Msg>` actor supports `Subscribe`/`Unsubscribe`/`Publish` semantics: publishing a message on a topic delivers it to every current subscriber of that topic, and subscribing to the "all" topic receives every published message.
- Unsubscribed actors and actors that terminate stop receiving further published messages.
- The system exposes an event stream / system-events channel that emits `SystemEvent` notifications (e.g. `ActorCreated`, `ActorRestarted`, `ActorTerminated`) to subscribers.
- Dead letters: messages sent to a nonexistent/terminated actor are routed to the dead-letters channel and delivered to its subscribers as `DeadLetter` entries.

### Selection (`select_child`, `select_child_of_child`, `select_all_children_of_child`, `select_from_context`, `select_paths`)
- `system.select(path)` and `ctx.select(path)` build an `ActorSelection` from an absolute or relative path string.
- Selection resolves path segments against the actor hierarchy, supporting a single child (`"child"`), nested children (`"child/grandchild"`), wildcard/all-children selection, and selection relative to a context (`ctx.myself`). `try_tell` on a selection delivers to all matched actors.
- Path strings produce the correct resolved actor URIs/paths; unmatched paths deliver to no actor (and dead-letter as appropriate).

### Supervision (`supervision_restart_failed_actor`, `supervision_escalate_failed_actor`)
- When an actor panics while handling a message, its failure is reported to its parent (supervisor). The parent consults its `supervisor_strategy()`.
- `Strategy::Restart` re-creates the actor instance (fresh state, `post_stop` then re-instantiate and `pre_start`/`post_start`) while preserving its mailbox/path, and continues processing.
- `Strategy::Escalate` propagates the failure up to the grandparent, which then applies its own strategy.
- `Strategy::Stop` terminates the failed actor. A `RestartError` path exists for actors that panic again while restarting.

### Scheduling / timers (`schedule_once`, `schedule_repeat`, `schedule_at_time`)
- The system's timer (`src/system/timer.rs`) supports `schedule_once(delay, receiver, sender, msg)`, `schedule(initial, interval, ...)` (repeating), and `schedule_at_time(time, ...)`, each returning a cancelable `ScheduleId`.
- A one-shot schedule delivers the message once after the delay; a repeat schedule delivers repeatedly at the interval until canceled; an at-time schedule delivers at (or just after) the specified instant.
- `cancel_schedule` prevents future deliveries.

### System bring-up and shutdown (`system_create`, `system_builder`, `system_load_app_config`, `system_shutdown`, `system_create_with_slog`)
- `ActorSystem::new()` and the `SystemBuilder` (name, config, log, exec/dispatcher) produce a running system with the standard guardian hierarchy (root, user, system/temp guardians) already started.
- Application configuration is loaded (default config merged with any provided config), exposed via `system.config()`.
- `system.shutdown()` returns a future/handle that completes once all actors terminate and background threads stop cleanly.
- Providing a custom logger (slog backend) at build time is supported.

### Futures execution (`system_futures_exec`, `system_futures_panic`)
- The system implements a futures executor: `system.run(future)` (or equivalent) schedules a future on the system thread pool and returns a handle whose result can be awaited/blocked on.
- A future that panics does not crash the system; the panic is contained and surfaced through the returned handle.

### Logging (`logging_stdlog`, `system_create_with_slog`)
- The system installs a logging facade (`src/system/logger.rs`) bridging to the `log`/`slog` ecosystem, and log records emitted during system operation are captured by the standard `log` backend in `logging_stdlog`.

## Solution decomposition

Independent sub-goals, roughly in dependency order. Each can be verified in isolation once its dependencies exist.

1. **Error and helper value types (`src/actor.rs`).** Implement constructors and `Display`/`Debug`/`From` for `MsgError`, `TryMsgError`, `CreateError`, `RestartError`; supply default trait-method bodies for `Actor` (`pre_start`/`post_start`/`post_stop`/`supervisor_strategy` default = `Restart`/`sys_recv`), and delegating impls for `Box<A>`. Provide the `Strategy` enum semantics.

2. **URIs and validation (`src/actor/uri.rs`, `src/validate.rs`).** Path/URI construction, formatting, equality, and name validation returning `InvalidName` for illegal actor names.

3. **Props (`src/actor/props.rs`).** Factory abstraction that produces boxed `Actor` instances (from `Default`, from args, from closures), used by the kernel to (re)create actor instances on start and restart.

4. **Actor cell + refs (`src/actor/actor_cell.rs`, `src/actor/actor_ref.rs`).** The `ActorCell` holds shared inner state (uri, parent, children set, status/terminating/restarting flags, kernel handle, system handle, mailboxes). Implement construction, `init` (attach kernel), accessors, child management, `send_any_msg`/`send_sys_msg` dispatch, `is_child`/`is_root`/`is_user`, and the lifecycle drivers `terminate`, `restart`, `receive_cmd`, `death_watch`, `handle_failure`. Implement `ActorRef`/`BasicActorRef` with `tell`, `try_tell`, `sys_tell`, path/equality/ordering.

5. **Channels (`src/actor/channel.rs`).** `Channel`, system-event channel, and dead-letter channel actors implementing subscribe/unsubscribe/publish and topic routing.

6. **Selection (`src/actor/selection.rs`).** Parse path strings into selection segments and resolve them against the hierarchy; implement `try_tell`/`sys_tell` over the resolved set.

7. **Kernel, mailbox, queue, provider (`src/kernel/*.rs`).** The mailbox queue (MPSC of envelopes), the mailbox run-loop that dequeues and invokes `recv`/`sys_recv` under a single-threaded-per-actor guarantee, the `KernelRef` commands (start/stop/restart/terminate/message processing), and the `provider` that creates actors, wires cells to kernels, and registers them in the tree.

8. **System (`src/system.rs`, `src/system/timer.rs`, `src/system/logger.rs`).** System construction/builder, guardian bootstrap, config loading, dispatcher/executor + futures `run`, timer scheduling, logger installation, and shutdown coordination.

9. **Crate wiring (`src/lib.rs`).** Module declarations and public prelude/re-exports so downstream (tests) can `use riker::actors::*`.

## Solution space

Valid alternative approaches — a correct solution need not match the golden diff's exact choices:

- **Concurrency primitives:** interior sharing may use `Arc<Inner>` with atomics/`RwLock`/`Mutex`/`DashMap`; any thread-safe children collection and status representation is acceptable as long as the single-message-at-a-time-per-actor guarantee and correct termination ordering hold.
- **Dispatcher/executor:** the futures executor may be built on a thread pool, `futures` executor, or channel-driven worker loop; only the observable `run`/panic-isolation behavior matters.
- **Timer implementation:** a dedicated timer thread with a sorted schedule, a wheel, or delay-based tasks are all acceptable, provided one-shot/repeat/at-time semantics and cancellation work.
- **Status encoding:** status may be an atomic integer with encoded states or an enum behind a lock.
- **Error `Display` wording:** exact user-facing strings are an implementation detail and should NOT be treated as required unless a test asserts them; matching semantics (which variant, `From<InvalidName>`, restart-on-panic messaging) is what matters.
- **Channel topic model:** topics may be strings or typed keys; subscriber storage may be per-topic maps or a flat list with filtering.
- **Selection parsing:** may be done with manual segment splitting or a small parser; wildcard handling and relative-vs-absolute resolution are the invariants.

## Known pitfalls

- **Termination ordering:** an actor with children must stop all children and wait for their `ActorTerminated` before terminating itself and running `post_stop`. Terminating leaf-first is required; skipping the wait leaks or double-frees.
- **Restart semantics:** on restart, preserve the mailbox and path but rebuild actor state via props; run `post_stop` then re-run `pre_start`/`post_start`. A panic during restart must surface `RestartError` and not loop infinitely.
- **`pre_start` panic is special:** a panic in `pre_start` does NOT invoke supervision — the actor fails to create (`CreateError::Panicked`). Panics elsewhere (in `recv`/`post_start`) DO follow the supervisor strategy.
- **`supervisor_strategy` default must be `Restart`**, and `Box<A>` delegations must forward to the inner actor rather than using the default.
- **System-message vs user-message channels:** system messages use a distinct mailbox and must continue to be processed even while user messages are suspended (e.g., during termination).
- **Dead-letter routing:** `tell`/`try_tell` to a terminated or nonexistent actor must not panic; it must route to dead letters. Type mismatch in `try_tell` must be reported, not silently dropped incorrectly.
- **Escalation:** escalate must climb to the parent's supervisor and apply the parent's strategy, not re-apply the child's.
- **Guardian bootstrap:** the root/user/system guardians must exist before `actor_of` works; `is_user`/`is_root`/`user_root` depend on them.
- **`init` and `Arc` cloning:** attaching the kernel typically rebuilds inner state; ensure the kernel handle is not lost and that clones share the same inner `Arc`.
- **Futures panic isolation:** a panicking future must not poison shared locks or bring down the executor thread pool.
- **Config merging:** loaded app config must merge defaults with user-supplied values; `system_load_app_config` expects specific keys to resolve.
- **Selection paths:** correctly distinguish absolute (`/user/...`) from relative paths, and handle the "all children" wildcard vs a named child.

## Cheat surface

Ways a solution could pass superficially without being a correct general implementation — these must be rejected:

- **Hardcoding to test fixtures:** returning fixed values, matching on specific actor names/paths/message contents used by the tests, or special-casing the exact number/order of subscribers instead of implementing general routing.
- **Reproducing golden error strings** to satisfy nothing (no behavior) — and conversely, only real behavior (not the private diff's exact wording) is required.
- **Stubbing supervision:** making restart/escalate no-ops that happen to let a test finish, without actually rebuilding state or climbing the tree.
- **Timers via `sleep` in the test thread** or delivering immediately regardless of delay/interval, rather than a real schedule honoring order and cancellation.
- **Faking futures execution** by running the future synchronously on the caller in a way that doesn't isolate panics (would fail `system_futures_panic` for the right reason but could mask executor bugs) — panic isolation must be genuine.
- **Leaving `panic!("STUB…")` reachable** behind conditions the current tests never hit.
- **Disabling/emptying tests, marking them `#[ignore]`, or editing the `fail_to_pass` tests** to trivially pass.
- **Removing the logging facade but printing** so a log-capture assertion coincidentally passes without a real `log`/`slog` bridge.

## Success criteria

- The crate compiles (library and test targets) with no remaining `STUB: not implemented` panics on any exercised path.
- All listed `fail_to_pass` tests pass: `actor_create`, `actor_stop`, `actor_tell`, `actor_try_tell`, `channel_dead_letters`, `channel_publish`, `channel_publish_subscribe_all`, `channel_system_events`, `logging_stdlog`, `system_create_with_slog`, `schedule_at_time`, `schedule_once`, `schedule_repeat`, `select_all_children_of_child`, `select_child`, `select_child_of_child`, `select_from_context`, `select_paths`, `supervision_escalate_failed_actor`, `supervision_restart_failed_actor`, `system_builder`, `system_create`, `system_futures_exec`, `system_futures_panic`, `system_load_app_config`, `system_shutdown`.
- No previously passing tests, doc-tests, or examples regress (the public API surface and re-exports in `src/lib.rs`/`src/actor.rs` remain intact).
- Behavior is general: actor creation/telling/stopping, channel pub/sub, selection, supervision, scheduling, futures execution, logging, config, and shutdown work for arbitrary actors/messages/paths, not just the test inputs.
- Tests pass because the implemented runtime is correct, not because tests were altered, ignored, or hard-coded around.