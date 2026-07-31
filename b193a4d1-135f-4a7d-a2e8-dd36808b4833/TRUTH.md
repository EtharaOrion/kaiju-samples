# TRUTH.md

## Problem

The crate `little-raft` (a compact, generic implementation of the Raft distributed-consensus protocol) has had the bodies of its core source files replaced with stubs. Trait methods have empty bodies or `panic!("STUB: not implemented")`, several `enum`/`struct` variants and fields are missing, and the `Timer` / `StateMachine` supporting types are unimplemented.

The goal is to restore a working Raft implementation so that a cluster of `Replica`s, each running on its own thread and communicating through a user-supplied `Cluster` abstraction, can:

- elect a single stable leader,
- replicate a log of client-submitted transitions,
- commit and apply those transitions to a user-defined state machine in a consistent order across all replicas,
- optionally compact the log into snapshots.

The integration test(s) named `run_replicas` construct several in-process replicas wired together with in-memory channels, submit a set of transitions, and assert that every replica's state machine converges to the same final state and that all submitted transitions are eventually applied. These tests currently panic on the stubbed code and must pass.

## Behavioral contract

A correct solution must satisfy these observable behaviors:

- **Public API shape is preserved.** `Cluster<T, D>`, `StateMachine<T, D>`, `StateMachineTransition`, `Snapshot<D>`, `TransitionState`, `Message<T, D>`, `LogEntry<T>`, `Replica<C, M, T, D>`, `Timer`, and `ReplicaID` remain the exported names with the signatures the rest of the crate and the tests expect. `Replica::new(...)` and `Replica::start(recv_msg, recv_transition)` keep their parameter lists.

- **Message enum is complete.** The `Message` variants used by the algorithm exist with all their fields: an append-entries request (leader → follower: term, `from_id`, previous log index/term, the entries to append, leader commit index), an append-entries response (term, `from_id`, success flag, the follower's last index, and an optional mismatch/conflict index), a vote request (term, `from_id`, last log index/term), and a vote response (term, `from_id`, granted flag).

- **State-machine trait works.** The state-machine trait exposes: applying a transition, retrieving pending client transitions, registering the state of a transition (queued/committed/applied/abandoned as modeled by `TransitionState`), producing a snapshot, and (re)loading from a snapshot. `Snapshot<D>` carries the last-included index, last-included term, and the serialized state data.

- **Replica construction.** A freshly created replica with no seed snapshot begins its log with a single no-op entry at index 0 / term 0 so that the log is never empty. A replica constructed from a seed snapshot instead starts with an empty in-memory log, an `index_offset` equal to one past the snapshot's last-included index, and `current_term` reflecting the snapshot. Initial state is Follower.

- **Leadership and elections.** A follower that receives no valid heartbeat before a randomized election deadline (chosen within the configured `election_timeout_range`) becomes a candidate, increments its term, votes for itself, and solicits votes. A candidate that gathers votes from a majority of the cluster becomes leader; a candidate/leader that sees a higher term reverts to follower. Exactly one leader per term is possible.

- **Heartbeats.** A leader periodically (driven by the heartbeat `Timer`) broadcasts append-entries requests — including empty ones as heartbeats — that reset followers' election deadlines and assert the leader's authority.

- **Log replication and commit.** The leader tracks per-peer `next_index`/`match_index`, sends the entries each peer is missing, retreats `next_index` on rejection (using the follower-reported conflict/mismatch information when available), and advances `commit_index` once an entry from the current term is replicated on a majority. Followers append entries only when the previous-log-index/term matches, truncating conflicting suffixes otherwise, and adopt the leader's commit index.

- **Apply and convergence.** Every replica applies committed-but-unapplied entries to its state machine in log order, updates `last_applied`, and reports transition state back to the state machine. All replicas eventually apply the same sequence, so their state machines converge.

- **Snapshotting.** When `snapshot_delta > 0` and enough entries have accumulated past the last snapshot, a replica compacts its applied log prefix into a snapshot, adjusting `index_offset` so that log access remains `log[real_index - index_offset]`. A leader whose follower needs an already-compacted entry must be able to bring that follower up to date. When `snapshot_delta == 0`, snapshotting is disabled.

- **Driven, non-blocking event loop.** `start` loops until the cluster's `halt()` returns true. The replica only polls the cluster for messages when notified over `recv_msg`, and only pulls new client transitions when notified over `recv_transition`. It must not busy-spin unboundedly nor block forever ignoring the timer; leaders additionally react to the heartbeat timer. Waiting on multiple channels is done with a select-style multiplexer.

- **Leader-change hook.** Whenever the perceived leader changes (including becoming unknown), the replica informs the user via the cluster's `register_leader` hook.

- **Timer semantics.** `Timer::new(duration)` starts a timer that will signal once after `duration`; `get_rx()` exposes a receiver the event loop can wait on; `renew()` restarts the countdown. The timer must not block the caller.

## Solution decomposition

A natural decomposition of the work:

1. **`lib.rs`** — restore the module declarations (`cluster`, `message`, `replica`, `state_machine`, `timer`) and crate-level docs. No logic.

2. **`cluster.rs`** — the `Cluster` trait already lists its methods; only documentation needs restoring. Behaviorally it is a no-op change, but the trait must remain intact and object-usable behind `Arc<Mutex<_>>`.

3. **`message.rs`** — fill in the missing `Message` enum variants and their fields, plus the `LogEntry` metadata. Ensure the derives (`Clone`, `Debug`, `PartialEq`, etc.) still hold.

4. **`state_machine.rs`** — define/complete `StateMachineTransition` (with an id and a stable ordering key), `TransitionState`, `Snapshot<D>`, and the `StateMachine` trait methods (apply, pending, register state, get/load snapshot).

5. **`timer.rs`** — implement a timer backed by a background thread (or equivalent) and a channel, supporting creation, receiver access, and renewal.

6. **`replica.rs`** — the bulk of the work:
   - `new`: initialize fields, seed from snapshot or plant the index-0 no-op entry.
   - `start`: the halt-checked dispatch loop with post-step `apply_ready_entries`.
   - `poll_as_leader` / `poll_as_follower` / `poll_as_candidate`: select over the relevant channels/timers and react.
   - `process_message`: full handling of all four message variants (append request/response, vote request/response), including term updates and state transitions.
   - Helpers: broadcast append requests, compute entries per peer, term-at-index lookups (accounting for snapshots and returning a "compacted" error where relevant), election-deadline updates, load pending transitions, become-leader/follower/candidate transitions, commit advancement, apply-ready-entries, and snapshot creation.

## Solution space

Multiple correct routes exist; do not penalize deviations that preserve the contract:

- **Channel / select library:** The reference uses crossbeam's `Select`. Any equivalent mechanism (`std::sync::mpsc` with timeouts, a different channel crate, condition variables, or a hand-rolled poll loop with bounded sleeps) is acceptable as long as the loop is notification-driven, respects the heartbeat timer, and does not block forever or busy-spin.

- **Timer implementation:** A background thread + channel, a `crossbeam` ticker, a timestamp/deadline compared inside the loop, or an async timer are all valid, provided `new`/`get_rx`/`renew` behave as specified and don't block the caller.

- **Conflict resolution optimization:** The optional `mismatch_index`/conflict-index fast-backup is an optimization. A simpler linear `next_index` decrement per rejection is also correct (just slower to converge); the tests only require eventual convergence.

- **Snapshot data representation:** The concrete serialized form of `Snapshot.data` is user/state-machine defined; the crate only stores and forwards it. Any representation the test's state machine agrees on is fine.

- **Field naming and internal structure:** Internal helper names, extra private methods, or a differently factored commit-advancement routine are acceptable. Only the exported types/signatures and behavior are contractual.

- **Randomization source:** Any RNG for the election timeout within the configured range is acceptable; the important property is that timeouts vary enough to avoid perpetual split votes.

## Known pitfalls

- **Empty-log invariant.** Forgetting the index-0 no-op entry (when no snapshot) makes `prev_log_index`/term lookups and the very first append underflow or panic. Conversely, planting it when starting from a snapshot corrupts indexing.

- **Index-offset arithmetic.** All log access must translate absolute indices to physical slots via `index_offset` (`log[abs - index_offset]`). Mixing absolute and physical indices, or off-by-one in `last_log_index = log.len() - 1 + index_offset`, breaks replication and snapshotting. `next_index[peer] - 1` can reference a compacted entry — handle the "log compacted" case rather than panicking.

- **Commit rule tied to current term.** A leader must only advance `commit_index` on a majority match for an entry **from its own current term** (Raft's safety rule). Committing based purely on majority replication of an older-term entry is incorrect.

- **Term monotonicity.** Any message carrying a higher term must force a step-down to follower and adoption of the new term before further processing; failing to do so allows multiple leaders.

- **Vote safety.** Grant a vote only if the candidate's log is at least as up-to-date and the voter hasn't already voted for someone else this term. Resetting `voted_for` correctly across terms is essential.

- **Election deadline resets.** Only *valid* leader/candidate contact should reset a follower's election deadline; otherwise stale nodes prevent progress or elections never fire.

- **Not driving the heartbeat/renew.** A leader that stops sending heartbeats (forgot to `renew()` the timer or didn't include it in the select) causes constant re-elections and non-convergence.

- **Deadlock via locking.** `cluster` and `state_machine` sit behind `Arc<Mutex<_>>`. Holding one lock while calling back into user code that needs the same lock, or holding a lock across a blocking channel wait, can deadlock the whole cluster.

- **Applying transitions more than once / out of order.** `last_applied` must gate application; the no-op transition must be idempotent (safe to apply repeatedly with no effect).

- **Notification-driven polling.** Calling `receive_messages` unconditionally in a tight loop violates the contract (it must only be called after a `recv_msg` notification) and can spin the CPU or drop messages.

- **halt() not checked.** If `start` never consults `halt()`, the test threads never terminate and the test hangs.

## Cheat surface

The reference diff is an authoring aid only. Watch for these non-solutions:

- **Hard-coding the test outcome.** Making the state machine converge only for the specific transitions/replica count in `run_replicas`, or special-casing peer counts, is illegitimate. The implementation must be a general Raft.

- **Bypassing consensus.** Directly copying transitions into every replica's state machine (e.g., via shared memory) instead of replicating through the `Message` protocol and leader-commit rule defeats the purpose.

- **Stub-only "passing".** Replacing `panic!` with silent no-ops that let the loop exit immediately (e.g., always returning from `start`) may avoid panics but produces no replication — the convergence assertions will fail.

- **Removing/weakening assertions or editing the test.** The `run_replicas` test itself and any test harness must remain the arbiter; changes there are cheating.

- **Ignoring safety for speed.** Committing without the majority + current-term rule may pass a lucky run but is not a correct solution; correctness must hold regardless of timing.

- **Faking the timer.** A `Timer` that never fires (or fires immediately forever) can superficially compile but breaks either heartbeats or elections.

## Success criteria

A solution is correct when:

- The crate compiles cleanly (with its existing dependencies) and exposes the same public types and signatures.
- The previously stubbed `panic!`/empty bodies are replaced with real logic; no `panic!("STUB...")` remains on any reachable path.
- The `run_replicas` integration test(s) flip from failing to passing: a multi-replica cluster elects a single leader, replicates all submitted transitions, and every replica's state machine converges to the identical final state with all transitions applied, terminating cleanly once `halt()` is signaled.
- The implementation is a genuine, general Raft: leader election with randomized timeouts, heartbeat-driven authority, log matching with conflict backoff, majority-and-current-term commit, in-order idempotent application, leader-change notification, and (when enabled) log compaction with correct index-offset handling.
- No test files or assertions are modified to achieve the pass.