# TRUTH.md

## Problem

The repository is a fork of `allegro/bigcache/v3`, a fast, concurrent, sharded, evicting in-memory cache for Go that stores serialized byte entries on the heap while avoiding per-entry GC pressure. Every source file across the core package (`bigcache.go`, `shard.go`, `config.go`, `encoding.go`, `hash.go`, `fnv.go`, `iterator.go`, `stats.go`, `clock.go`, `logger.go`, `utils.go`, `bytes*.go`, `entry_not_found_error.go`), the `queue` subpackage (`bytes_queue.go`), and the `server` subpackage (`server.go`, `cache_handlers.go`, `middleware.go`, `stats_handler.go`) has had its function bodies replaced with stubs of the form `_ = "STUB: not implemented"` returning zero values.

The task is to re-implement all stubbed function bodies so that the full existing test suite (core cache, byte queue, and HTTP server) passes. Function signatures, type definitions, struct field names, and exported API surface are already fixed by the surrounding (non-stubbed) code and the tests; the work is to supply correct behavior.

## Behavioral contract

The implementation must satisfy the observable behavior the tests assert. Grouped by area:

### Cache construction & validation (`New`, `NewBigCache`, `newBigCache`, `DefaultConfig`)
- Construction must reject invalid configs with an error (never a panic): a `Shards` value that is not a power of two, and any of `MaxEntrySize`, `MaxEntriesInWindow`, `HardMaxCacheSize` that is negative.
- When `CleanWindow > 0` but the configured `LifeWindow` rounds down to 0 seconds, construction must return an error.
- A `nil` `Hasher` in the config must be replaced with the default FNV64 hasher so construction still succeeds.
- `New` accepts a `context.Context`; `NewBigCache` is the deprecated context-free variant using a background context. Both delegate to a shared builder that also accepts a `clock` (tests inject a fake clock via the internal builder).
- The cache holds a slice of shards sized to `config.Shards`, a `shardMask` equal to `Shards-1`, a life window expressed in seconds, and a `close` channel.
- If `CleanWindow > 0`, a background goroutine periodically triggers cleanup on a ticker; it must terminate when either the context is cancelled or the cache is closed.
- `DefaultConfig(eviction)` returns a config with sensible defaults (notably 1024 shards, the given life window, a 1-second clean window, a non-nil default hasher, and a default logger).

### Core cache operations (`Get`, `GetWithInfo`, `Set`, `Append`, `Delete`, `Reset`, `ResetStats`, `Len`, `Capacity`, `Stats`, `KeyMetadata`, `Iterator`, `Close`)
- Each keyed operation hashes the key, selects the shard via `hashedKey & shardMask`, and delegates to the shard.
- `Get` returns the stored bytes or an `ErrEntryNotFound` sentinel when absent. Returned data must be a copy so later cache mutation does not corrupt the caller's slice.
- `GetWithInfo` returns the bytes plus a `Response` describing entry status (e.g. expired), returning not-found appropriately.
- `Set` stores/overwrites an entry; a nil value must be storable and retrievable as empty/nil.
- `Append` concatenates onto an existing entry, or behaves like `Set` when the key is absent; concurrent appends to the same key must accumulate correctly.
- `Delete` removes a key, updating delete-hit/delete-miss statistics; deleting a missing key yields not-found.
- `Reset` empties every shard; `ResetStats` zeroes statistics only.
- `Len` sums entry counts across shards; `Capacity` sums the byte capacity across shards.
- `Stats` aggregates hits, misses, delete hits/misses, and collisions across shards.
- `Close` signals shutdown by closing the `close` channel exactly once, letting background goroutines exit; it must not leave references that block GC.
- `Iterator` returns an iterator over all entries in the whole cache.

### Eviction & callbacks
- Hash collisions (different keys mapping to the same hashed key) must be detected by comparing the stored key against the requested key; a collision on read returns not-found and increments a collision counter rather than returning the wrong value.
- Time-based eviction: an entry is expired when the current timestamp minus its stored timestamp exceeds the life window (and never when current precedes stored). Expired entries are evicted on cleanup and, where applicable, on access.
- When a shard is full (respecting `HardMaxCacheSize`/max shard bytes), the oldest entry is evicted to make room (reason "no space"); an entry larger than the maximum shard size yields an error.
- Four `onRemove` dispatch variants must be selected based on which callback the config provides, with correct precedence: metadata callback, then plain `OnRemove`, then `OnRemoveWithReason`, else a no-op. The reason-based callback must honor the `onRemoveFilter` bitmask set via `OnRemoveFilterSet`.
- `KeyMetadata` reports how many times a key has been requested (when stats are enabled).

### Byte queue (`queue/bytes_queue.go`)
- A FIFO byte queue backed by a growable array storing length-prefixed blobs. Supports `Push` (returns index), `Pop`, `Peek`, `Get(index)`, `Len`, `Capacity`, `Reset`, and reports the byte-count meaning of stored entries.
- Must grow when full, must be able to reuse freed space at the front, and must handle both head-before-tail and tail-before-head layouts when allocating additional memory while preserving previously returned indexes for still-valid entries.
- Must reject entries that would exceed a configured maximum capacity, and enforce a minimum initial capacity.
- Reading from an invalid/out-of-range index or from an empty queue returns descriptive errors rather than panicking.
- Grows to accommodate a single value larger than current capacity (and larger than initial capacity).

### Encoding, hashing, utilities
- Entry encoding wraps a payload with a header carrying timestamp, hashed key, and key length, followed by the key bytes and value bytes; decoding must recover the timestamp, hashed key, key string, and value. Round-trip encode/decode must be lossless.
- The FNV64a hasher must produce the standard FNV-1a 64-bit hash for a string key (verified against known values). It must not allocate.
- Utility helpers include power-of-two detection, MB→bytes conversion, and a max helper; `bytesToString` performs a (zero-copy in the default build, safe-copy in the appengine build) conversion.

### HTTP server (`server/*`)
- Handlers implement a small REST API over a `*BigCache`: GET/PUT/DELETE of a key under a versioned path, a clear-cache endpoint, a cache-index handler, and stats endpoints (aggregate and indexed).
- Correct HTTP status codes are required: missing/empty key requests are client errors; a GET for an absent key is 404/not-found; a successful PUT/DELETE returns the appropriate success/created status; PUT that exceeds shard capacity or has an unreadable body returns an error status; invalid delete key is a client error.
- A metrics/logging middleware wraps handlers and records request metrics; a service loader wires routes together.

## Solution decomposition

1. **Config layer** (`config.go`, `utils.go`, `logger.go`, `clock.go`): defaults, `initialShardSize`, `maximumShardSizeInBytes`, `OnRemoveFilterSet`, power-of-two/MB-conversion/max helpers, a default logger, and a system clock returning `time.Now().Unix()`.
2. **Encoding & hashing** (`encoding.go`, `fnv.go`, `hash.go`, `bytes.go`, `bytes_appengine.go`, `entry_not_found_error.go`): entry (de)serialization with header field readers, FNV-1a hasher plus default-hasher constructor, byte↔string conversion, and the not-found sentinel error.
3. **Shard** (`shard.go`, `stats.go`): the locked per-shard map of hashed-key→queue-index over a `BytesQueue`, implementing get/set/append/del/cleanup/reset/len/capacity/stats/metadata and collision handling and eviction. This is the behavioral core.
4. **Cache facade** (`bigcache.go`): validation, construction, background cleanup goroutine, shard routing, callback dispatch selection, and aggregation methods.
5. **Iterator** (`iterator.go`): whole-cache iteration producing `EntryInfo` with valid/invalid-state handling under concurrent updates.
6. **Byte queue** (`queue/bytes_queue.go`): the growable length-prefixed FIFO with reuse and reallocation logic.
7. **Server** (`server/*`): HTTP handlers, middleware, and route/service wiring atop the cache.

A reasonable order: helpers/config → encoding/hash → queue → shard → cache → iterator → server.

## Solution space

- **Byte-to-string conversion**: the default build may use an `unsafe.Pointer` zero-copy conversion, while the appengine build must use a plain `string(b)` copy. Either the unsafe or a `reflect`/`unsafe.String` based approach is acceptable as long as the appengine variant stays copy-safe and both compile under their respective build tags.
- **Copy semantics on read**: any implementation is valid provided `Get` returns data independent of internal buffers.
- **Callback dispatch**: selecting the `onRemove` handler once at construction (as the reference does) or dispatching dynamically per removal are both acceptable, as long as precedence and filtering match the contract.
- **Cleanup goroutine termination**: listening on both the context's `Done` channel and the cache `close` channel is the safe approach; any mechanism that reliably stops the goroutine on both close and context cancellation is fine.
- **Queue reallocation**: the exact copy strategy when head is before/after tail can vary, provided previously returned indexes remain valid and no data is lost or duplicated.
- **Hasher**: any implementation producing standard FNV-1a 64-bit output for the test vectors passes; it need not literally mirror the reference.
- **Server routing**: the specific router/mux and handler structure may differ so long as paths, methods, and status codes match what the server tests expect.
- **Stats storage**: atomic counters vs. lock-protected fields are both acceptable; the parallel same-key-with-stats test only requires correctness under concurrency.

## Known pitfalls

- **Power-of-two validation**: zero and non-powers-of-two must be rejected; `shardMask` is `Shards-1` and only meaningful for powers of two.
- **LifeWindow seconds rounding**: a sub-second life window rounds to 0 seconds; this is only fatal when `CleanWindow > 0`. Do not reject a 0 clean window with a small life window.
- **Life window unit**: the cache stores life window in seconds, not nanoseconds; timestamp comparisons must use consistent second-resolution units.
- **Double close**: `Close` must not close the `close` channel twice or panic; the cleanup goroutine must exit exactly on the close/context signal.
- **Nil value caching**: setting a nil/empty entry must not be conflated with "not found."
- **Collision correctness**: failing to compare the stored key against the queried key returns wrong data on hash collisions; collisions must be counted and surfaced as not-found on read.
- **Returned slice aliasing**: returning a slice that points into the shared queue buffer causes data corruption after subsequent writes — return a copy.
- **Eviction ordering**: `onEvict` must return false (not evict) when the current timestamp precedes the stored timestamp, avoiding underflow on unsigned subtraction.
- **Queue index preservation**: after growing the buffer, indexes handed back to the shard map must still resolve to the same entries; getting this wrong corrupts the shard's key→index map.
- **Queue bounds**: reading an out-of-range, invalid, or empty-queue index must return an error, never panic or index out of range.
- **Header size accounting**: entry header length and shard capacity math must be consistent so `maximumShardSizeInBytes`/`initialShardSize` produce workable sizes and "entry bigger than max shard" is detected.
- **OnRemove unwrapping cost**: the no-op remove handler must avoid unwrapping; the reason handler must respect the filter bitmask before invoking the user callback.
- **Server body/read errors**: a PUT whose body cannot be read, or which exceeds shard capacity, must map to an error status rather than a success.

## Cheat surface

- The provided reference diff is an authoring aid only. Do not treat copying its comment text or exact expressions as the goal — the target is passing behavior, not textual identity.
- Do not hardcode responses to specific test inputs (e.g. returning fixed hash values, fixed stats, or canned HTTP bodies keyed to test literals). Implementations must be general.
- Do not stub out eviction/cleanup by making them no-ops that happen to satisfy a subset of tests; timing-eviction, clean-all, and no-space tests require real behavior.
- Do not weaken validation to always succeed; the validation test asserts specific rejections.
- Do not leave the cleanup goroutine leaking or the `close` channel unclosed to superficially pass; closing tests observe shutdown behavior.
- Avoid satisfying the collision tests by disabling hashing (e.g. constant hash) — that would break sharding and correctness elsewhere.

## Success criteria

- All listed `fail_to_pass` tests across the three packages (core `github.com/allegro/bigcache/v3`, `.../queue`, and `.../server`) compile and pass, including the `Example_custom` runnable example.
- No stubbed placeholder strings or unimplemented panics remain; every previously stubbed function returns correct values.
- The cache builds without error for valid configs and returns errors (not panics) for the invalid configs the validation test exercises.
- Concurrency tests (parallel set/iterate, parallel same-key-with-stats, random append/delete) pass without data races or corruption.
- The byte-queue tests covering push/pop/peek/reset/reuse/reallocation/bounds and max-size limits all pass.
- The server tests covering GET/PUT/DELETE/clear/stats/index handlers, middleware metrics, and service loading all pass with correct status codes.
- The build succeeds under both the default and appengine build-tag variants of the byte-conversion file.