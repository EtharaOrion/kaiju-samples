# Implement `zalando-incubator/graphql-jit`

You are given a TypeScript repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that throws `new Error("STUB")` on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, classes, interfaces, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `zalando-incubator/graphql-jit`
- Source directory to implement: `src/`
- Test command: `yarn jest` (run against `src/__tests__`)
- Specification / docs: http://spec.graphql.org/draft/#sec-Language.Operations

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Current Working Draft This is the specification for GraphQL, a query language and execution engine for describing and performing the capabilities and requirements of data models for client-server applications.

A conforming implementation of GraphQL must fulfill all normative requirements described in this specification (see Conformance). The GraphQL specification is provided under the OWFa 1.0 license (see Copyright and Licensing).

GraphQL was originally created in 2012 and the development of this open standard started in 2015. It is a deliverable of the GraphQL Specification Project, established in 2019 with the Joint Development Foundation.

The GraphQL Foundation was formed in 2019 as a neutral focal point for organizations who support development of the GraphQL ecosystem. If your organization benefits from GraphQL, please consider becoming a member.

This specification is developed on GitHub at graphql/graphql-spec. Contributions are managed by the GraphQL Working Group, hosted by the GraphQL Technical Steering Committee. To learn more see the contribution guide.

GraphQL has evolved and may continue to evolve in future editions of this specification.

Previous editions of the GraphQL specification can be found at permalinks that match their release tag. The latest working draft release can be found at https://spec.graphql.org/draft.

Contents GraphQL Introduction 1 Overview 2 Language 2.1 Source Text 2.1.1 White Space 2.1.2 Line Terminators 2.1.3 Comments ☰ 2.1.4 Insignificant Commas 2.1.5 Lexical Tokens 2.1.6 Ignored Tokens 2.1.7 Punctuators 2.1.8 Names 2.2 Descriptions 2.3 Document 2.4 Operations 2.5 Selection Sets 2.6 Fields 2.7 Arguments 2.8 Field Alias 2.9 Fragments 2.9.1 Type Conditions 2.9.2 Inline Fragments 2.10 Input Values 2.10.1 Int Value 2.10.2 Float Value 2.10.3 Boolean Value 2.10.4 String Value 2.10.5 Null Value 2.10.6 Enum Value 2.10.7 List Value 2.10.8 Input Object Values 2.11 Variables 2.12 Type References 2.13 Directives 2.14 Schema Coordinates 3 Type System 3.1 Type System Extensions 3.2 Type System Descriptions 3.3 Schema 3.3.1 Root Operation Types 3.3.2 Schema Extension 3.4 Types 3.4.1 Wrapping Types 3.4.2 Input and Output Types 3.4.3 Type Extensions 3.5 Scalars 3.5.1 Int 3.5.2 Float 3.5.3 String 3.5.4 Boolean 3.5.5 ID 3.5.6 Scalar Extensions 3.6 Objects 3.6.1 Field Arguments ☰ 3.6.2 Field Deprecation 3.6.3 Object Extensions 3.7 Interfaces 3.7.1 Interface Extensions 3.8 Unions 3.8.1 Union Extensions 3.9 Enums 3.9.1 Enum Extensions 3.10 Input Objects 3.10.1 OneOf Input Objects 3.10.2 Input Object Extensions 3.11 List 3.12 Non-Null 3.12.1 Combining List and Non-Null 3.13 Directives 3.13.1 @skip 3.13.2 @include 3.13.3 @deprecated 3.13.4 @specifiedBy 3.13.5 @oneOf 3.13.6 Directive Extensions 4 Introspection 4.1 Type Name Introspection 4.2 Schema Introspection 4.2.1 The __Schema Type 4.2.2 The __Type Type 4.2.3 The __Field Type 4.2.4 The __InputValue Type 4.2.5 The __EnumValue Type 4.2.6 The __Directive Type 5 Validation 5.1 Documents 5.1.1 Executable Definitions 5.2 Operations 5.2.1 All Operation Definitions 5.2.1.1 Operation Type Existence 5.2.2 Named Operation Definitions 5.2.2.1 Operation Name Uniqueness 5.2.3 Anonymous Operation Definitions 5.2.3.1 Lone Anonymous Operation 5.2.4 Subscription Operation Definitions 5.2.4.1 Single Root Field 5.3 Fields 5.3.1 Field Selections 5.3.2 Field Selection Merging 5.3.3 Leaf Field Selections ☰ 5.4 Arguments 5.4.1 Argument Names 5.4.2 Argument Uniqueness 5.4.3 Required Arguments 5.5 Fragments 5.5.1 Fragment Declarations 5.5.1.1 Fragment Name Uniqueness 5.5.1.2 Fragment Spread Type Existence 5.5.1.3 Fragments on Object, Interface or Union Types 5.5.1.4 Fragments Must Be Used 5.5.2 Fragment Spreads 5.5.2.1 Fragment Spread Target Defined 5.5.2.2 Fragment Spreads Must Not Form Cycles 5.5.2.3 Fragment Spread Is Possible 5.5.2.3.1 Object Spreads in Object Scope 5.5.2.3.2 Abstract Spreads in Object Scope 5.5.2.3.3 Object Spreads in Abstract Scope 5.5.2.3.4 Abstract Spreads in Abstract Scope 5.6 Values 5.6.1 Values of Correct Type 5.6.2 Input Object Field Names 5.6.3 Input Object Field Uniqueness 5.6.4 Input Object Required Fields 5.7 Directives 5.7.1 Directives Are Defined 5.7.2 Directives Are in Valid Locations 5.7.3 Directives Are Unique per Location 5.8 Variables 5.8.1 Variable Uniqueness 5.8.2 Variables Are Input Types 5.8.3 All Variable Uses Defined 5.8.4 All Variables Used 5.8.5 All Variable Usages Are Allowed 6 Execution 6.1 Executing Requests 6.1.1 Validating Requests 6.1.2 Coercing Variable Values 6.2 Executing Operations 6.2.1 Query 6.2.2 Mutation 6.2.3 Subscription 6.2.3.1 Source Stream 6.2.3.2 Response Stream 6.2.3.3 Unsubscribe 6.3 Executing Selection Sets 6.3.1 Executing the Root Selection Set ☰ 6.3.2 Field Collection 6.3.3 Executing Collected Fields 6.3.4 Normal and Serial Execution 6.4 Executing Fields 6.4.1 Coercing Field Arguments 6.4.2 Value Resolution 6.4.3 Value Completion 6.4.4 Handling Execution Errors 7 Response 7.1 Response Format 7.1.1 Execution Result 7.1.2 Response Stream 7.1.3 Request Error Result 7.1.4 Response Position 7.1.5 Data 7.1.6 Errors 7.1.7 Extensions 7.1.8 Additional Entries 7.2 Serialization Format 7.2.1 JSON Serialization 7.2.2 Serialized Map Ordering A Appendix: Conformance B Appendix: Notation Conventions B.1 Context-Free Grammar B.2 Lexical and Syntactic Grammar B.3 Grammar Notation B.4 Grammar Semantics B.5 Algorithms B.6 Data Collections C Appendix: Grammar Summary C.1 Source Text C.2 Ignored Tokens C.3 Lexical Tokens C.4 Document Syntax C.5 Schema Coordinate Syntax D Appendix: Type System Definitions E Appendix: Copyright and Licensing § Index Overview 1 ☰ GraphQL is a query language designed to build client applications by providing an intuitive and flexible syntax and system for describing their data requirements and interactions.

For example, this GraphQL request will receive the name of the user with id 4 from the Facebook implementation of GraphQL.

user id 4 name

Which produces the resulting data (in JSON): "user" "name" "Mark Zuckerberg"

GraphQL is not a programming language capable of arbitrary computation, but is instead a language used to make requests to application services that have capabilities defined in this specification. GraphQL does not mandate a particular programming language or storage system for application services that implement it. Instead, application services take their capabilities and map them to a uniform language, type system, and philosophy that GraphQL encodes. This provides a unified interface friendly to product development and a powerful platform for tool-building.

GraphQL has a number of design principles: Product-centric: GraphQL is unapologetically driven by the requirements of views and the front-end engineers that write them. GraphQL starts with their way of thinking and requirements and builds the language and runtime necessary to enable that.

Hierarchical: Most product development today involves the creation and manipulation of view hierarchies. To achieve congruence with the structure of these applications, a GraphQL request itself is structured hierarchically. The request is shaped just like the data in its response. It is a natural way for clients to describe data requirements.

Strong-typing: Every GraphQL service defines an application-specific type system.

Requests are executed within the context of that type system. Given a GraphQL operation, tools can ensure that it is both syntactically correct and valid within that type system before execution, i.e. at development time, and the service can make certain guarantees about the shape and nature of the response.

Client-specified response: Through its type system, a GraphQL service publishes the capabilities that its clients are allowed to consume. It is the client that is responsible for specifying exactly how it will consume those published capabilities. These requests are specified at field-level granularity. In the majority of client-server applications written Example № 1 { ( : ) { } } Example № 2 { : { : } } ☰ without GraphQL, the service determines the shape of data returned from its various endpoints. A GraphQL response, on the other hand, contains exactly what a client asks for and no more.

Self-describing: GraphQL is self-describing and introspective. A GraphQL service’s type system can be queryable by the GraphQL language itself, which includes readable documentation. GraphQL introspection serves as a powerful platform for building common developer tools and client software libraries.

Because of these principles, GraphQL is a powerful and productive environment for building client applications. Product developers and designers building applications against working GraphQL services—supported with quality tools—can quickly become productive without reading extensive documentation and with little or no formal training. To enable that experience, there must be those that build those services and tools.

The following formal specification serves as a reference for those builders. It describes the language and its grammar, the type system and the introspection system used to query it, and the execution and validation engines with the algorithms to power them. The goal of this specification is to provide a foundation and framework for an ecosystem of GraphQL tools, client libraries, and service implementations—spanning both organizations and platforms—that has yet to be built. We look forward to working with the community in order to do that.

Clients use the GraphQL query language to make requests to a GraphQL service. We refer to these request sources as documents. A document may contain operations (queries, mutations, and subscriptions) as well as fragments, a common unit of composition allowing for data requirement reuse.

A GraphQL document is defined as a syntactic grammar where terminal symbols are tokens (indivisible lexical units).
