# TRUTH.md

## Problem

The `Zahgon/erg` crate is the top-level binary/library crate for the Erg programming language. Two source files have been reduced to stubs whose function bodies are `panic!("STUB: not implemented")`:

- `src/dummy.rs` — implements `DummyVM`, an Erg interpreter that does **not** run bytecode itself but instead spawns a Python process running a small REPL server (`src/scripts/repl_server.py`), then mediates a length-prefixed binary protocol over a TCP socket. It also contains the wire-protocol primitives (`Inst`, `Message`, `MessageStream`) and a `PackageManagerRunner` that shells out to an external `poise` tool.
- `src/main.rs` — the CLI entry point. It reads an `ErgConfig` (built from command-line arguments/environment), selects an execution mode, and dispatches to the appropriate runnable (interpreter, compiler/package builder, type checker, linter, lexer, parser, transpiler, package manager, or version-bump utility), returning the process exit code.

A correct solution restores full behavior so that the interpreter round-trips code through the Python REPL server, the transpiler/VM embedding tests work, the wire protocol serializes correctly, and the large `exec_*` / `eval::*` example-execution test suite passes.

## Behavioral contract

Observable behaviors a correct implementation must satisfy:

1. **`Inst` byte mapping.** Converting a `u8` into `Inst` must map exactly: `0x01→Print`, `0x02→Load`, `0x03→Exception`, `0x04→Initialize`, `0x05→Exit`, `0x06→Execute`, and every other value → `Unknown`. This mapping must be the inverse of how instructions are serialized (an `Inst` cast to `u8` yields its discriminant).

2. **`Message` construction.** `Message::new(inst, data)` records the payload length in a 16-bit `size` field. When `data` is `None`, size is 0. When `data` is `Some`, size is the byte length, but a payload longer than `u16::MAX` (65535) must be clamped to 65535 (with a warning printed to stderr rather than panicking or overflowing). `len()` returns `size` as a `usize`.

3. **Wire format (send).** `send_msg` writes, in order and big-endian: 1 byte instruction, 2 bytes size, then the raw data bytes (nothing when data is absent). For a `Print` message carrying ASCII `"hello"` the emitted bytes are exactly `[1, 0, 5, 104, 101, 108, 108, 111]`.

4. **Wire format (receive).** `recv_msg` reads exactly 1 instruction byte, then exactly 2 size bytes (big-endian), then exactly `size` data bytes. A zero size yields a message with no data; otherwise the data is read fully. Instruction byte is decoded via the `Inst` mapping. Reads must use "read exactly N bytes" semantics and propagate I/O errors.

5. **`MessageStream::new`** simply wraps any `Read + Write` value.

6. **Port discovery.** A helper obtains a free local TCP port by binding to `127.0.0.1:0` and reading the assigned port from the socket's local address.

7. **`DummyVM` construction / `New`.** In REPL mode the constructor: picks a free port, loads the embedded `repl_server.py`, substitutes the port and the dump module name into it, spawns the Python interpreter running that script, then repeatedly attempts a TCP connection until it succeeds, sets a read timeout from config, and stores the connected `MessageStream`. In non-REPL mode no stream is created. The compiler is always built from the config. `DummyVM::new` and `Default` both funnel through this logic.

8. **`Runnable` accessors.** `cfg`/`cfg_mut` expose the compiler's config; `initialize` and `clear` delegate to the compiler.

9. **`exec` (batch).** Reads the input source, compiles it in "exec" mode, writes warnings to config output, and executes the produced object, returning an `ExitStatus` carrying the child exit code (defaulting to 0) and the warning count.

10. **`eval` (REPL round-trip).** Compiles source in eval mode, sends an `Execute` message containing the generated Python script bytes to the server, then receives one response and interprets it by instruction:
    - `Exception` → treat as a system-exit error result.
    - `Initialize` → re-init the compiler's generator, take payload as text.
    - `Print` → take payload as text.
    - `Exit` / `Load` / `Execute` / `Unknown` → unexpected from server; terminate cleanly.
    The textual result is appended to accumulated warnings. A trailing `"None"` (the Python repr of a unit/None result) is stripped so nothing is shown in the REPL. When type display is enabled, the last expression's type (and, for a definition, its identifier) is appended.

11. **`finish` / `Drop`.** Dropping the VM must finish it. In REPL mode `finish` sends an `Exit` message, waits for the server's `Exit` acknowledgment, optionally prints a shutdown notice (unless quiet), and removes the dumped `.pyc` file. In non-REPL mode it does nothing.

12. **`expect_block`.** Used by the REPL to decide multi-line continuation. It parses the source and, based on parse errors, classifies the block kind: an `ExpectNextLine` error's sub-message string maps to a `BlockKind`; an unterminated triple-quote error yields a multi-line-string block; other errors yield an error kind. On successful parse, source containing `Class` is a class definition, otherwise no special block.

13. **`PackageManagerRunner::run`.** Verifies the external `poise` tool is available (error + non-zero status if missing), then invokes it with inherited stdio and the config's runtime args, returning its exit status.

14. **`main` dispatch.** The entry point runs on a freshly spawned thread (larger stack). It reads the config, and depending on the selected `ErgMode`, constructs and runs the correct runnable, then exits the process with that runnable's exit code. Modes include running/executing Erg (the `DummyVM`), building/transpiling, type-checking (`PackageTypeChecker`), linting (`Linter`), lexing (`LexerRunner`), parsing (`ParserRunner`), package management (`PackageManagerRunner`), and a version-bump utility. The transpiler-embedding and vm-embedding tests exercise the library API these modes wrap.

## Solution decomposition

Sub-goals, roughly in dependency order:

1. **Protocol enum decode** — implement the `u8 → Inst` conversion per the fixed table (contract §1).
2. **Message value type** — implement `new` with size computation + clamping and the `len` accessor (contract §2).
3. **Framing over a stream** — implement `MessageStream::new`, `send_msg`, `recv_msg` with the exact big-endian layout and exact-read semantics (contract §3–5). Getting §3 and §4 correct is what flips `dummy::test_message`.
4. **Port helper** — free-port discovery (contract §6).
5. **VM lifecycle** — `New::new` (server spawn + connect loop), `Default`, `DummyVM::new`, `finish`, `Drop`, `initialize`, `clear`, `cfg`/`cfg_mut` (contract §7, §8, §11).
6. **Batch execution** — `Runnable::exec` and the inherent `exec` wrapper (contract §9).
7. **REPL evaluation** — `Runnable::eval` and the inherent `eval` wrapper, including response dispatch, `None` trimming, and type annotation (contract §10).
8. **Block classification** — `expect_block` for REPL continuation (contract §12).
9. **Package manager runner** — `new` + `run` (contract §13).
10. **CLI dispatch** — `main` selecting and running the mode-appropriate runnable, returning its exit code (contract §14). This drives the `exec_*`, `eval::*`, and `exec_repl_*` example suites.

## Solution space

- **Buffer construction in `send_msg`.** Any approach that produces the exact byte sequence is valid: build a single `Vec` and `write_all`, or issue separate `write_all` calls for the instruction, size, and data. Preallocation size is irrelevant to correctness.
- **Reading in `recv_msg`.** Reading the three regions with separate `read_exact` calls is natural, but any method that reads exactly the right bytes big-endian and yields identical `Message` values is acceptable. Decoding the instruction inline vs. via the `From` impl are equivalent.
- **Size clamping.** Comparing `len` against `u16::MAX` and clamping, or comparing against `65535`, or using `try_into` with a saturating fallback, all satisfy §2 as long as oversized payloads become 65535 and don't panic. Emitting the warning to stderr is expected but the exact wording isn't tested.
- **`Inst` decode** may use a `match`, an array/lookup table, or explicit conditionals.
- **Connection retry loop** may use `loop`, recursion, or a bounded retry; correctness only requires eventually connecting, applying the read timeout, and honoring the quiet flag for progress messages.
- **`New` vs `DummyVM::new`.** One may delegate to the other in either direction; the golden delegates the inherent `new` to the trait `New::new`.
- **`main` dispatch** may be a `match` on the mode enum or an if/else chain; helper functions per mode are fine. What matters is that each mode instantiates the right runnable and the process exits with the corresponding code.
- **`None`-trimming** can be done via `strip_suffix`, length truncation, or equivalent, as long as a trailing `"None"` is removed.
- **Error/exit handling in `eval`** may use a macro, a helper function, or inlined blocks; the observable requirement is a clean shutdown (finishing the VM) before exiting on protocol errors.

## Known pitfalls

- **Endianness / field order.** The protocol is big-endian and ordered instruction-byte, then 2-byte size, then data. Little-endian, wrong field order, or writing size as 1 or 4 bytes breaks `test_message` and all REPL execution.
- **Size field width.** `size` is 16 bits (2 bytes). Emitting it as a single byte or as the platform `usize` corrupts framing.
- **Partial reads.** Using `read`/`read_to_end` instead of read-exactly can under-read on a real socket and desynchronize the stream. Data must be read using its declared size.
- **Zero-length payloads.** A size of 0 must short-circuit to a data-less message; attempting to read zero bytes into an empty buffer or reading anyway must not corrupt the next message.
- **Payload length overflow.** Casting a `usize` length directly to `u16` truncates silently for large payloads; the spec requires explicit clamping to 65535.
- **`Drop` must finish, not double-run.** `finish` must be idempotent/safe: it only acts when a stream exists (REPL mode), so `Drop` in batch mode is a no-op. Sending an exit and awaiting acknowledgment in the wrong order can hang.
- **Server startup race.** The client must retry connecting until the spawned Python server is listening; connecting once and failing is incorrect.
- **Template substitution.** The embedded server script needs both the chosen port and the module name substituted; the module name derives from the dump filename with path separators turned into dots. Skipping either breaks the round-trip.
- **Stripping `None`.** The REPL suppresses `None` results by trimming a trailing `"None"`; forgetting this makes REPL output tests mismatch.
- **`exec` exit status.** Must surface the executed child's exit code (defaulting to 0 when absent) and the warning count, not a fixed value.
- **Read timeout.** The socket needs a read timeout from config, or a stalled server can block forever.
- **`.pyc` cleanup.** `finish` should remove the dumped bytecode file, ignoring the error if it's absent.
- **`main` must exit with the runnable's code.** Returning `()` or always exiting 0 defeats the error-path `exec_*_err` tests, which expect non-zero statuses.

## Cheat surface

Behaviors that must be genuinely implemented, not faked:

- **Do not hardcode `test_message`'s expected bytes.** The `[1,0,5,'h','e','l','l','o']` sequence and the `Print`/`A` round-trip must emerge from a general serializer/deserializer, not from special-casing the test inputs.
- **Do not stub `recv_msg`/`send_msg` to return canned messages.** They must actually traverse the wrapped stream so arbitrary payloads round-trip.
- **Do not bypass the Python server** by having `eval` compute results in Rust directly; the `eval::*` and `exec_repl_*` tests rely on real compilation + server execution (or the equivalent embedding path). Faking outputs per test string is a cheat.
- **Do not remove/weaken the protocol dispatch** in `eval` (e.g., ignoring `Exception`/`Initialize` distinctions) just to pass a subset; each instruction has distinct semantics.
- **Do not make `main` a no-op** or route every mode to one runnable; the transpiler/checker/linter/package-manager/version modes must each be dispatched correctly.
- **Do not swallow errors to force success.** Error-path tests require real non-zero exit statuses and error output.
- **No editing of tests, expected-output fixtures, or the embedded server script** to make assertions pass.

## Success criteria

- All listed `fail_to_pass` tests pass, including:
  - `dummy::test_message` — validates exact serialization and deserialization of the wire protocol.
  - `test_builder`, `test_transpiler_embedding`, `test_transpiler_embedding2/3/4`, `test_vm_embedding` — library-embedding APIs reachable through the modes wired in `main`.
  - The `eval::build_in_function::*` and `eval::literal::*` suites — REPL evaluation round-trips (print/assert/interpolation/multiline/ratio, plus their invalid-input error cases).
  - The `exec_repl_*` suite — interactive REPL behaviors including auto indent/dedent detection (`expect_block`), class/def definitions, decorators, loops, hello-world, invalid-indent and server-mock cases.
  - The large `exec_*` suite of example programs and their `*_err` counterparts — end-to-end compile-and-run behavior with correct success/error exit statuses.
- The crate builds without unresolved stubs; no `panic!("STUB…")` remains.
- No previously listed behavior regresses (no `pass_to_pass` set given, but the implementation must not break the workspace build).