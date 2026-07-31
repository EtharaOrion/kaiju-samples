# Implement `komora-io/concurrent-map`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `komora-io/concurrent-map`
- Source directory to implement: `src/`
- Test command: `cargo test` (run against `tests`)
- Specification / docs: https://github.com/Zahgon/concurrent-map

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

docs docs passing passing Lock-free linearizable map.

get , insert , cas , remove , iter , range , get_gt , get_gte , get_lt , get_lte , first , last , pop_first , pop_last fully lock-free node splits and merges based on the sled battle-tested implementation.

concurrent-map can be though of in some ways as a simplified, in-memory sled that supports high-level types.

initially designed for use in sled's next generation object store, marble.

The ConcurrentMap allows users to tune the tree fan-out ( FANOUT ) and the underlying memory reclamation granularity ( LOCAL_GC_BUFFER_SIZE ) for achieving desired performance properties. The defaults are pretty good for most use cases but if you want to squeeze every bit of performance out for your particular workload, tweaking them based on realistic measurements may be beneficial. See the ConcurrentMap docs for more details.

If you want to use a custom key type, you must implement the Minimum trait, allowing the left-most side of the tree to be created before inserting any data.

This is an ordered data structure, and supports very high throughput iteration over lexicographically sorted ranges of values. If you are looking for simple point operation performance, you may find a better option among one of the many concurrent hashmap implementations that are floating around. Pay for what you actually use :) The minimum supported rust version (MSRV) is 1.70 .
