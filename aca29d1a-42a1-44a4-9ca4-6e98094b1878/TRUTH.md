# TRUTH.md

## Problem

The crate `concurrent-map` (`Zahgon/concurrent-map`) implements a lock-free, ordered B+ tree map (`ConcurrentMap`) inspired by sled's internal index structure, using epoch-based reclamation (the `ebr` crate) for safe memory reclamation and fixed-size node arrays (the `stack_map::StackMap` crate) for node contents.

The source files `src/lib.rs` and `src/serde.rs` were stubbed: many functions, trait implementations, and constants were replaced with `panic!("STUB: not implemented")` bodies (and some associated-const / field / doc placeholders were blanked). The task is to restore a fully working implementation so that the map behaves like a thread-safe, concurrently-mutable, lexicographically-ordered `BTreeMap` analogue with atomic compare-and-swap, range scans, and no memory leaks.

All listed tests (`basic_map`, `timing_map`, `big_scan`, `bulk_load`, `concurrent_tree`, `test_00`..`test_03`, `leak_check`) must compile and pass, including under the crate's optional features (e.g. `serde`, `timing`, `fault_injection`) that the tests exercise.

## Behavioral contract

The restored `ConcurrentMap<K, V, FANOUT, LOCAL_GC_BUFFER_SIZE>` must satisfy the semantics of an ordered key/value map. Where `K: Clone + Minimum + Ord + Send + Sync + 'static` and `V: Clone + Send + Sync + 'static`.

Core point operations (behaving like `BTreeMap`, but returning **cloned** values rather than references so no locks are held):
- `insert(k, v)` returns the previously-stored value for `k` (`Some(old)`) or `None`.
- `get(&k)` returns `Some(cloned_value)` if present, else `None`.
- `remove(&k)` returns the removed value (`Some`) or `None`.
- `contains_key`, `len`, `is_empty` behave consistently with the above. `len` may be an eventually-consistent/lagging count but must be exact once concurrent activity quiesces (tests assert final counts).

Compare-and-swap:
- `cas(k, old: Option<&V>, new: Option<V>)` atomically installs `new` only if the current value equals `old` (with `None` meaning "absent"). On success it returns the previous value; on failure it returns a `CasFailure<V>` whose `actual` field holds the currently-observed value and whose `returned_new_value` field returns ownership of the rejected `new` value back to the caller.

Ordered iteration / scans:
- `iter()`, `range(..)`, and related scan APIs yield key/value pairs (cloned) in ascending key order, over the requested bound, correctly, even while other threads mutate the tree.
- Reverse iteration is supported via `std::cmp::Reverse<K>` when `K: Maximum`.
- Scans must be robust to concurrent structural changes (node splits/merges, root replacement) — they retry/re-descend as needed and never miss or duplicate stably-present keys.

Traits & conversions:
- `Minimum` supplies a `MIN` associated const that is `<=` every value of the type; `Maximum` supplies a `MAX` that is `>=` every value. These must be implemented for the standard scalar/tuple/wrapper types the tests use (integers, `()`, `Reverse<T>`, tuples, etc.), and the values must actually be the extreme values (e.g. `u64::MIN`, `i32::MIN`, etc.), because the empty tree's left-most leaf is created from `K::MIN`.
- `Default` builds a valid empty tree.
- `PartialEq` compares two maps as equal iff they contain the same ordered key/value sequence (with a fast path for pointer/`Arc` identity).
- `Debug` renders as a map of entries.

Feature-gated behavior:
- With `serde`, `ConcurrentMap` serializes/deserializes as its logical key/value contents (round-trips to an equal map).
- With `timing`, per-op timing stats (fastest/slowest) are tracked.
- With `fault_injection`, `debug_delay()` sometimes yields/returns `true` to shake out interleavings; in normal builds it is a compile-time-eliminated constant `false`.

Memory-safety contract (critical for `leak_check`):
- Every node allocated must eventually be freed exactly once — no leaks and no double-frees. Replaced/removed nodes are handed to epoch-based reclamation rather than freed immediately, and are only dropped once no reader can observe them.

## Solution decomposition

The implementation naturally breaks into layers; a correct solution must get all of them right.

1. **Raw pointer wrapper (`BoxedAtomicPtr`)** — a stable, copyable identity for a tree slot.
   - Construction from an owned boxed `Node`: leak the node to a raw pointer, wrap that raw pointer in a heap-allocated `AtomicPtr`, and store the pointer-to-the-atomic. (Two levels of indirection: a stable atomic cell plus the swappable node behind it.)
   - `Deref` to the underlying `AtomicPtr` (deref the stored raw pointer).
   - `PartialEq`/`Eq` compare by the stored pointer identity.
   - A `node_view` helper that atomically loads the current node pointer (Acquire ordering) and, if non-null, produces a `NodeView` capturing both the loaded node pointer and this slot's identity; a null load yields `None`.

2. **Deferred reclamation (`Deferred` + its `Drop`)** — the payload placed into the `ebr` garbage buffer.
   - Dropping a deferred *node* frees the node.
   - Dropping a deferred *boxed atomic pointer* must reclaim the heap-allocated `AtomicPtr` cell itself (reconstruct the owning `Box` from the raw pointer and drop it), guarding against null.

3. **Node view (`NodeView`)** — an epoch-protected read handle over a node.
   - `Deref` exposes the node behind the captured pointer.
   - `cas` performs the RCU (read-copy-update) install: `compare_exchange` the slot's atomic from the observed pointer to the new (leaked) replacement.
     - On success: return a view of the newly-installed node, and defer-drop the replaced node through the guard.
     - On failure: reclaim the replacement `Box` we just leaked (so it isn't lost), and return either `Err(None)` if the slot was concurrently emptied (null) or `Err(Some(new_view))` reflecting the actual current node.
     - Must assert the invariant that a node's `hi`/`next` fields are both set or both unset.
     - Must honor the fault-injection hook (spuriously fail without touching memory when injected).
   - `get_mut` yields a mutable reference to the node — a single-owner optimization used only when uniqueness is guaranteed.

4. **Tree structure (`Inner`, `Node`, root/leaf construction)**.
   - `Default` builds a root index node whose single child is a leaf keyed on `K::MIN`, wraps it in `Inner`, and initializes epoch reclamation and length counter. Enforces `FANOUT > 3` and `LOCAL_GC_BUFFER_SIZE > 0` via assertions.
   - Node primitives: distinguishing index vs. leaf nodes, `lo`/`hi` bounds, `next` sibling links, split and merge logic, RCU copy-on-write of `StackMap` contents.

5. **Traversal & operations** — `get`/`insert`/`remove`/`cas`/`iter`/`range` descend from the root following child pointers and sibling (`next`) links, handling concurrent splits/merges by re-reading views and retrying, splitting overfull nodes, merging underfull ones, and installing a new root when the old root splits. The eventually-consistent length counter is updated on logical insert/remove.

6. **serde (`src/serde.rs`)** — `Serialize` iterates entries as a map; `Deserialize` builds a fresh `ConcurrentMap` by inserting deserialized entries, producing a value equal to the original.

## Solution space

Multiple correct routes exist; a valid solution need not match the golden diff line-for-line.

- **Memory-ordering choices**: The reference uses `Acquire` loads and `AcqRel`/`Acquire` for `compare_exchange`. Any orderings that are *at least* as strong and preserve correctness (e.g. `SeqCst` throughout) are acceptable, as long as reclamation and visibility invariants hold.
- **Pointer-reclamation reconstruction**: reconstructing the owning `Box` from the raw pointer (`Box::from_raw`) and dropping it is the natural approach; any equivalent that frees exactly the allocation created in `new` is valid.
- **`PartialEq` implementation**: comparing ordered iterators element-by-element, or collecting and comparing, are both acceptable; the `Arc`-identity fast path is an optimization, not a requirement.
- **`Debug`**: any output that reasonably renders the entries is acceptable; the exact string is not asserted by the required tests (verify no test pins a specific format).
- **`fault_injection` `debug_delay`**: any implementation that occasionally returns `true` (optionally yielding) and usually returns `false` is fine; the exact probability distribution is unconstrained. Only the non-fault build's constant-`false` behavior is contractually fixed.
- **`Minimum`/`Maximum` extents**: any expression equal to the true type minimum/maximum works (`T::MIN`, associated consts, literal extremes). Tuple/`Reverse` impls compose from component extents.
- **Split/merge policy details** (fan-out thresholds, when to merge) may differ from the reference so long as `MERGE_SIZE == 1` invariant and the ordered-map semantics are preserved.
- **serde**: implementing via a helper `BTreeMap`/sequence adapter, or hand-written visitors, are both valid.

## Known pitfalls

- **Double indirection**: `BoxedAtomicPtr` stores a pointer to a heap `AtomicPtr`, which in turn points to the node. Confusing the two levels leads to freeing the wrong allocation (leak or UB). `Deferred`'s drop reclaims the *atomic cell*; node drops reclaim the *node*.
- **Leaking the replacement on failed CAS**: `cas` leaks the replacement box before the `compare_exchange`. On failure you **must** reclaim that box, or `leak_check` fails. On success you **must** defer-drop the old node (not free it immediately, or concurrent readers get UB).
- **Immediate vs. deferred free**: Never `Box::from_raw`+drop a node that could still be observed by another thread; route it through the epoch guard's defer-drop. Conversely, the rejected replacement in a failed CAS was never published, so it is safe (and required) to free promptly.
- **Null handling**: A concurrently-emptied slot loads as null; `node_view` must return `None` and `cas` must return `Err(None)` rather than dereferencing null.
- **Invariant assertion**: `hi` and `next` must be simultaneously `Some` or `None`; violating (or omitting) this check permits malformed nodes.
- **`Default` construction ordering**: the root must contain a leaf keyed at `K::MIN` before any inserts; forgetting this makes the tree unable to accept the first key. The `FANOUT > 3` / `LOCAL_GC_BUFFER_SIZE > 0` assertions guard against degenerate node arrays.
- **Wrong `Minimum`/`Maximum` values**: using something other than the true extreme (e.g. `0` for a signed type) breaks left-edge/right-edge correctness and range scans.
- **PartialEq iterator symmetry**: comparing only one direction (not checking the second iterator has also ended) reports differing-length maps as equal.
- **Concurrent retry loops**: operations must re-read node views after a lost race rather than reusing a stale `NodeView`; otherwise updates are lost or panic.
- **Feature-gated fields**: the `timing` feature adds `slowest_op`/`fastest_op` fields to `Inner`; construction must initialize them under `cfg` (min/max sentinels) so both feature and non-feature builds compile.

## Cheat surface

The following would make tests pass superficially or trivially without a correct concurrent B+ tree, and must be treated as non-solutions:

- Replacing the lock-free tree with a `Mutex<BTreeMap>`, `RwLock`, `DashMap`, or other off-the-shelf map behind the same public API. The task is to implement the specified lock-free structure; wholesale replacement of the internal algorithm is out of scope even if some tests pass. (Verify the epoch-reclamation and RCU node machinery is genuinely used.)
- Making `debug_delay()` in the non-fault build return anything other than a const-foldable `false`, or hard-coding the fault-injection path off entirely.
- Leaking memory intentionally (e.g. `mem::forget`, `Box::leak`) to sidestep double-free bugs — `leak_check` exists specifically to catch this.
- Weakening trait bounds, `unsafe`-transmuting, or using `static mut`/globals to fake shared state.
- Implementing `PartialEq`/`Debug`/serde in ways that don't reflect the actual stored contents (e.g. always returning `true` from `eq`, or serializing an empty map).
- Editing or deleting the tests, changing the `fail_to_pass` assertions, or gating real logic behind test-only `cfg`s.
- Deleting `spec.pdf.bz2` or other repo files as a stand-in for implementing behavior (removing the spec artifact is incidental and not part of the solution).

## Success criteria

- `src/lib.rs` and `src/serde.rs` contain no remaining `panic!("STUB: not implemented")` (or equivalent unimplemented) bodies; every stubbed function, trait impl, associated const, and struct field is filled with a correct implementation.
- The crate compiles cleanly under the default feature set and under each feature combination the test suite requires (at minimum `serde`, `timing`, and `fault_injection` as exercised by `timing_map` and the concurrency/leak tests).
- All listed `fail_to_pass` tests pass: `basic_map`, `timing_map`, `big_scan`, `bulk_load`, `concurrent_tree`, `test_00`, `test_01`, `test_02`, `test_03`, `leak_check` — including their concurrency stress and leak-detection assertions.
- The public API (`insert`, `get`, `remove`, `cas`, `iter`, `range`, `len`, `Default`, `PartialEq`, `Debug`, `Minimum`/`Maximum`, serde round-trip) behaves per the Behavioral contract, with cloned-value returns and ordered iteration.
- No memory leaks or double-frees under `leak_check`, i.e. epoch-based deferred reclamation is used correctly for both nodes and atomic-pointer cells.
- No test files, fixtures, or task metadata are modified to force passage.