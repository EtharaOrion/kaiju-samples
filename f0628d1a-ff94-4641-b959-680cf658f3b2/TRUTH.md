# TRUTH.md

## Problem

The repository is a Go implementation of the `github.com/google/uuid` package. All exported functionality has been replaced with stubs that return zero values (each body contains a `_ = "STUB: not implemented"` marker). The task is to implement every stubbed function so that the package behaves as a correct, RFC 9562 / RFC 4122–compatible UUID library.

A `UUID` is a fixed-size `[16]byte` value. The package must support:
- Parsing / formatting UUIDs in the canonical text form and related encodings.
- Generating UUIDs of versions 1, 2 (DCE), 3 (MD5), 4 (random), 5 (SHA-1), 6, and 7.
- Time / clock-sequence / node handling for time-based versions.
- `encoding.TextMarshaler/Unmarshaler`, `encoding.BinaryMarshaler/Unmarshaler`, `json` marshaling, and SQL `driver.Valuer` / `sql.Scanner`.
- A nullable wrapper type `NullUUID`.

The stubbed files are: `dce.go`, `hash.go`, `marshal.go`, `node.go`, `node_js.go`, `node_net.go`, `null.go`, `sql.go`, `time.go`, `util.go`, `uuid.go`, `version1.go`, `version4.go`, `version6.go`, `version7.go`. The existing test suite (see fail_to_pass list) must pass; no source of truth beyond the tests and standard UUID semantics is provided.

## Behavioral contract

Group the required externally-observable behaviors by concern.

### Core type, parsing, and formatting (`uuid.go`, `util.go`)
- `Parse` must accept all common UUID textual forms and return a matching `UUID`:
  - canonical 36-char `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`,
  - the same wrapped in braces `{...}` (38 chars),
  - the `urn:uuid:` prefixed form (45 chars),
  - the unhyphenated 32 hex-digit form.
  Invalid length or invalid hex must yield a descriptive error and the zero UUID.
- `ParseBytes` behaves identically to `Parse` but on a `[]byte`, without allocating a string.
- `MustParse` returns the `UUID` or panics on error.
- `FromBytes` builds a `UUID` from exactly 16 bytes; any other length is an error.
- `Must` unwraps a `(UUID, error)` pair, panicking on error.
- `String()` produces the canonical lowercase hyphenated 36-char form.
- `URN()` produces `urn:uuid:` + canonical form.
- `Variant()` and `Version()` decode the variant and version fields; `Version.String()` and `Variant.String()` produce human-readable names.
- `Validate` reports whether a textual value is a well-formed UUID (same acceptance rules as `Parse`) returning only an error (nil when valid).
- Length/format validation helpers must classify wrong-length input distinctly (a wrong-length error is recognizable, e.g. via an exported sentinel/predicate used by `TestWrongLength` / `TestIsWrongLength`).
- Hex encoding/decoding helpers (`encodeHex`, `decodeCanonical`, or equivalent) underpin the above and must round-trip correctly. `TestCoding` and `TestConstants` check encode/decode consistency and constant values.
- An enable/disable switch controlling whether `Parse`/`ParseBytes` accepts the brace and urn forms strictly may exist; behavior must match the default (lenient acceptance of all listed forms).

### Random source and pooling (`version4.go`, `uuid.go`)
- `New` / `NewString` return a random (Version 4) UUID; `NewString` returns its string form. `New` panics if the random source fails.
- `NewRandom` returns `(UUID, error)` using the configured reader; version nibble = 4, variant bits = RFC (10xx).
- `NewRandomFromReader` uses a caller-supplied `io.Reader`.
- `SetRand(io.Reader)` replaces the global randomness source; passing `nil` restores `crypto/rand`. `TestSetRand`, `TestBadRand`, `TestRandomFromReader` verify determinism/error propagation.
- A batching/pool mode (`EnableRandPool` / `DisableRandPool`) must draw random bytes from an internal buffer while still yielding valid V4 UUIDs. `TestRandPool`, `TestRandomUUID_Pooled` verify correctness with pooling on.

### Time, clock sequence, node (`time.go`, `node.go`, `node_net.go`, `node_js.go`, `version1.go`)
- A `Time` type represents 100-ns intervals since the Gregorian epoch (Oct 15 1582). `GetTime()` returns the current `Time` and clock sequence, advancing state safely under concurrency. `(Time).UnixTime()` converts back to seconds+nanoseconds relative to the Unix epoch.
- `ClockSequence()` returns the current 14-bit clock sequence, initializing it randomly on first use; `SetClockSequence(n)` sets it (a negative value forces a fresh random value). Clock-sequence access must be race-free (`TestClockSeq`, `TestClockSeqRace`).
- Node identity:
  - `NodeID()` returns a 6-byte copy of the current node id, lazily initializing it (from a hardware interface, or a random multicast-flagged value when none is available).
  - `SetNodeID([]byte)` sets the node id from the first 6 bytes (returns false if fewer than 6 bytes) and marks the interface name as user-set.
  - `NodeInterface()` returns the interface name the node id came from (`"user"`, `"random"`, or a real interface name).
  - `SetNodeInterface(name)` selects a named interface's hardware address; with `name == ""` it never fails (falls back to random). Returns false only when a *named* interface can't be found.
  - Platform split: the non-`js` build enumerates real network interfaces (caching the list, requiring ≥6-byte hardware addresses); the `js` build returns empty values to avoid pulling in `net`.
  - `(UUID).NodeID()` extracts the 6-byte node field (bytes 10–15) from a UUID.
- `NewUUID()` (Version 1) composes time-low/mid/hi, clock sequence, and node into a UUID, sets version 1 and RFC variant; the time-based fields must decode back via `(UUID).Time()`, `(UUID).ClockSequence()`, `(UUID).NodeID()` (`TestVersion1`, `TestNode`, `TestNodeAndTime`, `TestNodeID`, `TestGetTime`).

### Version 2 / DCE (`dce.go`)
- `NewDCESecurity(domain, id)` builds a V1 UUID then overwrites version to 2, byte 9 to the domain, and bytes 0–3 to the big-endian id.
- `NewDCEPerson()` = `NewDCESecurity(Person, uid)`; `NewDCEGroup()` = `NewDCESecurity(Group, gid)` using `os.Getuid`/`os.Getgid`.
- `(UUID).Domain()` reads byte 9; `(UUID).ID()` reads big-endian bytes 0–3. `Domain.String()` names Person/Group/Org and formats unknown domains. (`TestDCE`.)

### Hash-based V3/V5 (`hash.go`)
- Package-level namespace UUIDs (`NameSpaceDNS/URL/OID/X500`) parsed from their well-known values, plus `Nil` (all zeros) and `Max` (all 0xFF).
- `NewHash(h, space, data, version)` resets the hash, writes `space` then `data`, copies the first 16 sum bytes into a UUID, sets the version nibble to `version & 0xf` and RFC variant bits.
- `NewMD5` = `NewHash(md5.New(),…,3)`; `NewSHA1` = `NewHash(sha1.New(),…,5)`. (`TestMD5`, `TestSHA1`.)

### Version 6 & 7 (`version6.go`, `version7.go`)
- `NewV6()` produces a V6 UUID: it reorders the Gregorian timestamp so the high bits are most significant (time-ordered), sets version 6 and RFC variant, and fills clock-seq/node like V1.
- `NewV7()` / `NewV7FromReader` produce V7 UUIDs: a 48-bit Unix-millisecond timestamp in the leading bytes, version 7, RFC variant, remaining bits random. V7 generation must be monotonic within the same millisecond (a sub-millisecond/sequence counter guarantees strictly increasing ordering), including a strict variant. (`TestVersion6`, `TestVersion7`, `TestVersion7_pooled`, `TestVersion7FromReader`, `TestVersion7Monotonicity`, `TestVersion7MonotonicityStrict`.)
- Helpers to construct V6 from a specific time and to generate many unique V6 UUIDs must be present (`TestNewV6WithTime`, `TestNewV6FromTimeGeneratesUniqueUUIDs`).

### Encoding interfaces (`marshal.go`, `null.go`, `sql.go`)
- `(UUID).MarshalText` → canonical 36-byte form; `UnmarshalText` parses via `ParseBytes` and reports parse errors.
- `(UUID).MarshalBinary` → the raw 16 bytes; `UnmarshalBinary` requires exactly 16 bytes else error.
- JSON of a `UUID` uses its text form (a quoted canonical string); unmarshaling accepts that form. (`TestJSON`, `TestJSONUnmarshal`.)
- `(*UUID).Scan(src)` accepts `nil` (leaves the UUID as zero/Nil), a string (parsed), and `[]byte` (16 raw bytes copied, or hex text parsed depending on length); unsupported types error. `(UUID).Value()` returns the canonical string. (`TestScan`, `TestValue`.)
- `NullUUID` wraps `UUID` + `Valid bool` and implements Scan/Value, Binary, Text, and JSON marshaling where an invalid (null) value maps to SQL `nil` / JSON `null` / empty binary / the literal `null` text, and a valid value delegates to the underlying `UUID`. Unmarshaling `null`/nil sets `Valid=false`; a successful parse sets `Valid=true`. (All `TestNullUUID*`.)

### Fuzz targets
- `Parse`, `ParseBytes`, and `FromBytes` must never panic on arbitrary input and must return an error (not a spurious success) for malformed data. (`FuzzParse`, `FuzzParseBytes`, `FuzzFromBytes`.)

## Solution decomposition

Reasonable sub-goals, roughly in dependency order:

1. **Byte/hex primitives in `util.go`** — random-bit filling (`randomBits`) and hex encode/decode (`xtob`/`encodeHex`/`decodeCanonical`) that all higher layers reuse.
2. **Core `uuid.go`** — the `UUID` type constants, `Parse`/`ParseBytes`/`Validate`/`FromBytes`/`Must*`, `String`/`URN`, `Variant`/`Version` accessors and their `String()`s, the global rand reader plumbing (`SetRand`, `New`, `NewString`), and the wrong-length error handling. Everything else depends on parsing and the rand source.
3. **Random V4 (`version4.go`)** — `NewRandom`, `NewRandomFromReader`, and the rand-pool implementation.
4. **Node & platform files (`node.go`, `node_net.go`, `node_js.go`)** — mutex-guarded node/interface state and platform-specific hardware lookup.
5. **Time/clock (`time.go`)** — `GetTime`, `ClockSequence`/`SetClockSequence`, `Time.UnixTime`, race-safe state.
6. **Time-based generators (`version1.go`, `version6.go`, `version7.go`, `dce.go`)** — built on 4–5.
7. **Hash-based (`hash.go`)** — namespaces plus `NewHash`/`NewMD5`/`NewSHA1`.
8. **Encoding (`marshal.go`, `sql.go`, `null.go`)** — built on parsing and formatting.

## Solution space

- **Parsing strategy:** you may parse via table-driven hex decode, via `strings`/`hex` stdlib helpers, or manual byte arithmetic. Any implementation that accepts exactly the canonical, braced, `urn:uuid:`, and 32-digit forms (and rejects others with an error) is valid.
- **Wrong-length signaling:** the diff exposes wrong-length detection; a valid solution may use an exported sentinel error type/value, a boolean predicate, or wrap length errors — whatever the accompanying tests reference. Match the test's expectation for how a wrong-length case is identified.
- **Rand pool:** the pool can be a fixed-size buffer refilled from the reader, or any scheme that yields valid V4 UUIDs indistinguishable from unpooled ones. Enabling/disabling must be safe and reversible.
- **Clock sequence / time state:** may be guarded by a `sync.Mutex` or `sync/atomic`; correctness under concurrency is what matters, not the mechanism.
- **V7 monotonicity:** acceptable approaches include a per-millisecond incrementing counter stored in the sub-millisecond bits, borrowing extra random bits as a sequence, or tracking the last timestamp and bumping it — as long as successive V7 values are non-decreasing (and strictly increasing where the strict test requires).
- **V6 timestamp:** compute from `GetTime` (reordered) or by transforming a V1 layout; either is fine if the decoded time and version 6 are correct.
- **Node fallback:** when no hardware address is available, generating a random node id with the multicast bit set (or plain random bits) is acceptable per RFC; tests only require a valid non-zero node.
- **Hash version bits:** `NewHash` may take the version as an int and mask it; the important invariant is correct version + variant nibbles and copying the first 16 hash bytes.
- **SQL `Scan`:** handling `string` and `[]byte` (both 16-byte binary and textual) covers the contract; you may additionally handle other types, but must error on truly unsupported inputs.

## Known pitfalls

- **Variant bits vs. version bits:** version goes in the high nibble of byte 6; the RFC variant goes in the top two bits of byte 8 (`(b & 0x3f) | 0x80`). Setting these in the wrong byte or with the wrong mask is the most common failure.
- **Byte order:** DCE `ID` and V7 timestamps use big-endian; getting endianness or byte offsets wrong breaks `TestDCE`/`TestVersion7`.
- **`UnmarshalBinary` length check:** must reject anything other than exactly 16 bytes with an error, not silently truncate.
- **`UnmarshalText`/`Scan` must propagate parse errors** rather than swallowing them (tests assert on error for bad input).
- **NullUUID null semantics:** invalid null must serialize to SQL `nil`, JSON `null`, the byte string `null` for text, and an empty (nil) byte slice for binary — and unmarshaling those must set `Valid=false`. Delegation to the inner UUID only happens when `Valid`.
- **Concurrency:** `GetTime`, clock sequence, and node state are shared globals; unsynchronized access fails the race tests (`TestClockSeqRace`, `TestClockSeq` under `-race`).
- **`SetRand(nil)` must restore the default `crypto/rand`**, not leave a nil reader (would break subsequent `New`).
- **`New` panics on rand failure** whereas `NewRandom` returns an error — don't conflate them.
- **Fuzz safety:** parsing must not index out of bounds or panic on empty/short/garbage input; guard lengths before slicing.
- **Rand pool state** must be reset/consistent so pooled and unpooled generation both produce well-formed UUIDs, and toggling the pool at runtime is safe.
- **Build tags:** `node_js.go` and `node_net.go` are mutually exclusive via build constraints; both must compile and provide `getHardwareInterface` with matching signatures. Don't accidentally make both active or neither.
- **V7 monotonicity within a millisecond:** naive "timestamp + random" can produce out-of-order values; the sequence/counter logic is required for the monotonicity tests.

## Cheat surface

The following would make tests pass without genuinely implementing the spec and must be treated as non-solutions:

- Hard-coding expected outputs for specific test inputs (e.g., returning a fixed UUID string that a particular assertion expects) rather than computing from input.
- Detecting the test's known random seed / reader and returning precomputed values.
- Modifying, deleting, skipping, or weakening the tests, fuzz seed corpora, or their assertions.
- Replacing `crypto/rand` with a predictable constant just to satisfy determinism-related assertions (except where `SetRand` legitimately installs a caller reader).
- Leaving stub markers but stubbing out the interface methods to return canned values that only coincidentally satisfy the specific tested cases.
- Reintroducing removed artifacts or bypassing build tags to dodge the platform split.

Genuine implementations must derive every result from the actual input bytes, configured randomness source, time, and node state.

## Success criteria

- All listed fail_to_pass tests pass, including the fuzz targets run as tests: `TestJSON`, `TestJSONUnmarshal`, all `TestNullUUID*`, `TestClockSeqRace`, `TestScan`, `TestValue`, `TestGetTime`, `TestUUID`, `TestFromBytes`, `TestConstants`, `TestRandomUUID`, `TestRandomUUID_Pooled`, `TestNew`, `TestClockSeq`, `TestCoding`, `TestVersion1`, `TestNode`, `TestNodeAndTime`, `TestMD5`, `TestSHA1`, `TestNodeID`, `TestDCE`, `TestBadRand`, `TestSetRand`, `TestRandomFromReader`, `TestRandPool`, `TestWrongLength`, `TestIsWrongLength`, `TestValidate`, `TestVersion6`, `TestVersion7`, `TestVersion7_pooled`, `TestVersion7FromReader`, `TestVersion7Monotonicity`, `TestVersion7MonotonicityStrict`, `TestNewV6WithTime`, `TestNewV6FromTimeGeneratesUniqueUUIDs`, `FuzzParse`, `FuzzParseBytes`, `FuzzFromBytes`.
- The package builds cleanly under both the default (`net`) and `js` build tags.
- The suite passes under the race detector (the clock-sequence race test implies `-race`).
- No `"STUB: not implemented"` markers remain and no function returns a placeholder zero value where a computed result is required.
- No test files or fixtures were altered to force passage.