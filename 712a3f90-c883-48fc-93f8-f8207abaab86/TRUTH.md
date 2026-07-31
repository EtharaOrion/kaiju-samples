# Problem

The `etherparse` crate (a `#![no_std]`-compatible, zero-copy Ethernet / IP / transport packet parsing and building library) has been reduced to stubs across essentially its entire source tree: the library root, the error type hierarchy (`err/…`), the link/net/transport header + slice types, the checksum helpers, the IP defragmentation module, the I/O helpers, and the packet builder/slicer machinery. Supporting project files (`Cargo.toml` manifests, CI workflow, `Cross.toml`, `README.md`) were also stubbed.

The task is to re-implement the crate so that it compiles and behaves as a correct packet library, and so that a large battery of unit tests (checksum arithmetic, error-type trait conformance, defragmentation, header/slice round-trips, packet composition) pass. Crucially, the code must be **endianness-correct**: it must produce identical results on little-endian and big-endian (e.g. `powerpc64`) targets. The CI/manifest changes exist specifically to add a big-endian test target and a version bump (`0.20.2` → `0.20.3`).

The specification here describes the *destination*: the observable contracts each module must satisfy. It does not prescribe the internal file layout, since many arrangements are valid.

# Behavioral contract

Because the whole crate was stubbed, the contract is best expressed as a set of module-level invariants that the passing tests exercise.

### Checksum (`checksum.rs`)
- Provides an incremental Internet checksum (RFC 1071 one's-complement 16-bit sum) accumulator. There are three logical pieces the tests name directly:
  - a `u32`-based 16-bit-word helper (`u32_16bit_word`),
  - a `u64`-based 16-bit-word helper (`u64_16bit_word`),
  - a `Sum16BitWords` accumulator type (`sum16_bit_words`).
- The accumulator must support: construction/`new`, `Default`, `Clone`, `Debug`, `PartialEq`/`Eq`, and folding operations:
  - `add_2bytes`, `add_4bytes`, `add_8bytes`, `add_16bytes`, `add_slice`,
  - `ones_complement` (final fold-and-invert → 16-bit checksum),
  - a "no zero" variant (`to_ones_complement_with_no_zero`) that maps a computed `0x0000` result to `0xFFFF` (used where the protocol reserves 0 to mean "no checksum", e.g. UDP).
- **Endianness invariant:** adding the same input bytes must yield the same 16-bit checksum on every target. The byte values fed in are network-order octets; the arithmetic must not leak host endianness into the result. The `u32` and `u64` paths must agree (`u32_u16_comparison`).
- Adding must handle carry folding correctly: sums that overflow 16 bits carry into the high bits and are folded back before the final complement.

### Error types (`err/…`)
Every error type (dozens across `arp`, `ip`, `ipv4`, `ipv6`, `ip_auth`, `ip_exts`, `ipv4_exts`, `ipv6_exts`, `tcp`, `linux_sll`, `macsec`, `packet`, `io`, `net`, plus the top-level `len_error`, `value_too_big_error`, `value_type`, `layer`, `from_slice_error`, `read_error`, `slice_write_space_error`) must uniformly provide:
- `Debug` (derived-style, field-visible output the `debug` tests inspect).
- `Display` via `core::fmt` producing human-readable messages (the `fmt` tests check exact strings).
- `Clone`, `PartialEq`/`Eq`, and where tested `Hash`, `PartialOrd`/`Ord`.
- `source()` via `std::error::Error` (gated behind the `std` feature) returning the correct nested cause: leaf errors return `None`; wrapper/enum errors return the inner error for their I/O or content variants.
- Conversion (`From`) relationships between related error types where tested (e.g. `from_slice_error::from`, `arp_eth_ipv4_from_error`).
- Accessor helpers where tested (e.g. `from_slice_error::accessors`, `headers_slice_error::add_slice_offset` which shifts a byte offset).
- The read/limited-read error families must expose their I/O error and content/`Len` variants and their `len`/`io`/`content` accessors.

### Layer / value errors
- `Layer` is an enum naming each protocol layer with a `Display`.
- `ValueType`, `ValueTooBigError`, `LenError`, `LenSource` carry structured context (offending value, allowed max, byte length, source-of-length) with the trait suite above; `add_slice_offset`-style adjustments must be arithmetically correct.

### Defragmentation (`defrag/…`)
- `IpFragRange` models a `[start,end)` fragment byte range with: equality/`Debug`/`Clone`, an "is connected/overlapping/adjacent" predicate, and a `merge` producing the union when connected.
- `IpDefragBuf` accumulates fragment payload into a reconstructed buffer: `new`, adding fragments (respecting offsets and more-fragments flags), `Debug`/`Clone`/`Eq`.
- `IpDefragError` enumerates defrag failure modes with the full error-trait suite (`Debug`, `Display`, `source`, ordering/hash).
- `IpDefragPayloadVec` holds a defragmented payload plus its IP number / len source, with `Debug`, `Clone`, `Eq`, `Hash`, `Ord`.
- `IpDefragPool` is the reassembly pool: `new`/`Default`, `process_sliced_packet` (feeds a sliced packet, returns a finished payload when complete), and `retain` (drops stale/partial entries). It reuses buffers via the pool.

### Link / net / transport headers and slices
- Each header type supports read-from-slice, read-from-reader (std), write, `header_len`, and field accessors matching the on-wire layout; each `…Slice` is a zero-copy view exposing the same fields plus `.slice()`/payload. Round-trip (`write` then `from_slice` yields the original) must hold.
- Bounded newtypes (`VlanId` 12-bit, `VlanPcp` 3-bit, `IpDscp` 6-bit, `IpEcn` 2-bit, `Ipv6FlowLabel` 20-bit, `IpFragOffset` 13-bit, `MacsecShortLen`, `MacsecAn`, `Qrv`, etc.) enforce their range with a `TryFrom`/constructor that returns a `ValueTooBigError` (or a dedicated unknown-value error) when out of range.
- `SlicedPacket` / `LaxSlicedPacket` / `PacketHeaders` / `LaxPacketHeaders` parse a full stack from Ethernet, Linux SLL, an ether type, or IP downward; the "lax" variants tolerate truncated / cut-off payloads (as found in ICMP-embedded packets) instead of erroring.

### Composition tests
- `compositions_tests::test_compositions` requires that building packets with the `PacketBuilder` and then slicing/parsing them yields consistent headers and correct (endianness-independent) checksums.
- `compositions_tests::test_packet_slicing_panics` requires the documented panic/guard behavior on the specific malformed-length inputs it drives.

# Solution decomposition

A correct solution proceeds roughly as:

1. **Manifests / project files.** Fix the crate + proptest-generator `Cargo.toml` so the workspace builds; bump the version string to `0.20.3` in `README.md` (and update the doc links accordingly). Add the big-endian CI target and the `Cross.toml` env passthrough for `PROPTEST_CASES`. These are non-behavioral but must be internally consistent.

2. **`lib.rs` wiring.** Declare all modules, re-export the public API surface, keep `#![no_std]` with `alloc`/`std` feature gating so both `--no-default-features` and default builds compile.

3. **Checksum module.** Implement the one's-complement 16-bit accumulator with correct carry folding, endianness-independent byte handling, the `u32`/`u64` helpers, and the "no-zero" final variant.

4. **Error hierarchy.** Implement every error enum/struct with the uniform trait suite (`Debug`, `Display`, `Clone`, `Eq`, feature-gated `Error`/`source`, plus `Hash`/`Ord` where used) and the required `From`/accessor conversions.

5. **Value/newtype layer.** Bounded integer newtypes with range-checked constructors and their error mappings.

6. **Header + slice types** for link, net, transport, and their extension headers; ensure read/write/round-trip and field accessors.

7. **Defrag module.** Range algebra, buffer, payload vec, pool, and error.

8. **Higher-level assembly.** Readers/writers, `LimitedReader`, packet builder, sliced/lax-sliced cursors and packet types.

# Solution space

- **File layout is not fixed.** The golden solution spreads types across many files with `mod.rs` re-exports; a different-but-correct solution may consolidate or split modules differently, as long as the public paths the tests reference (module names appearing in the test IDs, e.g. `err::ip::header_error`, `checksum::sum16_bit_words_tests`) resolve. Note the test IDs pin *module* paths, so the module tree (and where each `#[cfg(test)] mod` lives) must broadly match the canonical crate layout.
- **Checksum accumulator width.** Both a `u32` and a `u64` accumulator are expected (tests exercise each and compare them). Internally either may fold carries eagerly or lazily; only the final `ones_complement` result is observable.
- **Endianness handling** may be achieved by consistently interpreting inputs as big-endian/network order, or by doing the fold in a byte-order-neutral way and byte-swapping only at the boundary — any approach that yields identical results on LE and BE is acceptable.
- **Error trait provision** may be via `derive` (`Debug`, `Clone`, `PartialEq`, `Eq`, `Hash`, `PartialOrd`, `Ord`) plus hand-written `Display`/`Error`, or hand-written throughout. Message wording must match what the `fmt` tests assert.
- **CI/manifest specifics** (exact matrix entry name, reduced proptest case count) are cosmetic; any configuration that keeps the build green and passes the big-endian target is acceptable. The version-string bump must be consistent wherever it appears.
- **Bounded-newtype error type**: returning a shared `ValueTooBigError` or a per-type dedicated error is both acceptable provided the corresponding tests' expectations are met.

# Known pitfalls

- **Endianness bug in checksum (the headline pitfall).** Reading 16-bit words with the host's native byte order and summing them produces a checksum that differs between LE and BE machines. The big-endian CI target exists precisely to catch this. The sum must be computed so the *bytes*, not the host-interpreted integers, drive the result; and the `u32` and `u64` paths must agree exactly.
- **Carry folding.** Failing to fold the accumulated high bits back into the low 16 bits before complementing yields wrong checksums for inputs that overflow.
- **The "no-zero" rule.** For protocols where a checksum of `0` encodes "no checksum" (UDP), the final value must be remapped `0x0000 → 0xFFFF`; forgetting this fails `to_ones_complement_with_no_zero` and UDP composition tests.
- **`source()` correctness.** Leaf errors must return `None`; wrapper/enum errors must return the *actual* nested cause for their I/O and content variants. Returning `None` everywhere (or the wrong variant) fails the many `source` tests. This must be `#[cfg(feature = "std")]`-gated so `no_std` builds still compile.
- **`Display` string exactness.** The `fmt` tests assert specific message text; approximate wording fails them.
- **Feature gating.** The crate must build under `--no-default-features` (no `std`, `alloc` only). Using `std`-only items (e.g. `std::error::Error`, `Vec` without `alloc`) outside their gates breaks the no_std / no-default-features builds.
- **Offset adjustment arithmetic.** `add_slice_offset`-style helpers must add (not overwrite) and must not overflow for the tested inputs.
- **Bounded newtype range checks.** Off-by-one in the max value (e.g. allowing `1<<n` instead of `(1<<n)-1`) breaks range-enforcement tests.
- **Defrag range merge/connectivity.** Adjacent vs. overlapping vs. disjoint must be distinguished correctly; an incorrect predicate corrupts reassembly and fails `is_value_connected` / `merge` / pool tests.
- **Lax vs strict parsing.** Lax parsers must not error on truncated payloads; strict parsers must. Conflating the two breaks composition and slicing-panic tests.

# Cheat surface

The following would technically flip tests without implementing the real behavior and must be treated as **incorrect**:

- Hard-coding checksum results (or special-casing the exact test inputs) instead of computing a genuine RFC 1071 sum. A correct implementation must be endianness-independent for *arbitrary* input, which the proptests (including the big-endian target) verify.
- Making `source()` always return `None` (or a constant) to satisfy leaf tests while breaking the wrapper-error `source` tests — no single shortcut satisfies both leaf and nested cases.
- Stubbing `Display` to emit the literal strings the tests compare against without deriving them from the error's actual field values (would break for other field values / proptests).
- Deleting, `#[ignore]`-ing, or gating out the listed tests, or weakening assertions.
- Removing the big-endian CI target or the `PROPTEST_CASES` passthrough to avoid exercising the endianness path.
- Bypassing bounded-newtype range checks (e.g. `unsafe`-constructing out-of-range values) so range tests appear to pass while the invariant is actually unenforced.
- Implementing "lax" parsers as identical to strict parsers (or vice versa) so one test group passes at the expense of the semantic distinction.

# Success criteria

- The workspace builds on default features and with `--no-default-features`, in both `std` and `no_std`/`alloc` configurations.
- The crate builds and its tests pass on a **big-endian** target (e.g. `powerpc64-unknown-linux-gnu`) as well as little-endian, confirming the checksum and all multi-byte field handling are endianness-correct.
- All listed `fail_to_pass` tests pass, specifically:
  - the full `checksum::*` suite (both word-width helpers, the `Sum16BitWords` accumulator, add/fold/ones-complement/no-zero, `u32_u16_comparison`);
  - `compositions_tests::test_compositions` and `test_packet_slicing_panics`;
  - the `defrag::*` range/buffer/payload/pool/error tests;
  - the entire `err::*` trait-conformance suite (`debug`, `fmt`/`display`, `source`, `clone_eq_hash`, ordering, `from`, accessors, `add_slice_offset`) across arp, ip, ipv4, ipv6, ip_auth, ip_exts, ipv4_exts, ipv6_exts, io, and the top-level error types.
- No previously-passing behavior regresses; the public API surface remains coherent and documented, and the version/link references are consistently updated to `0.20.3`.