# Implement `asynchronics/nexosim`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `asynchronics/nexosim`
- Source directory to implement: `nexosim/src/`
- Test command: `cargo test -p nexosim` (run against `nexosim`)
- Specification / docs: https://docs.rs/nexosim

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

A high-performance, discrete-event computation framework for system simulation.

NeXosim is a developer-friendly, yet highly optimized software simulator able to scale to very large simulation with complex time-driven state machines.

It promotes a component-oriented architecture that is familiar to system engineers and closely resembles flow-based programming: a model is essentially an isolated entity with a fixed set of typed inputs and outputs, communicating with other models through message passing via connections defined during bench assembly. Unlike in conventional flow-based programming, request-reply patterns are also possible.

NeXosim leverages asynchronous programming to perform auto-parallelization in a manner that is fully transparent to model authors and users, achieving high computational throughput on large simulation benches by means of a custom multi-threaded executor.

A practical overview Simulating a system typically involves three distinct activities: 1. the design of simulation models for each node of the system, 2. the assembly of a simulation bench from a set of models, performed by inter-connecting model ports, 3. the execution of the simulation, managed through periodical increments of the simulation time and by exchange of messages with simulation models.

The following sections go through each of these activities in more details.

Authoring models Models can contain four kinds of ports: output ports, which are instances of the Output type and can be used to broadcast a message, requestor ports, which are instances of the UniRequestor or Requestor types and can be used to send/broadcast a message and receive a single reply (UniRequestor) or an iterator over the replies of all connected replier ports (Requestor), input ports, which are synchronous or asynchronous methods that implement the InputFn trait and take an &mut self argument, a message argument and, optionally, &Context and &Model::Env arguments, replier ports, which are similar to input ports but implement the ReplierFn trait and return a reply.

Messages that are broadcast by an output port to an input port are referred to as events, while messages exchanged between requestor and replier ports are referred to as requests and replies.

Models must implement the Model trait, which is most conveniently done by annotating the impl block of the model with the #[Model] macro. This trait allows models to specify a custom Model::init method that is guaranteed to run exactly once when the simulation is initialized, i.e.

after all models have been connected but before the simulation starts.

More complex models can be built with the ProtoModel trait. The ProtoModel::build method makes it possible to: build the final Model from a builder (the model prototype), perform possibly blocking actions when the model is added to the simulation rather than when the simulation starts, such as establishing a network connection or configuring hardware devices, connect submodels and add them to the simulation.
