# Implement `orion-rs/orion`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `orion-rs/orion`
- Source directory to implement: `src/`
- Test command: `cargo test` (run against `tests`)
- Specification / docs: https://docs.rs/orion

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

aead safe_api Authenticated secret-key encryption.

auth safe_api Message authentication.

errors Errors for Orion’s cryptographic operations.

hash safe_api Hashing.

hazardous [Caution] Low-level API.

kdf safe_api Key derivation.

kex safe_api Ephemeral key exchange.

pwhash safe_api Password hashing and verification.

util Utilities such as constant-time comparison.

A usable pure-Rust cryptography library.

Authenticated secret-key encryption orion::aead offers authenticated secret-key encryption using XChaCha20Poly1305.

Password hashing and verification orion::pwhash offers password hashing and verification using Argon2i.

Key derivation orion::kdf offers key derivation using Argon2i.

Message authentication orion::auth offers message authentication and verification using BLAKE2b.

Hashing orion::hash offers hashing using BLAKE2b.

Key exchange orion::kex offers ephemeral key exchange using X25519 and BLAKE2b.

A note on no_std: When Orion is used in a no_std context, the high-level API is not available, since it relies on access to the systems random number generator.

More information about Orion is available in the wiki.
