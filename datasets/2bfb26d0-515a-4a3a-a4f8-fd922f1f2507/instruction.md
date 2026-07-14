# Implement `grpc/grpc-go`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `grpc/grpc-go`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://grpc.io/docs/languages/go

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Go Developer stories and talks Stubbing gRPC in Go , by Jean de Klerk , Google. October 8, 2020.

Talking to Go gRPC Services Via HTTP/1  A gRPC Conf 2020 presentation by Malte Isberner, StackRox.

Last modified October 30, 2023: Fix broken link jadekler→jeanbza (#1217) (06a0803)  View page source  Edit this page  Create child page  Create documentation issue  Create project issue Quick start Run your first Go gRPC app in minutes!

Basics tutorial Learn about Go gRPC basics.

Learn more ALTS authentication Additional docs Examples FAQ    Reference API Generated code  Other grpc-go repo Performance benchmark Installation       gRPConf 2026 is on Sept 3rd! - Register now ($50 until Jul 24th) or Submit a talk proposal (by Jun 14th) Go Developer stories and talks Stubbing gRPC in Go , by Jean de Klerk , Google. October 8, 2020.

Talking to Go gRPC Services Via HTTP/1  A gRPC Conf 2020 presentation by Malte Isberner, StackRox.

Last modified October 30, 2023: Fix broken link jadekler→jeanbza (#1217) (06a0803)  View page source  Edit this page  Create child page  Create documentation issue  Create project issue Quick start Run your first Go gRPC app in minutes!

Basics tutorial Learn about Go gRPC basics.

Learn more ALTS authentication Additional docs Examples FAQ    Reference API Generated code  Other grpc-go repo Performance benchmark Installation       gRPConf 2026 is on Sept 3rd! - Register now ($50 until Jul 24th) or Submit a talk proposal (by Jun 14th) Quick start This guide gets you started with gRPC in Go with a simple working example.

Prerequisites Go , any one of the two latest major releases of Go .

For installation instructions, see Go’s Getting Started guide.

Protocol buffer compiler, protoc , version 3 .

For installation instructions, see Protocol Buffer Compiler Installation.

Go plugins for the protocol compiler: 1. Install the protocol compiler plugins for Go using the following commands: 2. Update your PATH so that the protoc compiler can find the plugins: Get the example code The example code is part of the grpc-go repo.

1. Download the repo as a zip file and unzip it, or clone the repo: 2. Change to the quick start example directory: Run the example From the examples/helloworld directory: 1. Compile and execute the server code: 2. From a different terminal, compile and execute the client code to see the client output:      $ go install google.golang.org/protobuf/cmd/protoc-gen-go@latest go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest $ export PATH = " $PATH : $(go env GOPATH ) /bin"   $ git clone -b v1.81.1 --depth 1 https://github.com/grpc/grpc-go $ cd grpc-go/examples/helloworld $ go run greeter_server/main.go gRPConf 2026 is on Sept 3rd! - Register now ($50 until Jul 24th) or Submit a talk proposal (by Jun 14th) Congratulations! You’ve just run a client-server application with gRPC.

Update the gRPC service In this section you’ll update the application with an extra server method. The gRPC service is defined using protocol buffers . To learn more about how to define a service in a .proto file see Basics tutorial. For now, all you need to know is that both the server and the client stub have a SayHello() RPC method that takes a HelloRequest parameter from the client and returns a HelloReply from the server, and that the method is defined like this: Open helloworld/helloworld.proto and add a new SayHelloAgain() method, with the same request and response types: Remember to save the file!

Regenerate gRPC code Before you can use the new service method, you need to recompile the updated .proto file.

While still in the examples/helloworld directory, run the following command: $ go run greeter_client/main.go Greeting: Hello world  // The greeting service definition.

service Greeter { // Sends a greeting rpc SayHello (HelloRequest) returns (HelloReply) {} } // The request message containing the user's name.

message HelloRequest { string name = 1; } // The response message containing the greetings message HelloReply { string message = 1; } // The greeting service definition.

service Greeter { // Sends a greeting rpc SayHello (HelloRequest) returns (HelloReply) {} // Sends another greeting rpc SayHelloAgain (HelloRequest) returns (HelloReply) {} } // The request message containing the user's name.

message HelloRequest { string name = 1; } // The response message containing the greetings message HelloReply { string message = 1; } $ protoc --go_out =. --go_opt = paths =source_relative \ --go-grpc_out =. --go-grpc_opt = paths =source_relative \ helloworld/helloworld.proto This will regenerate the helloworld/helloworld.pb.go and helloworld/helloworld_grpc.pb.go files, which contain: Code for populating, serializing, and retrieving HelloRequest and HelloReply message types.

Generated client and server code.

Update and run the application You have regenerated server and client code, but you still need to implement and call the new method in the human-written parts of the example application.

Update the server Open greeter_server/main.go and add the following function to it: Update the client Open greeter_client/main.go to add the following code to the end of the main() function body: Remember to save your changes.

Run the client and server like you did before. Execute the following commands from the examples/helloworld directory: 1. Run the server: 2. From another terminal, run the client. This time, add a name as a command-line argument: You’ll see the following output: What’s next Learn how gRPC works in Introduction to gRPC and Core concepts.

Work through the Basics tutorial.

Explore the API reference .

func (s *server) SayHelloAgain(ctx context.Context, in *pb.HelloRequest) (*pb.HelloReply, er return &pb.HelloReply{Message: "Hello again " + in.GetName()}, nil } r, err = c.SayHelloAgain(ctx, &pb.HelloRequest{Name: *name}) if err != nil { log.Fatalf("could not greet: %v", err) } log.Printf("Greeting: %s", r.GetMessage()) $ go run greeter_server/main.go $ go run greeter_client/main.go --name =Alice $ Greeting: Hello Alice Greeting: Hello again Alice  Last modified May 11, 2026: Replace developers.google.com/protocol-buffers with protobuf.dev (#1502) (2e86d79)  View page source  Edit this page  Create child page  Create documentation issue  Create project issue Basics tutorial A basic tutorial introduction to gRPC in Go.

This tutorial provides a basic Go programmer’s introduction to working with gRPC.

By walking through this example you’ll learn how to: Define a service in a .proto file.

Generate server and client code using the protocol buffer compiler.

Use the Go gRPC API to write a simple client and server for your service.

It assumes that you have read the Introduction to gRPC and are familiar with protocol buffers . Note that the example in this tutorial uses the proto3 version of the protocol buffers language: you can find out more in the proto3 language guide and the Go generated code guide .

Why use gRPC?

Our example is a simple route mapping application that lets clients get information about features on their route, create a summary of their route, and exchange route information such as traffic updates with the server and other clients.

With gRPC we can define our service once in a .proto file and generate clients and servers in any of gRPC’s supported languages, which in turn can be run in environments ranging from servers inside a large data center to your own tablet — all the complexity of communication between different languages and environments is handled for you by gRPC. We also get all the advantages of working with protocol buffers, including efficient serialization, a simple IDL, and easy interface updating.

Setup You should have already installed the tools needed to generate client and server interface code – if you haven’t, see the Prerequisites section of Quick start for setup instructions.

Get the example code The example code is part of the grpc-go repo.

1. Download the repo as a zip file and unzip it, or clone the repo: 2. Change to the example directory: Defining the service Our first step (as you’ll know from the Introduction to gRPC) is to define the gRPC service and the method request and response types using protocol buffers . For the complete .proto file, see routeguide/route_guide.proto .

To define a service, you specify a named service in your .proto file:      $ git clone -b v1.81.1 --depth 1 https://github.com/grpc/grpc-go $ cd grpc-go/examples/route_guide   gRPConf 2026 is on Sept 3rd! - Register now ($50 until Jul 24th) or Submit a talk proposal (by Jun 14th) Then you define rpc methods inside your service definition, specifying their request and response types. gRPC lets you define four kinds of service method, all of which are used in the RouteGuide service: A simple RPC where the client sends a request to the server using the stub and waits for a response to come back, just like a normal function call.

A server-side streaming RPC where the client sends a request to the server and gets a stream to read a sequence of messages back. The client reads from the returned stream until there are no more messages. As you can see in our example, you specify a server-side streaming method by placing the stream keyword before the response type.

A client-side streaming RPC where the client writes a sequence of messages and sends them to the server, again using a provided stream. Once the client has finished writing the messages, it waits for the server to read them all and return its response. You specify a client-side streaming method by placing the stream keyword before the request type.

A bidirectional streaming RPC where both sides send a sequence of messages using a read-write stream.
