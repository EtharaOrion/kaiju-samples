# Implement `riker-rs/riker`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `riker-rs/riker`
- Source directory to implement: `src/`
- Test command: `cargo test` (run against `tests`)
- Specification / docs: https://docs.rs/riker

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

ActorSelection A selection represents part of the actor heirarchy, allowing messages to be sent to all actors in the selection.

ActorUri An ActorUri represents the location of an actor, including the path and actor system host.

All A channel topic representing all topics * BasicActorRef A lightweight, un-typed reference to interact with its underlying actor instance through concurrent messaging.

Channel A specialized actor for providing Publish/Subscribe capabilities for user level messages Context Provides context, including the actor system during actor execution.

DeadLetter EventsChannel A specialized channel that publishes messages as system messages Props Provides instances of ActorProducer for use when creating Actors (actor_of_props).

Publish RestartError Error type when an actor fails to restart.

Subscribe Topic When publishing a message to a channel a Topic is provided.

Strategy Supervision strategy SysTopic System topics used by the event_stream channel Actor ActorArgs riker   ▼  ▼  docs.rs ▼ Rust ▼ ActorFactory ActorFactoryArgs ActorProducer Represents the underlying Actor factory function for creating instances of Actor .

ActorRefFactory Produces ActorRefs. actor_of blocks on the current thread until the actor has successfully started or failed to start.

ActorReference ActorSelectionFactory Receive Receive and handle a specific message type Tell TmpActorRefFactory Produces ActorRefs under the temp guardian actor.
