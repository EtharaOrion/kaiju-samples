# Implement `http-rs/async-h1`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `http-rs/async-h1`
- Source directory to implement: `src/`
- Test command: `cargo test` (run against `tests`)
- Specification / docs: https://github.com/Zahgon/async-h1

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Asynchronous HTTP/1.1 parser.

crates.io v2.3.4 downloads 6.5M docs latest This crate uses #![forbid(unsafe_code)] to ensure everything is implemented in 100% Safe Rust.

Given the rapidly-improving nature of async Rust, async-h1 only guarantees it will work on the latest stable Rust compiler. Currently async-h1 compiles on rustc 1.40.0 and above, but we reserve the right to upgrade the minimum Rust version outside of major releases. If upgrading stable compiler versions is an issue we recommend pinning the version of async- h1 .

Want to join us? Check out our "Contributing" guide and take a look at some of these issues: Issues labeled "good first issue" Issues labeled "help wanted" async-h1 API Docs | Releases | Contributing Installation $ cargo add async-h1 Safety Minimum Supported Rust Version Contributing License Licensed under either of Apache License, Version 2.0 or MIT license at your option.

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in this crate by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any additional terms or conditions.
