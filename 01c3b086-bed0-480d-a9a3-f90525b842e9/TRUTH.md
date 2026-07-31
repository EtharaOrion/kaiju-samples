# TRUTH.md

## Problem

The repository `Zahgon/SpectralCluster` is a Python re-implementation of the spectral clustering algorithms used for speaker diarization (ICASSP 2018 "Speaker Diarization with LSTM", "Turn-to-Diarize", and the multi-stage streaming clustering paper). Several core modules have been reduced to stubs: the function/method bodies were replaced with `pass` (or left empty), while class definitions, dataclass fields, enum members, signatures, and module wiring remain. Comments/docstrings were also stripped.

The task is to restore the *behavior* of every stubbed function/method so that the full clustering pipeline works end-to-end and the listed test suite passes. The affected modules are:

- `utils.py` — low-level linear-algebra / labeling helpers
- `laplacian.py` — Laplacian matrix construction
- `refinement.py` — affinity-matrix refinement operations
- `constraint.py` — constrained clustering operations
- `custom_distance_kmeans.py` — K-Means with arbitrary scipy distances
- `naive_clusterer.py` — a simple threshold/centroid clusterer
- `fallback_clusterer.py` — fallback clusterer + single-cluster detection
- `autotune.py` — auto-tuning of the `p_percentile` hyper-parameter
- `spectral_clusterer.py` — the top-level `SpectralClusterer.predict` orchestration
- `multi_stage_clusterer.py` — streaming multi-stage clustering + label matching
- `configs.py` — example pre-built clusterer configurations

There is also a stray binary artifact (`spec.pdf.bz2`) tracked in the repo; a correct solution does not depend on it, and removing it is acceptable but not required for tests.

## Behavioral contract

The public entry point is `SpectralClusterer.predict(X)` (optionally with a `constraint_matrix`). `X` is a `(n_samples, n_features)` float array; the return is an integer label array of shape `(n_samples,)`. Labels must be *ordered by first appearance* (the first sample's cluster is 0, the next new cluster is 1, etc.). The number of distinct labels must respect `min_clusters`/`max_clusters`.

Module-level contracts:

- **`utils.compute_affinity_matrix(X)`** — produces a symmetric affinity where the affinity between two rows equals `(cos(x,y)+1)/2`. Rows are L2-normalized before computing the dot products; the result lies in `[0,1]` with `1` on the diagonal.
- **`utils.compute_sorted_eigenvectors(A, descend=True)`** — returns eigenvalues and eigenvectors of `A`, sorted by eigenvalue (descending by default, ascending when requested). Column *i* of the eigenvector matrix corresponds to eigenvalue *i*.
- **`utils.compute_number_of_clusters(eigenvalues, max_clusters, stop_eigenvalue, descend=True, eps)`** — estimates cluster count via the maximal eigen-gap, honoring the `max_clusters` cap and a stopping eigenvalue threshold; also returns the max gap value used (for autotune proxy).
- **`utils.enforce_ordered_labels(labels)`** — relabels an integer array so cluster ids appear in ascending order of first occurrence.
- **`utils.get_cluster_centroids(embeddings, labels)`** — returns per-cluster mean vectors.
- **`utils.chain_labels(...)`** — composes/relabels label sequences; must validate shapes and raise on mismatched/bad shapes (`TestChainLabels::test_bad_shape`).
- **`laplacian.compute_laplacian(affinity, laplacian_type)`** — returns, per enum: `Affinity` → `W` unchanged; `Unnormalized` → `D − W`; `GraphCut` → `D^{-1/2}(D−W)D^{-1/2}`; `RandomWalk` → `D^{-1}(D−W)`, where `D` is the degree diagonal. Guard against division by zero.
- **`refinement`** operations each map an affinity matrix to a refined one:
  - *CropDiagonal*: replace each diagonal element with the row's max off-diagonal value.
  - *GaussianBlur*: apply a Gaussian filter with the configured sigma.
  - *RowWiseThreshold*: for each row, zero out entries below a per-row threshold (a percentile / row-max fraction), optionally binarizing surviving entries or preserving the diagonal, per options.
  - *Symmetrize*: make symmetric via either elementwise max of `A` and `Aᵀ`, or their average.
  - *Diffuse*: replace `A` with `A·Aᵀ` (graph diffusion).
  - *RowWiseNormalize*: divide each row by its maximum (or its sum, per implementation) so scaling is normalized.
- **`constraint`**:
  - `ConstraintOperation.check_input` raises `ValueError` for non-square / non-2D / mismatched affinity vs. constraint shapes.
  - `AffinityIntegration.adjust_affinity` returns elementwise `max` (type `Max`) or average (type `Average`) of affinity and constraint matrix.
  - `ConstraintPropagation.adjust_affinity` implements the closed-form propagation: symmetric-normalize affinity, form `(I − α·Â)^{-1}`, build `(1−α)² · T · C · T`, then combine with the original affinity using positive-mask logic so positive propagated constraints pull affinities up and negative ones push them down.
  - `ConstraintMatrix.compute_diagonals` builds a matrix whose only nonzeros are on the first sub/super-diagonals: `+1` between adjacent turns judged same-speaker (score is 0), `−1` when a speaker-turn score exceeds the threshold, `0` otherwise.
- **`custom_distance_kmeans.run_kmeans`** — with no custom distance, runs scikit-learn `KMeans`; with a custom distance, initializes centroids via k-means++ then runs the local `CustomKMeans` (assign to nearest centroid under the given scipy distance, recompute centroids, iterate to convergence/`max_iter`).
- **`naive_clusterer`** — a simple online/threshold clusterer producing ordered labels; supports an adaptation update path (`test_adaptation`).
- **`fallback_clusterer`** — routes to a fallback (naive or agglomerative) clusterer under configured conditions, and `CheckSingleCluster` decides single-vs-multi via affinity thresholds / GMM-BIC.
- **`autotune`** — `get_percentile_range` returns a linspace of candidate `p_percentile` values determined by min/max/step; `update_percentile_range` mutates state and re-derives the range; `tune` performs a multi-level coarse-to-fine search minimizing a caller-supplied proxy ratio, returning sorted eigenvectors, cluster count, and the best `p_percentile`.
- **`multi_stage_clusterer`** — streaming ingestion of one embedding at a time returning updated full label sequences, with fallback / main / pre-clusterer / compression stages and label deflickering (order-based and Hungarian matching so labels stay consistent across steps).

## Solution decomposition

Implement in dependency order so each layer can be tested against its own suite:

1. **`utils.py`** — foundation for everything else. Affinity, eigen decomposition + sorting, eigengap cluster count, centroid computation, ordered-label enforcement, and label chaining with shape validation.
2. **`laplacian.py`** — the four Laplacian variants keyed by the `LaplacianType` enum, using degree matrix arithmetic with zero-safe inverses.
3. **`refinement.py`** — the individual refinement operations, each honoring `RefinementOptions` fields (sigma, percentile, thresholding type, soft multiplier, symmetrize type). `RowWiseThreshold` is the subtle one (row-max vs percentile, binarization, diagonal preservation).
4. **`constraint.py`** — input validation, affinity integration, constraint propagation closed form, and constraint-matrix construction from turn scores.
5. **`custom_distance_kmeans.py`** — the `CustomKMeans` assign/update loop plus the `run_kmeans` dispatcher (sklearn vs custom).
6. **`naive_clusterer.py`** and **`fallback_clusterer.py`** — simpler clusterers and the single-cluster decision helpers used as fallbacks by the main clusterer.
7. **`autotune.py`** — percentile range generation and the coarse-to-fine tuning loop that calls back into the clusterer's per-percentile evaluation.
8. **`spectral_clusterer.py`** — orchestrate: build affinity (or use provided), optionally apply constraints before/after refinement, run refinement sequence, compute Laplacian, eigen-decompose, estimate cluster count (or autotune), optionally reduce dimension / row-renormalize spectral embeddings, run K-Means (custom distance), and produce ordered labels. Integrate the fallback and single-cluster conditions.
9. **`multi_stage_clusterer.py`** — label-matching utilities (the `TestMatchLabels` cases) and the streaming stage machine.
10. **`configs.py`** — no algorithmic logic beyond assembling `SpectralClusterer`/refinement/autotune/constraint objects with the documented parameter values for the ICASSP2018 and Turn-to-Diarize presets.

## Solution space

Multiple correct routes exist; do not penalize deviations that preserve behavior:

- **Linear algebra style**: eigen decomposition may use `numpy.linalg.eig`/`eigh` or `scipy`; symmetric-matrix routines are acceptable as long as sorting semantics and returned shapes match tests.
- **Affinity computation**: normalizing rows then dotting, or computing cosine via `scipy.spatial.distance`, are equivalent provided the `(cos+1)/2` mapping and diagonal-of-1 hold.
- **Refinement `RowWiseNormalize`**: dividing each row by its max or by a norm are both plausible; the correct one is whichever makes `TestRowWiseNormalize` pass — match the expected normalization exactly.
- **`Symmetrize`**: max-based vs average-based must be selected by the option enum; both branches must exist.
- **Constraint propagation**: the positive/negative combination can be written with masks, `np.where`, or clipping, as long as positive constraints raise and negative constraints lower affinities per the closed form.
- **CustomKMeans**: centroid initialization can be random or k-means++-seeded; convergence can be by tolerance and/or `max_iter`. Determinism (seeding) matters where tests assert specific labels — use fixed random state to reproduce expected clusterings.
- **Cluster-count / eigengap**: descending vs ascending eigenvalue handling both acceptable if the `descend` flag is respected consistently.
- **Multi-stage label matching**: Hungarian assignment via `scipy.optimize.linear_sum_assignment` or an equivalent optimal-matching implementation; order-based deflickering via first-appearance mapping.
- **Fallback single-cluster detection**: threshold-based, std-based, neighbor-based, all-affinity, and GMM-BIC variants each map to a `SingleClusterCondition`; only the branches exercised by tests must be exactly correct.
- Removing `spec.pdf.bz2` is optional and orthogonal to correctness.

## Known pitfalls

- **Label ordering**: forgetting to enforce first-appearance ordering causes off-by-permutation failures across `spectral_clusterer_test`, `configs_test`, and `multi_stage_clusterer_test`. Always pass final labels through the ordered-relabel step.
- **Diagonal handling in refinement**: `CropDiagonal` must use the row's max *off-diagonal* value (not including the diagonal), and `RowWiseThreshold` with `preserve_diagonal` must keep the diagonal intact after thresholding.
- **Percentile vs row-max thresholding**: the two `ThresholdType` branches compute different per-row cutoffs and different soft-multiplier scaling of surviving entries; conflating them breaks `test_3by3_matrix_percentile` / `test_3by3_matrix_row_max` / `test_binarization`.
- **Degree zero / division**: Laplacian normalization and constraint propagation must guard against zero degrees (add an epsilon or handle explicitly) to avoid NaNs.
- **Eigenvalue sort direction**: mixing ascending/descending between `compute_sorted_eigenvectors` and `compute_number_of_clusters` yields wrong cluster counts; keep the `descend` semantics coherent.
- **Constraint application timing**: `apply_before_refinement` determines whether the constraint operation runs before or after the refinement sequence; getting this backwards breaks the constraint-propagation and affinity-integration clusterer tests.
- **Autotune loop termination**: must halt when the range collapses to a single point or the step drops below the minimum step, and must remember the globally best percentile/eigenvectors/cluster count across levels — not just the last level.
- **KMeans determinism**: non-seeded initialization produces unstable labels; tests expect reproducible cluster assignments.
- **`chain_labels` shape validation**: must raise (not silently proceed) on malformed inputs.
- **`compute_diagonals` sign logic**: `+1` for same-speaker adjacency (score exactly 0) vs `−1` for above-threshold turn scores vs `0` otherwise — the score==0 vs score>threshold vs in-between cases are distinct.
- **Constraint check_input**: must raise `ValueError` for each invalid-shape case; the constraint tests and callers rely on these guards.
- **Single-cluster path**: when `min_clusters=1`, the affinity-threshold single-cluster decision must short-circuit before spectral clustering; otherwise the single-cluster tests fail.

## Cheat surface

The following would make tests green without genuinely implementing the specification and must be treated as failing the intent:

- Hard-coding the specific expected label arrays / matrices from the test files keyed on input shapes (e.g., returning a canned answer for a `6x2` or `1000x6` input).
- Detecting test-specific magic constants and branching on them rather than computing results generically.
- Stubbing functions to return their input unchanged or to return zeros where the test happens to tolerate it, while other (unlisted but logically required) behaviors remain broken.
- Reproducing the reference source verbatim from memory rather than implementing the described behavior — correctness must come from the algorithms, not from copying.
- Suppressing/rerouting the required `ValueError` validations so error-path tests pass trivially without real checks.
- Monkeypatching test doubles or seeding RNG in a way that only matches asserted outputs for the exact test fixtures.

A legitimate solution computes results purely from the mathematical definitions above and works for arbitrary inputs of the documented shapes.

## Success criteria

- All listed `fail_to_pass` tests across `autotune_test`, `configs_test`, `constraint_test`, `custom_distance_kmeans_test`, `fallback_clusterer_test`, `laplacian_test`, `multi_stage_clusterer_test`, `naive_clusterer_test`, `refinement_test`, `spectral_clusterer_test`, and `utils_test` pass.
- No previously passing tests regress (no `pass_to_pass` regressions).
- `SpectralClusterer.predict` returns an ordered integer label vector of correct length for arbitrary valid `X`, honoring `min_clusters`/`max_clusters`, laplacian type, refinement sequence, custom distance, autotune, constraint, and fallback/single-cluster options.
- Each refinement, laplacian, constraint, and utility function behaves per the Behavioral contract for arbitrary inputs, including raising `ValueError` on the specified invalid inputs.
- The pre-built configurations in `configs.py` construct working clusterers that reproduce the ICASSP2018 and Turn-to-Diarize behaviors exercised by `configs_test`.
- Multi-stage streaming clustering returns consistent, deflickered label sequences as each embedding is fed in.