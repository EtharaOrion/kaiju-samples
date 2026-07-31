# Problem

The repository `signature_pad` is a TypeScript library that lets a user draw a freehand signature on an HTML `<canvas>`, with support for undo/redo, color/width changes, background colors, and export to PNG/JPG/SVG. Several source files have had their implementation bodies replaced with `throw new Error("STUB")` placeholders. The task is to restore correct, working implementations of these stubs so the library behaves as specified and the test suite passes.

Stubbed files:
- `src/point.ts` — geometric point value object.
- `src/bezier.ts` — cubic Bézier curve construction and length approximation.
- `src/signature_event_target.ts` — a small `EventTarget` wrapper for emitting signature lifecycle events.
- `src/throttle.ts` — a generic function-rate limiter.
- `src/signature_pad.ts` — the main class tying together pointer/mouse/touch input, curve rendering, data model, and image export.

There is also an import-hygiene test: every relative import/export specifier in `src/` must end with a `.js` extension (ESM/NodeNext convention), even though the sources are `.ts`.

# Behavioral contract

**Point (`src/point.ts`)**
- Constructor takes `(x, y, pressure?, time?)`. It MUST throw an `Error` when `x` or `y` is `NaN` (message should reference the invalid coordinates). String numeric inputs MUST be coerced to numbers, and the stored `x`/`y` MUST be of `number` type.
- `pressure` defaults to `0` when falsy/absent; `time` defaults to the current timestamp (`Date.now()`) when falsy/absent.
- `distanceTo(other)` returns Euclidean distance between the two points.
- `equals(other)` returns `true` only when `x`, `y`, `pressure`, and `time` all match; differing in any one yields `false`.
- `velocityFrom(start)` returns `0` when the two times are equal; otherwise distance divided by the time difference (may be negative if start is later).

**Bezier (`src/bezier.ts`)**
- Static `fromPoints(points, widths)` builds a `Bezier` from four consecutive points, deriving the two control points from the midpoint/length-ratio construction. It MUST not produce `NaN` when adjacent points coincide (division-by-zero must be guarded, treated as ratio `0`).
- The constructed curve uses `points[1]` as start, `points[2]` as end, the computed control points in between, and carries `widths.start`/`widths.end`.
- `length()` returns an approximated arc length by sampling the curve (a fixed number of parametric steps) and summing segment distances.
- The parametric point helper computes the standard cubic Bézier polynomial for a coordinate given `t` and the four control values.

**SignatureEventTarget (`src/signature_event_target.ts`)**
- Constructor MUST create a native `EventTarget`; if the `EventTarget` constructor is unavailable (older Safari/iOS), it MUST fall back to using `document` as the event target rather than throwing.
- `addEventListener`, `removeEventListener`, and `dispatchEvent` MUST delegate to the internal target (with `dispatchEvent` returning the delegated boolean result).

**throttle (`src/throttle.ts`)**
- Returns a wrapped function that invokes the original at most once per `wait` interval, preserving the most recent arguments/`this`, and executing a trailing call for events that arrive during the cooldown. A `wait` of `0` should effectively call through immediately (the pad also bypasses throttling entirely when the configured value is `0`).

**SignaturePad (`src/signature_pad.ts`)**
- Constructor calls `super()`, stores the canvas, and resolves options with correct fallback semantics:
  - Numeric-tunable options that may legitimately be `0` (`throttle`, `minDistance`) MUST use nullish-coalescing so an explicit `0` is preserved, while `undefined` falls back to defaults (`throttle` → 16, `minDistance` → 5).
  - Other options (`velocityFilterWeight` 0.7, `minWidth` 0.5, `maxWidth` 2.5, `dotSize` 0, `penColor` `'black'`, `backgroundColor` `'rgba(0,0,0,0)'`, `compositeOperation` `'source-over'`, `canvasContextOptions` `{}`) use their documented defaults; explicit `undefined` for any option must yield the fallback.
  - Sets up the throttled move handler (or the raw update when throttle is 0), binds all event handlers, obtains the 2D context with the context options, clears, and calls `on()`.
- `on()` disables text selection and touch actions on the canvas (`touchAction`/`msTouchAction` = `'none'`, `userSelect`/`webkitUserSelect` = `'none'`) and attaches the appropriate input listeners (pointer events when available and not iOS-Scribble, otherwise mouse plus optional touch).
- `off()` restores canvas styles (`touchAction` etc. back to `'auto'`, selection back to `'auto'`) and removes all listeners.
- `clear()` fills the canvas with the background color, empties the data model, resets internal stroke state, marks the pad empty, and clears cached data-URL state.
- `isEmpty()` reflects internal empty flag; `toData()` returns the stored point groups.
- `fromData(pointGroups, {clear})` optionally clears first, redraws the given groups via curve/dot drawing, and appends them to the stored data. When `clear: false`, existing canvas content is preserved.
- `fromDataURL()` returns a Promise, draws the image onto the canvas honoring ratio/width/height/offset options, and marks the pad non-empty; caches the URL/options for redraw.
- `redraw()` re-renders from cached data-URL (if any) and stored point-group data without permanently clearing them.
- `toDataURL(type, encoderOptions)`: for `'image/svg+xml'` returns a base64-encoded SVG data URL (only accepting object encoder options, ignoring non-objects); otherwise delegates to `canvas.toDataURL` (only accepting numeric encoder options).
- `toSVG()` produces an SVG string, optionally scaled for high DPI and optionally including the background color.
- Input handling: a stroke begins on primary-button/single-touch/pointer down, updates on move (throttled), and ends on up/cancel — dispatching `beginStroke`, `beforeUpdateStroke`, `afterUpdateStroke`, and `endStroke` events. `beginStroke` is cancelable (calling `preventDefault` aborts the stroke and prevents any canvas writing). Pointer events with a different pointer id than the active stroke are ignored while a stroke is in progress, but a new pointer id is accepted once the previous stroke ends. `pointerup`/`mouseup` outside the canvas and `pointercancel`/`touchcancel` end the stroke. Touch handlers call `preventDefault` only when the event is cancelable.

# Solution decomposition

1. **Point** — implement validation, numeric coercion, defaults, and the three geometric methods.
2. **Bezier** — implement `calculateControlPoints` (midpoints, segment lengths, guarded length ratio, translation), `fromPoints`, the polynomial `point` helper, and the sampled `length`.
3. **SignatureEventTarget** — try/catch construction of `EventTarget` with `document` fallback; delegate the three listener/dispatch methods.
4. **throttle** — implement time-based rate limiting with trailing invocation and argument capture.
5. **SignaturePad** — the bulk: option resolution, handler binding, context acquisition, `on`/`off` style + listener management, `clear`/`redraw`/`fromDataURL`/`toDataURL`/`toSVG`, data model (`fromData`/`toData`/`isEmpty`), and the pointer/mouse/touch event pipeline with stroke lifecycle events and pointer-id tracking.
6. **Import hygiene** — ensure all relative imports/exports across `src/` carry the `.js` suffix.

# Solution space

- **EventTarget fallback**: any mechanism that yields a working target and degrades to `document` (or another valid `EventTarget`) when the constructor throws is acceptable; the try/catch shape is not mandated.
- **throttle**: multiple correct rate-limiter implementations exist (timeout-based trailing edge, timestamp comparison, leading+trailing). What matters is at-most-once-per-`wait` with the latest args eventually applied, and correct behavior at `wait === 0`.
- **Bezier length**: the step count and exact summation loop are implementation details; any reasonable sampling that yields the expected approximate length is fine. Guarding the zero-length division may be done via a conditional or an epsilon.
- **Point defaults**: `pressure || 0` vs explicit undefined-checks are both acceptable as long as falsy/absent behavior matches; likewise `Date.now()` vs `new Date().getTime()` for the time default.
- **toDataURL/toSVG**: the precise SVG string builder can vary; correctness is judged by the tested structural expectations (SVG element, DPI scaling, optional background rect, base64 encoding for the data-URL variant).
- **Listener window resolution**: obtaining the correct `window`/`defaultView` for a canvas in an external document can be done in various ways, provided listeners are attached to and removed from the same target — critical for the "endStroke outside canvas in an external window" case.
- **Option coalescing**: the essential requirement is `0`-preserving handling for `throttle`/`minDistance` (nullish coalescing or an equivalent explicit `=== undefined` check) versus falsy-fallback for the rest.

# Known pitfalls

- Using `||` instead of `??` for `throttle` and `minDistance` would wrongly discard a legitimate `0`, breaking the "allows to set … to 0" tests.
- Forgetting that explicit `undefined` options must still fall back to defaults.
- `Point.equals` must compare all four fields; omitting `pressure` or `time` fails several equality tests.
- `velocityFrom` must return exactly `0` for equal times (avoid division by zero producing `NaN`/`Infinity`).
- Bézier control-point computation must guard `l1 + l2 === 0`; coincident points otherwise yield `NaN` coordinates.
- The `beginStroke` event must be dispatched as **cancelable**, and a cancelled begin must prevent any drawing/data mutation.
- Pointer-id tracking: ignore moves/ups from a foreign pointer id during an active stroke, but reset the tracked id on stroke end so a subsequent different pointer id works.
- Ending strokes must handle `pointerup`/`mouseup` firing outside the canvas (listeners on window/document, not just canvas) and `pointercancel`/`touchcancel`.
- Touch handlers must call `preventDefault` only when `event.cancelable` is true.
- `on()`/`off()` must set and later restore both standard and vendor-prefixed style properties (`touchAction`/`msTouchAction`, `userSelect`/`webkitUserSelect`).
- `clear()` must reset cached data-URL state and the active stroke pointer id, not merely wipe pixels.
- `redraw()` must not permanently discard the stored data — it clears then repopulates from cached state.
- `toDataURL` must ignore mismatched encoder-option types (object only for SVG, number only otherwise) to satisfy the type-guard tests.
- Every relative `import`/`export … from '...'` in `src/` must end in `.js`; a missing extension fails the imports test regardless of runtime behavior.
- Move updates must go through the throttled wrapper when throttle > 0 but bypass it (use the raw update) when throttle is 0.

# Cheat surface

- Do NOT special-case test inputs, hard-code expected coordinate/length/velocity values, or return canned strings from `toDataURL`/`toSVG` to match specific assertions. Implementations must compute results generically.
- Do NOT satisfy the imports test by editing/deleting the test or by stripping imports rather than adding correct `.js` extensions.
- Do NOT stub `dispatchEvent` to always return `true`/`false`; it must reflect the delegated target's return so cancelable event semantics work.
- Do NOT make `isEmpty` a constant; it must track real stroke/data state.
- Avoid removing the deleted binary spec artifact as a substitute for real implementation work — the only meaningful change is restoring source behavior. (If the reference removes an unrelated packaged spec file, that is incidental and not part of the required behavior.)
- Do NOT bypass throttling/event dispatch just to make a timing-sensitive test pass; the lifecycle events and rate limiting are part of the contract.

# Success criteria

- All listed `fail_to_pass` tests across `tests/point.test.ts`, `tests/bezier.test.ts`, `tests/imports.test.ts`, and `tests/signature_pad.test.ts` pass.
- No `throw new Error("STUB")` (or equivalent placeholder) remains in the five stubbed files.
- Point validation, coercion, distance, equality, and velocity behave exactly as contracted.
- Bézier construction is `NaN`-free for coincident points and length approximation matches expectations.
- The `SignatureEventTarget` wrapper delegates correctly and falls back to `document` when needed; events (`beginStroke` cancelable, `beforeUpdateStroke`, `afterUpdateStroke`, `endStroke`) dispatch with correct semantics.
- Option handling preserves explicit `0` for `throttle`/`minDistance` and applies fallbacks for `undefined`.
- Pointer/mouse/touch stroke lifecycle, pointer-id filtering, out-of-canvas and cancel handling, and touch `preventDefault` gating all behave as tested.
- `on`/`off` toggle canvas styles and listeners correctly; `clear`, `redraw`, `fromData`/`toData`, `fromDataURL`, `toDataURL`, and `toSVG` (including DPI and background variants) produce the expected results.
- All relative import/export specifiers in `src/` end with `.js`.