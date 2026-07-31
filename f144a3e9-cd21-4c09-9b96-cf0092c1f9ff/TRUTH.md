# TRUTH.md

## Problem

The `btclib` repository is a pure-Python Bitcoin library whose source modules have been reduced to stubs: function/method bodies were replaced with `pass` (or otherwise emptied), while module layout, public names, signatures, and the test suite remain intact. The task is to restore correct, working implementations of every stubbed function, class, and method across the library so that the enumerated `fail_to_pass` tests succeed.

The scope spans the full cryptographic and serialization stack of a Bitcoin toolkit:

- Low-level encodings (`base58`, `bech32`, `b32`, `b58`, `var_int`, `var_bytes`, `utils`, `hashes`).
- Elliptic-curve math over secp256k1 (`ec/curve*`, `sec_point`, `number_theory`), including affine/Jacobian arithmetic and scalar multiplication algorithms.
- Signature schemes: ECDSA (`ecc/dsa`), Schnorr/BIP340 (`ecc/ssa`), Bitcoin message signing (`ecc/bms`), plus deterministic nonces (`rfc6979_nonce`, `bip340_nonce`), Diffie–Hellman, Pedersen commitments, Borromean rings, sign-to-contract.
- Key management: BIP32 HD wallets and paths, key origin, SLIP132; WIF/address conversions (`to_prv_key`, `to_pub_key`).
- Mnemonics: BIP39, Electrum, shared entropy handling.
- Script layer: `script`, `script_pub_key`, `sig_hash`, `taproot`, `witness`, tapscript op codes, and the script execution engine.
- Transaction and block structures (`tx/*`, `block/*`) and PSBT (`psbt/*`).
- Supporting infrastructure: `alias`, `amount`, `network`, `descriptors`, `exceptions`, and CI workflow YAML files.

A correct solution reproduces the documented behavior of each module so that Bitcoin test vectors (BIP32, BIP39, BIP174/371, BIP340, RFC6979, etc.) round-trip and validate exactly.

## Behavioral contract

Implementations must satisfy the observable behavior exercised by the tests. Key contracts by area:

**Encodings & utilities**
- `base58` / `bech32` encode/decode must be exact inverses and reject malformed input (bad checksum, wrong length, invalid characters) by raising the library's own exception types.
- `var_int` / `var_bytes` must serialize and parse Bitcoin's compact-size and length-prefixed byte fields, consuming exactly the right number of bytes from a stream.
- `utils.bytes_from_octets` must accept both `bytes` and hex strings (with optional embedded spaces) and enforce permitted lengths when a length constraint is supplied.
- `hashes` must provide hash160/hash256 and the tagged/derived hashes needed by addresses and scripts.
- `amount` must convert between satoshis and BTC `Decimal` values without floating-point contamination, normalize canonical decimals, and reject out-of-range or non-integer amounts.

**Elliptic curve**
- Curve arithmetic must produce correct point addition, doubling, negation, on-curve checks, affine↔Jacobian conversions, and equality (accounting for the projective scaling of Jacobian coordinates).
- Every scalar-multiplication variant (double-and-add, Montgomery ladder, fixed window, sliding window, wNAF, cached multiples, endomorphism-based, multi/double mult) must yield identical results for the same input and correctly handle the point at infinity and scalars reduced modulo the group order.
- SEC point serialization must handle compressed/uncompressed forms and the infinity encoding.

**Signatures**
- ECDSA and Schnorr signing/verification must match the standard test vectors, including deterministic nonce generation (RFC6979 for ECDSA, BIP340 for Schnorr) and low-`s` / even-`y` normalization where the standard requires it.
- Public-key recovery, private-key cracking (on nonce reuse), signature (de)serialization (DER, BIP340, compact BMS), and the input-type polymorphism (accepting keys/messages in multiple representations) must all behave as the tests expect.
- Optional libsecp256k1 acceleration paths must produce results identical to the pure-Python paths (and degrade gracefully when the native library is unavailable).

**Keys, mnemonics, HD wallets**
- BIP32 extended-key (de)serialization, hardened/non-hardened child derivation, public-key-only derivation, and account/path derivation must match BIP32 vectors, including detection of invalid xkeys.
- Derivation-path parsing/formatting (`der_path`, `key_origin`) must round-trip between string and integer index forms, with correct hardened markers.
- BIP39/Electrum mnemonic ↔ entropy ↔ seed conversions, and entropy validation/rolls collection, must match their respective vectors.

**Scripts, transactions, blocks, PSBT**
- `script` must serialize/parse opcodes, minimal pushes, integer encodings, and OP_N forms, with equality and concatenation semantics.
- `script_pub_key` must recognize and construct standard output types (p2pk, p2pkh, p2wpkh, p2sh, p2wsh, p2ms with BIP67 ordering, nulldata, p2tr) and derive their addresses.
- `sig_hash` must compute legacy, SegWit v0, and taproot sighashes for all hash-type flags (including the SIGHASH_SINGLE bug reproduction).
- `tx`/`block` structures must (de)serialize, compute ids/hashes, and validate; `to_dict`/`from_dict` JSON round-trips must be lossless.
- PSBT must implement BIP174/BIP371 creation, combination/merge/join, finalization, extraction, signing, ordering/shuffling, hash-preimage fields, and unknown-field preservation.

**Error handling**
- Invalid inputs must raise the library's specific exception classes (e.g., value/type/run-time variants defined in `exceptions.py`) rather than generic errors, because many tests assert on exception type and sometimes message content.

**CI workflows**
- The added GitHub Actions YAML files are configuration only; they do not affect the Python test outcomes and merely need to be syntactically valid YAML.

## Solution decomposition

Because modules depend on one another, restore them roughly bottom-up:

1. **Foundations**: `exceptions`, `alias`, `utils`, `number_theory`, `hashes`, `var_int`, `var_bytes`, `amount`. These have no intra-library dependencies and unlock everything else.
2. **Encodings**: `base58`, `bech32`, then `b58`/`b32` address layers, and `network` (network parameter lookup by key/value).
3. **Elliptic curve core**: `curve_group`, `curve_group_2`, `curve_group_f`, `curve`, `sec_point`, and the ec `libsecp256k1` shim.
4. **Key conversion**: `to_prv_key`, `to_pub_key` (multi-format key normalization used pervasively).
5. **Signatures**: `rfc6979_nonce`, `bip340_nonce`, then `dsa`, `ssa`, `bms`, followed by `dh`, `pedersen`, `borromean`, `sign_to_contract`, and the ecc `libsecp256k1` shim.
6. **HD/keys/mnemonics**: `bip32`, `der_path`, `key_origin`, `slip132`; `entropy`, `mnemonic`, `bip39`, `electrum`.
7. **Scripts**: `script`, `op_codes_tapscript`, `witness`, `taproot`, `script_pub_key`, `sig_hash`, then the `script/engine/*` interpreter and `descriptors`.
8. **Transactions/blocks/PSBT**: `out_point`, `tx_in`, `tx_out`, `tx`, `block_header`, `block`, then `psbt_utils`, `psbt_out`, `psbt_in`, `psbt`.

Within each module, the primary sub-goals are: correct (de)serialization that consumes/produces the exact byte layout, validation that raises the right exception types, and JSON dict round-trips where dataclasses expose `to_dict`/`from_dict`.

## Solution space

Multiple correct routes exist; a different-but-valid implementation should not be penalized for the following choices:

- **Scalar-multiplication internals**: the specific windowing/NAF/ladder implementations may differ in structure as long as all variants agree with each other and with the reference multiplication on all inputs (including INF and reduced scalars). Precomputation/caching strategies are free to vary.
- **Coordinate representation details**: any consistent affine/Jacobian handling is acceptable provided equality treats projectively-equal points as equal and infinity is detected correctly.
- **Nonce and hashing helpers** may be factored differently, provided the deterministic outputs match RFC6979/BIP340 vectors bit-for-bit.
- **libsecp256k1 acceleration** may be implemented, stubbed to always fall back, or detected at runtime — any approach passes as long as pure-Python results are correct and native/py results agree when native is present.
- **Encoding helpers** (base conversion, checksum computation) may be reused across bech32/base58 or duplicated; internal helper names are unconstrained.
- **Serialization plumbing** may use `BytesIO` streams, slicing, or incremental parsing; only the resulting bytes and consumed lengths matter.
- **Dataclass vs. plain class** structure is fine as long as the public attributes, constructors, `assert_valid`, and dict/serialization methods behave as tests expect.
- **CI YAML** contents (runner matrix, action versions) are irrelevant to test success; any valid YAML satisfies the file-existence requirement.
- **Error messages**: exact wording is only required where a test matches on message text; otherwise only the exception *type* matters.

## Known pitfalls

- **Wrong exception types**: tests use `pytest.raises` with the library's specific classes; raising a bare `ValueError`/`Exception` will fail. Validation must go through `exceptions.py` types.
- **Infinity handling**: point-at-infinity in affine (`INF`, `y==0`) and Jacobian (`INFJ`, `z==0`) forms must be recognized everywhere; forgetting this breaks negation, multiplication, and equality tests.
- **Jacobian equality**: comparing raw tuples is wrong — points equal in affine space have many Jacobian representations; equality must account for the `Z` scaling factor.
- **Signature normalization**: ECDSA low-`s` enforcement and Schnorr even-`y` / x-only public keys are mandatory to match vectors; skipping normalization yields valid-but-nonmatching signatures that fail vector comparison.
- **Deterministic nonce fidelity**: RFC6979/BIP340 nonce derivation must reduce modulo the group order and use the exact hashing scheme; small deviations produce entirely different signatures.
- **Byte-exact serialization**: var_int compact-size boundaries, minimal script pushes, little- vs big-endian fields, and length prefixes must be precise; off-by-one or endianness errors cascade into tx/block/psbt id mismatches.
- **SIGHASH edge cases**: legacy SIGHASH_SINGLE "bug" (index ≥ number of outputs returns a fixed hash), ANYONECANPAY input selection, and per-flag output/input pruning must be reproduced exactly.
- **BIP67 / lexicographic ordering**: p2ms keys and PSBT input/output ordering follow defined sort rules; naive ordering breaks the corresponding tests.
- **Hex/bytes polymorphism**: `bytes_from_octets` and key/message acceptors must handle both hex strings (possibly space-separated) and raw bytes, and strip whitespace for address/WIF/xkey strings but not for messages.
- **Amount arithmetic**: using floats or skipping `Decimal` normalization causes precision/canonicalization failures; range checks must reject dust/overflow.
- **Address version/network coupling**: derived addresses must select prefixes/HRP from the correct network; mismatched network lookup yields wrong or rejected addresses.
- **Unknown-field preservation in PSBT**: global/input/output unknown key-value pairs must survive combination, merge, and re-serialization.
- **Circular/ordering imports**: restoring modules out of dependency order can surface import-time failures; ensure foundational modules are correct first.

## Cheat surface

The following would make tests pass superficially or trivially without a genuine implementation, and must be treated as non-solutions:

- Hard-coding expected outputs keyed to specific test-vector inputs (e.g., returning a memorized signature, address, xkey, sighash, or serialized blob for the exact inputs the tests use) rather than computing them.
- Detecting test input values and branching to canned results.
- Overriding, monkeypatching, weakening, or skipping the tests, or editing the test files / fixtures.
- Replacing signature verification with functions that always return `True`, or validation that never raises.
- Catching-all exceptions and re-raising the type a test expects without actually performing the guarded computation.
- Importing an external Bitcoin library and delegating wholesale to it to sidestep implementing the library's own logic (beyond the intended optional libsecp256k1 acceleration, which must still agree with a genuine pure-Python path).
- Making CI YAML or unrelated files carry logic that shims test results.

A legitimate solution computes results from first principles / standard algorithms so that it would generalize to inputs not present in the test suite.

## Success criteria

- Every test in the `fail_to_pass` list passes when the suite is run, without modifying test files, fixtures, or configuration to alter assertions.
- Implementations are input-general: they produce correct results for arbitrary valid inputs, not merely the specific vectors in the tests, and reject invalid inputs with the library's designated exception types.
- All scalar-multiplication variants, serialization/deserialization pairs, and encode/decode pairs are mutually consistent and round-trip losslessly.
- Standard Bitcoin test vectors (BIP32, BIP39, Electrum, BIP174/BIP371 PSBT, BIP340 Schnorr, RFC6979 ECDSA, SEC point, legacy/SegWit/taproot sighash) match byte-for-byte.
- No previously passing behavior is broken (no regressions), and modules import cleanly in dependency order.
- The added CI workflow files exist and are valid YAML (their content does not otherwise affect correctness).