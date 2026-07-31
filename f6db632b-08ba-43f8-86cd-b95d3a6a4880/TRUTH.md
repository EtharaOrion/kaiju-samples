# TRUTH.md

## Problem

The repository `Shivansh9411/promptui` is a Go port of the `manifoldco/promptui`
interactive‑prompt library in which a set of source files has been reduced to
stubs. Every stubbed function currently contains a placeholder of the form
`_ = "STUB: not implemented"` and returns a zero value (`nil`, `""`, `0`, an
empty struct, etc.). The task is to restore the real behavior of these
components so the library compiles and behaves like the upstream library.

The files reduced to stubs include the terminal styling helpers (`codes.go`,
`styles.go`, `styles_windows.go`), the movable input cursor (`cursor.go`), the
key‑code definitions (`keycodes*.go`), the searchable, scrollable list model
(`list/list.go`), the buffered screen renderer (`screenbuf/screenbuf.go`), and
the interactive prompt/select drivers (`prompt.go`, `promptui.go`, `select.go`).

Correctness is exercised primarily through the `list` and `screenbuf` packages,
whose unit tests must move from failing to passing:

- `list.TestListNew`
- `list.TestListMovement`
- `list.TestListPageDown`
- `list.TestListComparion`
- `screenbuf.TestScreen`

The remaining files must still compile and expose their public API so the whole
module builds, but they are not directly asserted by the listed tests.

## Behavioral contract

The implementation as a whole must satisfy the following observable behaviors.

**Package `list` — construction (`New`)**
- Accepts an arbitrary `items interface{}` and a visible `size int`.
- Returns an error when `size < 1`, and a distinct error when `items` is `nil`
  or is not a slice kind. Determination of "is a slice" must be reflection‑based
  so any concrete slice element type is accepted.
- On success, returns a non‑nil `*List` whose internal collection preserves the
  order and length of the input slice, whose visible window equals `size`, and
  whose starting scroll position and cursor are both `0`.
- Each stored element must retain a stable, per‑element identity so that two
  equal values (e.g. two identical strings) remain individually addressable
  (see `TestListComparion`). This is why elements are stored as independent
  pointers to `interface{}` values rather than as bare values.

**Package `list` — navigation**
- `Next` advances the cursor toward the end but never past the last in‑scope
  item; when the cursor would leave the bottom of the visible window, the scroll
  start advances so the cursor stays visible.
- `Prev` moves the cursor toward the start but never below the first item; when
  the cursor moves above the current window, the scroll start follows it up.
- `PageDown` jumps the window forward by one page (`size`), clamping the start so
  the last page is fully populated and never scrolling past the end; the cursor
  is repositioned into the new page (advancing to the page start, or to the final
  item when already at the page start).
- `PageUp` jumps the window backward by one page, clamping the start at `0`, and
  keeps the cursor no lower than the new start.
- `CanPageDown` / `CanPageUp` report whether another page exists in the given
  direction.
- Movement must be a no‑op at the respective boundary (top for `Prev`/`PageUp`,
  bottom for `Next`/`PageDown`).

**Package `list` — inspection**
- `Items` returns the currently visible slice (at most `size` elements starting
  at the scroll position) together with the index — relative to that visible
  slice — of the active (cursor) item, or `NotFound` (`-1`) when the cursor lies
  outside the visible window.
- `Index` returns the position of the currently selected item within the
  original, unfiltered collection, using element identity for the lookup, or
  `NotFound` when nothing is selected.
- `Start`/`SetStart` and `SetCursor` read and write the scroll/cursor position
  with out‑of‑range values clamped into valid bounds.

**Package `list` — searching**
- `Search(term)` trims surrounding spaces, resets cursor and start to `0`, and
  narrows the working scope to the items for which the user‑supplied `Searcher`
  returns true.
- `CancelSearch` restores the full collection as the working scope and resets
  cursor and start.

**Package `screenbuf` — buffered rendering (`TestScreen`)**
- A `ScreenBuf` wraps an `io.Writer` and accumulates output between an explicit
  reset and a flush.
- Writing a line records its content and counts it as one visible row; the first
  write of a render cycle must first move the terminal cursor up over and clear
  the rows written by the previous cycle so redraws do not accumulate.
- Flushing emits the buffered bytes to the underlying writer, then resets the
  buffer while remembering how many rows were drawn so the next cycle can erase
  them.
- The sequence of bytes produced for a given series of writes/flushes must match
  the expected control‑sequence + text output asserted by `TestScreen`
  (cursor‑up, clear‑line, hide/show cursor around drawing, and the line text
  each terminated appropriately).

**Supporting packages (must compile and behave, but not directly asserted)**
- `codes.go`: `Styler(attrs...)` returns a function wrapping a value with the
  ANSI escape sequence built from the given attributes and terminated by the
  reset code (unless the value already ends with the reset code); `upLine` and
  `movementCode` produce the corresponding cursor‑movement escape sequences.
- `cursor.go`: the `Cursor` type inserts a visible pointer glyph at its position,
  supports insertion, masking, backspace, absolute/relative movement with
  bounds correction, and a readline‑style `Listen` callback that maps key runes
  to navigation/edit actions.
- `keycodes*.go`: expose the key‑rune variables (`KeyEnter`, `KeyBackspace`,
  `KeyPrev`, etc.), with the platform‑specific `KeyBackspace` guarded by build
  constraints.

## Solution decomposition

1. **List model core** — implement `New` with the two validation checks and the
   reflection‑based conversion of the input slice into a collection of
   independently‑addressable elements; initialize `size`, `scope`, and the
   collection.
2. **List navigation** — implement `Next`, `Prev`, `PageUp`, `PageDown`,
   `CanPageUp`, `CanPageDown`, keeping cursor and scroll start mutually
   consistent and boundary‑safe.
3. **List inspection** — implement `Items`, `Index`, `Start`, `SetStart`,
   `SetCursor` with clamping and identity‑based lookup.
4. **List searching** — implement `Search`, `CancelSearch`, and the internal
   filter that rebuilds the scope from the `Searcher`.
5. **Screen buffer** — implement the reset/write/flush cycle that clears the
   previously drawn rows before redrawing and emits the correct control
   sequences.
6. **Styling and escape helpers** — implement `Styler`, `upLine`,
   `movementCode`, and any color/style variable wiring the templates depend on.
7. **Cursor and key codes** — implement the input `Cursor` methods and expose
   the key‑rune variables under the correct build tags.
8. **Prompt/select drivers** — restore `prompt.go`, `promptui.go`, `select.go`
   so the package builds and its public entry points function.

## Solution space

- **Element identity:** storing elements as `[]*interface{}` (pointer per
  element) is the canonical way to give equal values distinct identities. Any
  equivalent scheme that guarantees each original element is uniquely
  identifiable for `Index`/`TestListComparion` (e.g. index‑based bookkeeping) is
  acceptable, provided the observable results match.
- **Clamping style:** bounds checks may be written as `if`/`switch` guards or via
  helper min/max functions; either is fine as long as no navigation call panics
  and boundary no‑ops hold.
- **PageDown cursor placement:** the exact arithmetic (computing the new start
  then deriving the cursor, versus incrementing and re‑clamping) may vary; only
  the resulting `(start, cursor)` pairs asserted by the tests matter.
- **Screen buffer implementation:** the buffer may be a `bytes.Buffer` plus a
  line counter, or a slice of recorded lines; the flush may write directly or via
  an intermediary. Any structure that produces the byte sequence expected by
  `TestScreen` is valid.
- **Reflection vs. type switches in `New`:** reflection is the general solution;
  a solution could special‑case common slice types, but it must still reject
  non‑slices and accept arbitrary element types the tests use.
- **Styler assembly:** attributes can be joined with `;` and formatted into one
  escape, or emitted as separate escapes; the visible wrapping semantics
  (prefix escape + value + trailing reset unless already present) are what
  matter.

## Known pitfalls

- **Equal‑value comparison (`TestListComparion`):** if elements are stored by
  value rather than by unique reference, `Index` cannot distinguish duplicate
  values and the comparison test fails. Preserve per‑element identity.
- **Off‑by‑one in windowing:** `Items` must return at most `size` elements and
  must clamp the end to the length of the current scope; the active index is
  relative to the *visible* slice, not the whole collection, and must be
  `NotFound` when the cursor is off‑screen.
- **Cursor/start desynchronization:** every movement must keep the cursor inside
  the `[start, start+size)` window; forgetting to advance/retreat `start` in
  `Next`/`Prev` breaks `TestListMovement`.
- **PageDown clamping:** failing to clamp `start` when the remaining items are
  fewer than a page (or when the scope is shorter than `size`) causes an
  out‑of‑range window or wrong cursor in `TestListPageDown`.
- **Validation order and messages in `New`:** both the `size < 1` and the
  not‑a‑slice conditions must be checked; a `nil` input must be treated as an
  error, not dereferenced.
- **Search must reset position:** neglecting to reset cursor/start on `Search`
  and `CancelSearch` leaves stale scroll state.
- **Screen redraw accumulation:** if the previous cycle's rows are not cleared
  before the next draw, output accumulates and `TestScreen`'s expected byte
  stream will not match; also remember to reset the row counter after flush.
- **Build tags:** `keycodes_other.go` / `keycodes_windows.go` and
  `styles_windows.go` are guarded by platform build constraints; the constraint
  syntax must remain valid so exactly one `KeyBackspace` definition is compiled
  per platform (duplicate or missing definitions break the build).

## Cheat surface

- Do **not** hard‑code the specific values the tests assert (e.g. return a fixed
  visible slice, a fixed active index, or a canned byte sequence) instead of
  computing them from the model state. The list and screen behaviors must be
  general and driven by the actual inputs.
- Do **not** special‑case the exact item slices, sizes, or search terms used by
  the tests; navigation and search must work for arbitrary inputs.
- Do **not** stub `Index`/`Items` to always return `NotFound`/empty just to
  satisfy a subset of assertions.
- Do **not** remove or weaken the `New` validation to make a test pass while
  breaking the error contract.
- Leaving unrelated stubs (`prompt.go`, `select.go`, etc.) as no‑ops is only
  acceptable insofar as the module still compiles and their public signatures
  are intact; the graded packages must be genuinely implemented.

## Success criteria

- The whole module compiles on the target platform with correct build‑tag
  handling of key codes and platform styles.
- `list.TestListNew`, `list.TestListMovement`, `list.TestListPageDown`,
  `list.TestListComparion`, and `screenbuf.TestScreen` all pass.
- `list.New` enforces the `size >= 1` and slice‑type contracts and initializes
  state at the origin.
- List navigation keeps cursor and scroll window consistent and boundary‑safe;
  `Items`, `Index`, and the search operations behave as specified for arbitrary
  inputs and duplicate values.
- The screen buffer clears the previous render before redrawing and emits the
  expected control‑sequence/text byte stream.
- No previously passing behavior is regressed and no test‑specific values are
  hard‑coded.