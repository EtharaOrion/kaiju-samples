# TRUTH.md

## Problem

The `datasketch` package has been reduced to stubs across its core probabilistic-data-structure modules and its CI workflow files. Every public class body has been gutted (methods `pass` or raise), so imports may succeed but almost all runtime behavior is missing. The task is to re-implement the library so that the enumerated `fail_to_pass` tests covering MinHash (including permutation "schemes" and a GPU-accelerated path), HyperLogLog / HyperLogLog++, LeanMinHash, b-bit MinHash, WeightedMinHash, MinHashLSH (in-memory + Redis + Cassandra integration), LSHForest, LSHEnsemble, LSHBloom, HNSW, and the async LSH variants all pass.

The work spans two categories:
- **Python library modules** under `datasketch/` (and `datasketch/aio/`, `datasketch/experimental/aio/`) — the substantive behavior.
- **GitHub Actions workflow YAML** under `.github/workflows/` — infrastructure files that do not affect the pytest suite but were part of the stubbed set.

The specification here concentrates on the library behavior, since that is what the tests exercise.

## Behavioral contract

Each data structure must satisfy the contract implied by its test module. Key observable behaviors:

**MinHash (`minhash.py`)**
- Construction with `num_perm`, optional `seed`, optional `hashfunc`, optional pre-supplied `hashvalues`/`permutations`, and a **permutation scheme** selector (default scheme is `affine32`; an `affine64` scheme uses the full 64-bit range).
- `update(value)` and batched `update_batch(values)` fold hashed tokens into the running minimum register; byte tokens must be accepted directly.
- Registers store per-permutation minimums; empty registers use a scheme-specific maximum sentinel; the register dtype matches the scheme width.
- `jaccard(other)`, `count()` (approx cardinality via number of non-max registers), `is_empty()`, `merge(other)` (elementwise min), `union(*mhs)` classmethod, `copy()`, equality (`__eq__` compares seed, scheme, and registers), and `__hash__` consistency where applicable.
- `bulk(...)` / a generator helper produce many MinHashes and must propagate the chosen scheme.
- Scheme correctness guards: a `hashfunc` or supplied `hashvalues` whose outputs fall outside the scheme's valid integer range must raise; python ints must convert exactly; operations mixing two MinHashes built under different schemes must be **refused** (raise), as must an invalid scheme name. The default `hashfunc` must match the scheme's width.

**GPU MinHash path (`minhash.py`, exercised by `test_minhash_gpu.py`)**
- A GPU/batch acceleration mode with at least three settings: force-on ("always"), auto ("detect"), and CPU fallback. "Always" mode must raise a clear error when no GPU device is available. "Detect" mode must yield results **identical** to the CPU path. The GPU code path, when run on CPU (a shim), must produce the same registers for all schemes and must detect/reject a wrong cache dtype. Pickling must remain portable (a GPU-mode instance unpickles and behaves on a CPU-only host).

**HyperLogLog / HyperLogLog++ (`hyperloglog.py`)**
- Construction by precision `p` or by `hashfunc`; construction directly from an existing register array (`init_from_reg` semantics). Registers initialized to zero → `is_empty()`.
- `update`, `count()` cardinality estimation (the `++` variant applies bias correction giving accurate small- and large-cardinality estimates), `merge`, `union` (classmethod), `copy`, equality, byte-order-independent serialize/deserialize round-trip, and pickle round-trip.

**LeanMinHash (`lean_minhash.py`)**
- An immutable, memory-lean projection built from a MinHash; supports `jaccard`, `count`, `is_empty`, `merge`, `union`, hashing, equality, pickle, and a compact `bytesize`/`serialize`/`deserialize` (round-trips including explicit byteorder).

**b-bit MinHash (`b_bit_minhash.py`)**
- Built from a MinHash truncated to `b` bits; supports `jaccard` estimate, equality, pickle, and a `bytesize` reflecting the compressed representation.

**WeightedMinHash (`weighted_minhash.py`)** — supports the LSH/forest weighted variants (`__H` byte-key derivation, jaccard).

**MinHashLSH (`lsh.py`) and storage (`storage.py`)**
- Banding by `(threshold, num_perm)` or explicit `params=(b, r)`; `insert(key, minhash)`, `query(minhash)`, `remove(key)`, `__contains__`, counts helpers (`get_counts`, subset counts), insertion/deletion sessions (context managers with buffering), pickle.
- The `_H` hashing of a band slice into a byte key must be stable/deterministic.
- Storage abstraction with in-memory dicts and a Redis backend selectable via `storage_config`; buffered query must match unbuffered candidates. Non-bytes keys raise where the backend requires bytes.

**LSHForest / LSHEnsemble / LSHBloom** — build/index, `query`, pickle, Redis-backed index; ensemble uses partitioning (`lshensemble_partition.py`). Bloom variant (`lsh_bloom.py`) has a `BloomTable` (insert/query/save) and detects scheme mismatch on load; supports in-memory save.

**HNSW (`hnsw.py`)**
- A mutable navigable-small-world index behaving like an ordered mapping: `insert`/`__setitem__`, `search`/query returning nearest neighbors under a supplied distance function (Euclidean, Jaccard, MinHash-Jaccard), `update`, `upsert`, `copy`, `merge`, `clear`, `pickle`, `popitem` (first/last), and both **soft** and **hard** removal with `pop` + `clean`. A configuration variant maintains **reversed edges** and must satisfy the same tests.

**Async LSH (`aio/lsh.py`, `aio/storage.py`, `experimental/aio/lsh.py`)** — async initialization via `await`, async storage creation/close, batch_size property, insert/query/remove mirroring the sync semantics (not directly in the listed failing tests but must import cleanly).

## Solution decomposition

1. **MinHash core + schemes.** Introduce a scheme registry mapping scheme names → (integer width/dtype, modulus/mersenne prime, empty sentinel, default hashfunc width, permutation-generation parameters). Implement register storage, update/update_batch, set-similarity ops, equality/pickle, and strict range validation. Ensure copy/merge/union/bulk thread the scheme through and refuse cross-scheme operations.
2. **GPU acceleration shim.** Add a mode enum and a device-detection helper; a vectorized batch-update kernel with a CPU fallback that is bit-for-bit equivalent; guard cache dtype; keep pickled state device-independent.
3. **HyperLogLog family.** Registers + rank computation, cardinality estimator, and the `++` subclass with bias/linear-counting correction; serialization and init-from-registers.
4. **Lean / b-bit / weighted MinHash.** Derive compact forms from MinHash; implement serialization and similarity estimators.
5. **Storage layer.** Ordered and unordered storage abstractions with dict and Redis backends; random-name helper; batching support. Async counterparts.
6. **LSH family.** Banding math, `_H` key hashing, session buffering, counts, and backend wiring shared with forest/ensemble/bloom; partitioning for ensemble; Bloom table with save/load and scheme-mismatch detection.
7. **HNSW.** Layered graph with entry point, level assignment, greedy search + neighbor selection, ordered-mapping semantics, soft/hard delete + cleanup, merge/copy/pickle, and the reversed-edge bookkeeping variant.
8. **Async LSH.** Async init/close, storage creation, and CRUD mirroring sync semantics.
9. **Workflow YAML.** Recreate CI definitions (build, checks, doc, pypi, per-backend test matrices). These are inert w.r.t. pytest.

## Solution space

- **Scheme representation** may be a dict/registry, dedicated classes, or an enum — any is acceptable provided the default is `affine32`, `affine64` uses the full 64-bit range, dtypes/sentinels differ per width, and cross-scheme ops raise.
- **GPU backend** may target CuPy/Numba/Torch or a pure-numpy vectorized "gpu-style" path; tests run on CPU, so the only hard requirements are: identical results to the scalar CPU path, an explicit raise for forced-GPU-without-device, dtype-cache validation, and portable pickling. The detection mechanism (env var, import probe, capability flag) is unconstrained.
- **HyperLogLog++ correction** may use published bias tables, empirical thresholds, or an equivalent estimator, as long as small- and large-cardinality accuracy tests pass.
- **HNSW neighbor selection** may use the simple or heuristic candidate-pruning strategy; reversed-edge tracking may be a separate adjacency map or derived on demand — both must pass identical behavioral tests.
- **Storage backends**: Redis wiring may use `redis-py` sync/async clients; in-memory backend may be plain dicts or `defaultdict`. Serialization of keys (prepickle) may default based on backend type.
- **Serialization formats** are free to choose byte layout as long as round-trips (including explicit byteorder for LeanMinHash) are self-consistent and produce equal objects.
- **Workflow YAML** contents are essentially unconstrained (versions, action refs, matrix entries) and are not graded by the test suite.

## Known pitfalls

- **Register dtype vs. scheme width.** Using a fixed 64-bit dtype for a 32-bit scheme (or vice versa) breaks the empty sentinel, `dtype`, and range-validation tests. The sentinel for an empty register must equal the scheme's maximum value, not a generic max-int.
- **Silent cross-scheme mixing.** `merge`/`union`/`__eq__`/`jaccard` across differing schemes must raise, not coerce or silently compare — a common oversight.
- **Range validation ordering.** Out-of-range `hashfunc` output and out-of-range supplied `hashvalues` must raise at the point of use/construction; exact conversion of python ints must not overflow.
- **`__eq__` must include scheme and seed**, not just registers, or `test_eq_differs_across_schemes` fails.
- **GPU "always" without device must raise**, and "detect" must not diverge numerically from CPU — off-by-one in the batch reduction shows up here. Pickles must not embed device handles.
- **HyperLogLog++ bias correction** applied unconditionally (ignoring the linear-counting/large-range thresholds) yields inaccurate estimates at the extremes.
- **LeanMinHash byteorder**: deserialize must honor the byteorder recorded/param, or the byteorder test fails on big/little mismatch.
- **LSH `_H` determinism**: hashing must be stable across processes (avoid Python's salted `hash()` for band keys); use a fixed digest. Buffered query must return the same candidate set as direct query.
- **HNSW soft vs. hard removal**: soft-remove must keep the node reachable-but-marked until `clean`, while hard-remove must repair the graph immediately; `popitem_first`/`popitem_last` ordering and reversed-edge consistency after removal are frequent failure points.
- **Storage `batch_size` setter** must raise if the index is uninitialized rather than silently no-op.
- Do not let optional-dependency imports (redis, cassandra, motor, cupy) fail at module import time when the backend is unused — guard them so in-memory tests still import.

## Cheat surface

- **Do not** hard-code expected values keyed to specific test inputs (e.g. returning a fixed cardinality, fixed jaccard, or a canned neighbor list). Estimators must be computed from register state; the tests use randomized/varied inputs and statistical tolerances.
- **Do not** special-case a particular scheme name to pass while leaving others broken; all enumerated schemes must be genuinely implemented.
- **Do not** stub the GPU path to always take the CPU branch while claiming device availability — the "always-without-device raises" and "shim rejects wrong cache dtype" tests probe the real branch.
- **Do not** make `remove`/`clean`/`popitem` merely mutate a size counter without repairing the HNSW graph; subsequent `search` correctness is tested.
- **Do not** bypass serialization by pickling whole objects where a compact `serialize`/`deserialize` byte-size contract is asserted (`test_bytesize`, `test_serialize`).
- Equality/`is_empty` must reflect real state, not always-True/always-False.
- Reproducing the golden implementation's incidental comments or CI YAML verbatim is unnecessary and not the goal; correct behavior is.

## Success criteria

- All listed `fail_to_pass` tests pass: the full `test_hnsw.py` matrix (base, reversed-edges, Jaccard, MinHash-Jaccard variants) for clear/copy/merge/pickle/popitem/search/soft+hard-remove/update/upsert; `test_hyperloglog.py` (HLL, HLL++, and specific small/large-card estimation); `test_lean_minhash.py`; `test_minhash.py` and `test_minhash_schemes.py` (all scheme-basics cases) and `test_minhash_gpu.py`; `test_lsh.py`, `test_lshbloom.py`, `test_lshensemble.py`, `test_lshforest.py`; and the Redis/Cassandra `test_integration.py` cases (in their target environments).
- No previously importable module regresses; optional-backend guards keep the in-memory suite importable without redis/cassandra/mongo/gpu installed.
- Library public API (`from datasketch import MinHash, HyperLogLog, MinHashLSH, LeanMinHash, WeightedMinHash, MinHashLSHEnsemble, MinHashLSHForest`) imports successfully.
- The `.github/workflows/*.yml` files are present and valid YAML; their exact content is not verified by the test suite.