# TRUTH.md

## Problem

The repository `Zahgon/neat-python` is a Python implementation of the NEAT
(NeuroEvolution of Augmenting Topologies) algorithm. Many modules across the
`neat/` package have had their function/method bodies replaced with `pass`
stubs (and one CI workflow file removed). The task is to re-implement these
stubs so that the full NEAT toolchain works end-to-end: activation and
aggregation function registries, gene attribute types, genes, genomes,
network phenotypes (feed-forward, recurrent, CTRNN), speciation, reproduction,
stagnation, statistics, reporting, checkpointing, config parsing/round-trip,
parallel evaluation, innovation tracking, and JSON export.

The definition of "correct" is: the listed `fail_to_pass` tests all pass, and
no previously-passing behavior regresses. The behavior must match the classic
neat-python semantics that the test-suite encodes.

## Behavioral contract

The implementation must satisfy the following observable behaviors, grouped by
subsystem. (Exact numeric constants matter only where tests pin them.)

### Activation functions (`neat/activations.py`)
- Provide the standard per-scalar activation functions. Tests pin specific
  input→output pairs, so the following exact forms are required:
  - `sigmoid`: logistic on `5*z` clamped to `[-60, 60]`.
  - `tanh`: `tanh(2.5*z)` with argument clamped to `[-60, 60]`; outputs
    `tanh(-2.5)`, `0`, `tanh(2.5)` at `z = -1, 0, 1`.
  - `sin`: `sin(5*z)` with argument clamped to `[-60, 60]`.
  - `gauss`: `exp(-5*z^2)` with `z` clamped to `[-3.4, 3.4]`; value `1.0` at 0.
  - `relu`: `z` if `z>0` else `0`.
  - `softplus`: `0.2*log(1+exp(5*z))`, arg clamped to `[-60, 60]`.
  - `identity`: returns `z` unchanged.
  - `clamped`: clamp to `[-1, 1]`.
  - `inv`: reciprocal, returning `0.0` when division raises `ArithmeticError`.
  - `log`: natural log of `max(1e-7, z)`.
  - `exp`: `exp(z)` with `z` clamped to `[-60, 60]`.
  - `abs`, `hat` (`max(0, 1-|z|)`), `square` (`z**2`), `cube` (`z**3`).
  - (Also `elu`, `lelu`, `selu` for completeness.)
- `ActivationFunctionSet.get(name)` returns the registered function, and raises
  `InvalidActivationFunction` for unknown names.
- `ActivationFunctionSet.is_valid(name)` returns a bool membership check.
- Adding a non-callable or wrong-arity function raises `InvalidActivationFunction`.

### Aggregation functions (`neat/aggregations.py`)
- `sum`, `product` (fold with multiplication, identity `1.0`), `max`, `min`,
  `maxabs` (element with largest absolute value), `median`, `mean`.
- The reducing/statistical aggregations must tolerate an **empty iterable** by
  returning `0.0` (orphaned nodes with no inputs).
- `AggregationFunctionSet.get` raises `InvalidAggregationFunction` on unknown
  name; `is_valid` returns bool; bad additions raise the invalid-function error.

### Gene attributes (`neat/attributes.py`)
- `BaseAttribute` builds per-instance config item copies (must not share mutable
  config state across instances), and derives config item names of the form
  `"{attr_name}_{item}"`. `get_config_params` returns `ConfigParameter`s.
- `FloatAttribute`: `clamp` to `[min,max]`; `init_value` supports gaussian/normal
  (clamped gauss) and uniform init (bounded by `mean ± 2*stdev` intersected with
  min/max), raising `RuntimeError` on unknown `init_type`; `mutate_value` uses a
  single random draw where `r < mutate_rate` → clamped additive gaussian, else
  `r < mutate_rate + replace_rate` → re-init, else unchanged; `validate` raises
  `RuntimeError` when `max < min`.
- `IntegerAttribute`: analogous, with integer clamp, `randint` init, and rounded
  gaussian mutation.
- `BoolAttribute`: `init_value` maps textual truthy/falsey strings, and
  `random`/`none` → 50/50; unknown default raises `RuntimeError`. `mutate_value`
  adjusts the effective rate by `rate_to_false_add`/`rate_to_true_add` and, when
  triggered, returns a fresh random bool (mutation may keep the same value).
  `validate` rejects unrecognized defaults.
- `StringAttribute`: `init_value` returns a random option for `none`/`random`
  default, else the default; `mutate_value` picks a random option with prob
  `mutate_rate`; `validate` rejects a default not in options.
- Zero mutation rate ⇒ value never changes; mutation rate of one ⇒ always
  mutates/replaces per the rate split.

### Config (`neat/config.py`, `test_config*`)
- Loading a nonexistent config file raises an error.
- Unknown options, missing/invalid default activation, and other malformed
  sections raise the appropriate errors (`RuntimeError`/lookup errors) as the
  tests expect.
- Config `save`/round-trip must reproduce an equivalent, re-loadable config;
  saving to an invalid target raises.

### Genes (`neat/genes.py`)
- `BaseGene`/`DefaultNodeGene`/`DefaultConnectionGene`: `copy` preserves key
  (and connection `innovation`) plus all attribute values; `crossover` requires
  matching keys (and matching innovation for connection genes), and inherits each
  attribute randomly from one of the two parents; `distance` combines attribute
  differences plus discrete activation/aggregation mismatches, scaled by a
  coefficient; node `__init__` requires an int key; `__lt__` compares by key and
  rejects mismatched key types; `__str__` includes key and attribute names.

### Genome / networks
- `DefaultGenome` supports create/mutate/crossover/distance, node & connection
  mutation, and the **75% disable rule**: when crossing two parents where a
  matching connection gene is disabled in either parent, offspring inherit the
  disabled state with 75% probability (and enabled otherwise); a connection
  enabled in both parents is never spuriously disabled. The rule is applied after
  attribute inheritance and preserves other attributes.
- Feed-forward network (`neat/nn/feed_forward.py`): correct topological layering,
  activation of nodes in order, and `create` from genome that prunes unused nodes.
  Unconnected/output-only cases behave sensibly.
- Recurrent network (`neat/nn/recurrent.py`) and CTRNN produce deterministic,
  reset-able trajectories; CTRNN `advance` validates input length; CTRNN
  `create` prunes and builds the expected node/connection structure. Two-neuron
  dynamics match expected integration.

### Population / evolution (`neat/population.py`, reproduction, species, stagnation, statistics, reporting)
- Fitness evaluation: fitness function is called each generation with correct
  arguments; best genome is tracked across generations; not assigning fitness (or
  setting it to `None`) raises; fitness criterion `max`/`min`/`mean` selects the
  reported best correctly; invalid criterion raises.
- Termination: threshold reached stops evolution; when no fitness termination is
  configured, a generation limit is required and all generations run.
- Population size is maintained across generations.
- **Complete extinction**: when all species die, either raise a
  `CompleteExtinctionException` (its own exception type/inheritance/message) or,
  when `reset_on_extinction` is enabled, rebuild a fresh population (new genomes),
  reset the innovation tracker, preserve the best genome/statistics as tests
  require, and continue the generation counter. Reporters are notified and receive
  correct state; works with checkpointer, elitism zero, small populations,
  negative/zero fitness, fitness threshold, and repeated extinctions.

### Innovation tracking (`neat/innovation.py`)
- Deterministic assignment of innovation numbers to structural mutations, with a
  monotonic counter that continues correctly across checkpoint restore.

### Checkpointing (`neat/checkpoint.py`)
- Saves a **gzip-compressed pickle** file containing population, species set,
  generation number, RNG state, innovation tracker, and genome indexer state.
- `restore_checkpoint` reconstructs a `Population` that continues evolution such
  that a resumed run matches an uninterrupted run: preserves generation number,
  fitness values, genome keys/structure, species count/membership, population
  size, random state, and continues genome indexer and innovation numbers with no
  ID collisions. Restore works with the same or a new config.

### Export (`neat/export/exporters.py`, `json_format.py`)
- Export feed-forward, recurrent, CTRNN, and IZNN networks to a JSON structure
  containing well-formed, validatable node and connection entries, correct numeric
  precision, optional metadata, and correct detection/marking of built-in vs
  custom activation and aggregation functions. Invalid network type raises;
  export-to-file works; output is well-formatted JSON.

### Parallel (`neat/parallel.py`)
- Parallel evaluator distributes genome evaluation across workers and writes back
  fitness values equivalent to serial evaluation.

## Solution decomposition

Sub-goals, roughly in dependency order (leaves first — many tests only need the
lower layers):

1. **Math utilities** (`math_util.py`): `mean`, `median`/`median2`, variance/
   stdev helpers used by aggregations and statistics.
2. **Activation & aggregation registries**: implement the scalar/iterable
   functions and the get/is_valid/validate error paths.
3. **Attributes**: name derivation, config-param generation, and the
   init/mutate/clamp/validate logic for float/int/bool/string.
4. **Config**: parsing, validation, and save/restore round-trip.
5. **Genes**: copy/crossover/distance/comparison/str.
6. **Graphs** (`graphs.py`): `creates_cycle`, `required_for_output`,
   `feed_forward_layers` used by phenotype construction and genome mutation.
7. **Genome**: structure, mutation, crossover with the disable rule, distance.
8. **Innovation tracking**.
9. **Phenotypes**: feed-forward, recurrent, CTRNN, (IZNN if present).
10. **Speciation, stagnation, reproduction, statistics, reporting**.
11. **Population**: the `run`/generation loop, best-genome tracking, termination,
    and extinction handling.
12. **Checkpointer**: gzip-pickle save + restore that rebuilds a runnable
    population.
13. **Parallel evaluator**.
14. **Export** (exporters + json_format).
15. **CI workflow file** (`.github/workflows/tests.yml`) — not exercised by tests
    but part of the stubbed set; a minimal valid GitHub Actions workflow suffices.

## Solution space

Multiple correct routes exist; do not penalize deviations that preserve behavior:

- **Numeric activation forms**: only functions whose exact input/output pairs are
  asserted (tanh, sin, gauss, softplus, relu, clamped, inv, log, exp, abs, hat,
  square, cube, identity) must match those forms. `elu`/`lelu`/`selu` are not
  pinned and any reasonable definition is acceptable.
- **Empty-aggregation handling**: returning `0.0` on empty input is what tests
  require; the internal branch style (guard vs. try/except) is free.
- **Attribute mutation**: whether mutate/replace share one `random()` draw or use
  two independent draws is an implementation choice **as long as** the boundary
  behaviors tests check hold (rate 0 ⇒ never change; rate 1 ⇒ always change;
  mutation-vs-replacement partition). The single-draw approach used by classic
  neat-python is the safest match; if using two draws, ensure the pinned
  statistical tests still pass.
- **Bool mutation returning a fresh random bool** (may keep same value) is
  required semantics — do not implement it as a guaranteed flip.
- **Disable rule**: the 75% probability must be applied; equivalent formulations
  (sampling once, comparing `random() < 0.75`, etc.) are fine. Only apply it when
  the gene is disabled in at least one parent; never disable a both-enabled gene.
- **Checkpoint payload**: any serialization that round-trips all required state
  via gzip+pickle is acceptable; tests assert the file is a gzipped pickle and
  that a restored run matches an uninterrupted run, so the *set* of preserved
  state (generation, RNG, innovation counter, indexer, species, fitness) matters
  more than exact tuple layout.
- **Export format**: exact JSON key names must match what the export tests assert,
  but helper structuring is free.
- **Feed-forward construction**: any correct topological ordering / pruning that
  yields the same outputs is valid.
- **CI workflow contents** are essentially unconstrained (no test loads it).

## Known pitfalls

- **Shared mutable config across attribute instances**: `_config_items` must be
  deep-copied per instance; sharing the class-level dict corrupts per-gene
  defaults (this is exactly the bug the reference guards against).
- **Argument scaling/clamping in activations**: forgetting the `2.5`, `5.0`
  scale factors or the clamp bounds will fail the pinned value tests. `gauss`
  clamps `z` (not the scaled argument) to `[-3.4, 3.4]`.
- **Empty iterable aggregations**: `max([])`/`min([])`/`median([])` raise; must
  short-circuit to `0.0`.
- **`product_aggregation` identity**: fold must start at `1.0` and multiply, not
  `sum`.
- **Mutate/replace ordering**: check `mutate_rate` first, then the combined
  `mutate_rate + replace_rate` threshold; swapping these changes the probability
  split and fails statistical tests.
- **Bool/String validate**: must raise `RuntimeError` on invalid defaults/options,
  not silently accept.
- **Disable rule timing**: apply *after* attribute inheritance; applying before,
  or applying to genes enabled in both parents, breaks the disable-rule tests.
- **Innovation counter continuity after restore**: restoring must not reset the
  innovation/indexer counters, or new nodes/connections collide with old IDs.
- **RNG state on checkpoint**: to make a resumed run bit-identical to an
  uninterrupted run, the random state must be captured and restored.
- **Extinction semantics**: raise `CompleteExtinctionException` when
  `reset_on_extinction` is false; otherwise rebuild — do not silently continue
  with zero genomes. Reporter notification order and innovation reset are checked.
- **`get`/`is_valid` error types**: registries must raise the *specific* invalid
  function exception classes, not generic `KeyError`.
- **Node gene `__lt__` / `__init__`**: must reject mismatched key types and
  require int keys (tests assert the raised errors).
- **Connection crossover**: must require matching innovation numbers (raise on
  mismatch) and preserve innovation/key in the child.

## Cheat surface

Watch for solutions that satisfy tests without implementing the real algorithm:

- **Hard-coding pinned activation outputs** for the specific test inputs
  (e.g. returning literals for `z=-1,0,1`) instead of the general formula.
- **Special-casing test fixtures** in genome/population code (detecting known
  genome keys, population sizes, or seeds) to fabricate expected results.
- **Faking checkpoint restore** by returning the live in-memory population object
  instead of genuinely deserializing a gzipped pickle from disk — the "file is a
  gzipped pickle" and "resumed matches uninterrupted" tests should catch this,
  but verify a real file is written/read.
- **Stubbing extinction** to never actually exhaust species, or catching the
  exception internally so the raise-path tests can't observe it.
- **Export that emits a canned JSON blob** rather than reflecting the actual
  network's nodes/connections and correctly classifying built-in vs custom
  functions.
- **Disable rule implemented as a constant** (always/never disable) that happens
  to pass a subset of the probabilistic checks — the mathematical-model-accuracy
  test measures the ~75% rate over many samples.
- **Bool mutation as guaranteed flip** to pass a "changes value" test while
  failing the "returns random value" semantics.
- Overly permissive `is_valid`/`validate` that never raise, passing positive
  tests but failing the negative (bad-config / bad-add) tests.

## Success criteria

- All listed `fail_to_pass` tests pass:
  - `tests/test_activation.py`, `tests/test_aggregation.py`,
    `tests/test_attributes.py` (Float/Integer/Bool/String/EdgeCases),
  - `tests/test_config.py`, `tests/test_config_save_restore.py`,
  - `tests/test_genes.py` (node & connection gene behavior),
  - `tests/test_feedforward_network.py`, `tests/test_ctrnn.py`,
  - `tests/test_disable_rule.py`, `tests/test_extinction.py`,
  - `tests/test_fitness_evaluation.py`, `tests/test_checkpoint.py`,
  - `tests/test_export.py`.
- No regressions in any tests that were already passing.
- The registries raise the correct specific exception types on invalid
  functions/config; attributes honor the zero-rate/full-rate boundary semantics;
  the disable rule reproduces ~75% probability statistically; checkpoints are
  genuine gzipped pickles whose restored runs are indistinguishable from
  uninterrupted runs; extinction either raises the dedicated exception or performs
  a real population reset per configuration.
- Implementations are general (formula/algorithm driven), not tailored to the
  specific literal values or fixtures used in the tests.