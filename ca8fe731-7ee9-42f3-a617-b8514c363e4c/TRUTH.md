## Problem

The `go.uber.org/goleak` package (in this repository under `Shivansh9411/goleak`) is a library for detecting leaked goroutines in Go tests. Three source files have been reduced to stubs whose functions return zero values or `nil` with placeholder bodies (`_ = "STUB: not implemented"`). The task is to implement the real behavior in:

- `leaks.go` — the core leak-finding logic (`Find`, `VerifyNone`, `filterStacks`).
- `options.go` — the `Option` mechanism, built-in stack filters, retry logic, and the `opts` aggregator.
- `testmain.go` — `VerifyTestMain`, the `TestMain`-integration entry point.

These functions depend on an already-implemented helper package `internal/stack`, which exposes a `stack.Stack` type and functions `stack.Current()` and `stack.All()`. The `internal/stack` tests are listed among the tests that must pass, but they exercise the (already-working) stack package; implementing the stubs must not break the ability to build/run them. The primary behavioral goal is that the top-level `goleak` tests (`TestFind`, `TestVerifyNone`, etc.) pass.

## Behavioral contract

Assume `stack.Stack` provides at least these observable accessors: `ID() int`, `State() string`, `FirstFunction() string`, `CreatedBy() string`, and `HasFunction(name string) bool`. Assume `stack.Current()` returns the current goroutine's stack and `stack.All()` returns all goroutines' stacks.

**`Find(options ...Option) error`**
- Records the *current* goroutine's ID before scanning so it is never reported as a leak.
- Builds an `opts` from the provided options.
- Rejects options that are meaningless for `Find`: if a `Cleanup` function was supplied, it must return an error stating Cleanup can only be passed to `VerifyNone` or `VerifyTestMain`; if `RunOnFailure` was supplied, it must return an error stating RunOnFailure can only be passed to `VerifyTestMain`. (Exact wording is matched by tests — see pitfalls.)
- Repeatedly collects `stack.All()`, filters it, and if zero goroutines remain returns `nil` (success). Otherwise it consults the retry policy; the loop index passed to the retry policy starts at 0 and increments each attempt.
- When leaks persist after retries are exhausted, returns a non-nil error whose message begins with `found unexpected goroutines:` followed by the rendered stacks.

**`filterStacks(stacks, skipID, opts) []stack.Stack`**
- Drops any stack whose ID equals `skipID`.
- Drops any stack for which the combined option filter matches.
- Retains all others. May reuse the backing array of the input slice (in-place compaction is acceptable).

**`VerifyNone(t TestingT, options ...Option)`**
- Builds opts, extracts (and clears) any cleanup function from the opts before calling `Find`, so that the cleanup does not reach `Find` and trigger its Cleanup-rejection error.
- If `t` also implements a `Helper()` method (the `testHelper` interface), calls it to mark the function as a test helper.
- Calls `Find` with the (cleanup-stripped) opts; on error calls `t.Error(err)`.
- If a cleanup function was present, invokes it with exit code `0` after the check.

**`VerifyTestMain(m TestingM, options ...Option)`**
- Runs the tests via `m.Run()` and captures the exit code.
- Builds opts; extracts and clears the cleanup function. If none was supplied, the cleanup defaults to the process-exit hook (`_osExit`). The cleanup must run on function exit, receiving the (possibly rewritten) exit code.
- Decides whether to run a leak check: run when the test suite succeeded (exit code 0) and `RunOnFailure` was not set, OR when `RunOnFailure` was set (regardless of outcome). Do not run a leak check on a failed run unless `RunOnFailure` is set.
- When running, uses different error-message prefixes for the success vs. failure case (both written to the stubbable stderr writer `_osStderr` via `fmt.Fprintf`).
- If a leak is found and the original exit code was 0, rewrites the exit code to a non-zero failure value (1) before cleanup runs. If the tests already failed, the exit code is preserved.

**Options / filters (`options.go`)**
- `Option` is an interface with `apply(*opts)`. Two concrete implementers: the `opts` struct itself (copies its fields onto the target) and an `optionFunc` adapter (invokes the wrapped function).
- Public option constructors: `IgnoreTopFunction`, `IgnoreAnyFunction`, `IgnoreCreatedBy`, `IgnoreCurrent`, `Cleanup`, `RunOnFailure`; plus unexported `maxSleep` and `addFilter` helpers.
  - `IgnoreTopFunction(f)` → filter matching stacks whose top/first function equals `f`.
  - `IgnoreAnyFunction(f)` → filter matching stacks that contain `f` anywhere.
  - `IgnoreCreatedBy(f)` → filter matching stacks created-by exactly `f`.
  - `IgnoreCurrent()` → snapshots all goroutine IDs *at option-construction time* and later filters out any stack whose ID is in that snapshot.
  - `Cleanup(fn)` → stores `fn` in `opts.cleanup`.
  - `RunOnFailure()` → sets `opts.runOnFailure`.
  - `maxSleep(d)` → sets `opts.maxSleep`.
  - `addFilter(fn)` → appends `fn` to `opts.filters`.
- `buildOpts(options...)` returns an `opts` seeded with default max retries (`_defaultRetries` = 20) and a default max sleep (100 ms), pre-populated with the built-in filters, then applies each supplied option in order.
- `opts.filter(s)` returns true if any registered filter matches `s`.
- `opts.retry(i)` returns false once `i >= maxRetries`; otherwise it sleeps for an exponentially increasing duration (capped at `maxSleep`) and returns true. The backoff grows roughly as microseconds shifted left by the attempt index.
- Built-in filters that must exist and be installed by `buildOpts`: `isTestStack`, `isSyscallStack`, `isStdLibStack`, `isTraceStack`, `isDNSResolverStack` (semantics described in pitfalls).

## Solution decomposition

1. **Option plumbing** — Give `optionFunc` a working `apply`, and make `opts.apply` copy its relevant fields onto the destination. Implement `addFilter`/`maxSleep` and the public constructors as thin `optionFunc`/`addFilter` wrappers.
2. **`buildOpts`** — Construct defaults, install the five built-in filters, apply user options.
3. **Filtering** — Implement `opts.filter` (any-match) and `filterStacks` (skip self + apply filter).
4. **Retry/backoff** — Implement `opts.retry`.
5. **Built-in filters** — Implement each `is*Stack` predicate against stack accessors.
6. **`Find`** — Wire current-ID capture, invalid-option rejection, the retry loop, and error formatting.
7. **`VerifyNone`** — cleanup extraction, helper marking, error reporting.
8. **`VerifyTestMain`** — run, cleanup defaulting/deferral, run-decision, error output, exit-code rewrite.

## Solution space

- **Filter representation:** filters can be a slice of predicate closures (as in the reference) or any equivalent aggregation; `opts.filter` just needs to short-circuit on the first match.
- **In-place vs. fresh slice:** `filterStacks` may build a new slice instead of compacting in place; both are correct as long as the result is the retained set. Order should be preserved.
- **Retry timing:** the exact backoff formula is an internal detail; any monotonic-ish, capped, sleeping backoff that stops at `maxRetries` will satisfy the tests (which typically use small retry counts and `maxSleep`). What matters is that `retry(i)` returns false at/after the max and true before it.
- **Cleanup extraction idiom:** swapping `opts.cleanup` to `nil` while capturing the old value, versus copying then explicitly zeroing, are equivalent. The essential property is that `Find` never sees a non-nil cleanup coming from `VerifyNone`/`VerifyTestMain`.
- **Exit-code rewrite:** any non-zero value works in principle, but `1` is the conventional choice; tests may assert on it, so prefer 1.
- **Error construction:** `errors.New` / `fmt.Errorf` or equivalent; only the message text/prefix is contractually relevant.
- **Copyright/license headers** are optional for correctness (they appear in the reference but are not required by tests). Do not treat their absence as a failure.

## Known pitfalls

- **Exact error strings.** Tests assert specific messages. `Find` must reject Cleanup with a message conveying "Cleanup can only be passed to VerifyNone or VerifyTestMain" and RunOnFailure with "RunOnFailure can only be passed to VerifyTestMain". The leak error must carry the `found unexpected goroutines:` prefix. `VerifyTestMain`'s stderr messages distinguish the successful-run case (`Errors on successful test run`) from the unsuccessful-run case (`Errors on unsuccessful test run`).
- **Cleanup must not reach `Find`.** If you forget to strip `opts.cleanup` before calling `Find` from `VerifyNone`/`VerifyTestMain`, `Find` will error out on every call. Extract and clear it first.
- **Skipping the current goroutine.** `Find` must capture the current goroutine ID *before* scanning and pass it as the skip ID; otherwise `TestFind`/`TestVerifyNone` will always see at least one "leak" (themselves).
- **`IgnoreCurrent` snapshot timing.** The set of goroutine IDs must be captured when the option is *constructed*, not when the filter runs. Building it lazily inside the returned closure would capture goroutines that appear later and defeat the option.
- **Built-in filter semantics** (get these right or the standard testing goroutines will be misreported):
  - `isTestStack`: matches only when the top function is one of the testing-runtime functions (`testing.RunTests`, `testing.(*T).Run`, `testing.(*T).Parallel`, `testing.runFuzzing`, `testing.runFuzzTests`) *and* the goroutine state begins with `chan receive`.
  - `isSyscallStack`: has `runtime.goexit` in stack and state prefixed with `syscall`.
  - `isStdLibStack`: top function is `os/signal.signal_recv` or `os/signal.loop`, or the stack has `runtime.ensureSigM`.
  - `isTraceStack`: has `runtime.ReadTrace`.
  - `isDNSResolverStack`: created-by string is prefixed with `net.(*Resolver).`.
  These matter for `TestVerifyParallel`, `TestVerifyTestMain`, and general false-positive avoidance.
- **Retry loop index.** The index handed to `retry` starts at 0 on the first post-scan check; off-by-one here changes how many attempts happen and can slow or destabilize tests.
- **Deferred cleanup ordering in `VerifyTestMain`.** The cleanup (default `_osExit`) must run via `defer` after the exit-code rewrite, so the rewritten code is what gets passed. Also, defaulting cleanup to `_osExit` when none is supplied is required — otherwise the process won't exit with the right code.
- **Don't call `os.Exit` directly.** Use the stubbable `_osExit` and `_osStderr` variables so tests can intercept them.
- **`buildOpts` must install the built-in filters,** not just the user's. Omitting them causes legitimate framework goroutines to be reported as leaks.

## Cheat surface

- The listed `internal/stack/*` tests do not depend on the stubbed files' logic; they should already pass. Do not "fix" them by editing the stack package to hardcode expected outputs, and do not weaken them.
- Do not make `Find`/`VerifyNone` unconditionally return success (e.g., always `nil`, empty filtered list) to pass tests — the tests include cases that *expect* leaks to be detected (`TestFind`, `TestFindRetry`, `TestNoLeaks`, `TestVerifyTestMain`).
- Do not hardcode the specific goroutine counts or IDs used in tests; the implementation must genuinely filter and compare against live `stack.All()` output.
- The reference diff also deletes a `spec.pdf.bz2` binary; removing or keeping that file is irrelevant to correctness and must not be used as a signal.
- License-header comments carry no behavior; adding them is neither required nor sufficient.

## Success criteria

- The package builds and all listed fail_to_pass tests pass, including the top-level behavioral tests: `TestFind`, `TestFindRetry`, `TestVerifyNone`, `TestIgnoreCurrent`, `TestVerifyParallel`, `TestOptionsFilters`, `TestOptionsIgnoreCreatedBy`, `TestOptionsIgnoreAnyFunction`, `TestOptionsRetry`, `TestVerifyTestMain`, `TestNoLeaks`, and the `internal/stack` suite.
- `Find` correctly ignores the calling goroutine and the built-in framework goroutines, returns `nil` when clean, and returns a `found unexpected goroutines:`-prefixed error when leaks remain after retries.
- `Find` rejects `Cleanup` and `RunOnFailure` options with the specified messages.
- `VerifyNone` marks the test failed on leaks, honors `Helper()`, and runs any cleanup with exit code 0 without passing cleanup into `Find`.
- `VerifyTestMain` runs the suite, performs the leak check per the success/`RunOnFailure` rules, writes the correctly-worded message to the stubbable stderr, rewrites a passing exit code to non-zero on leak detection, and always invokes the (defaulted) cleanup with the final exit code.
- All option constructors and built-in filters behave as described, and `buildOpts` seeds defaults and built-in filters before applying user options.