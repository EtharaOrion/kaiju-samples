# Implement `uber-go/goleak`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `uber-go/goleak`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://pkg.go.dev/go.uber.org/goleak

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Details Learn more about best practices Repository github.com/uber-go/goleak Links Open Source Insights README ¶ Expand ▾ Documentation Overview Package goleak is a Goroutine leak detector.

Valid go.mod file Redistributable license Tagged version Stable version goleak

CI CI passing passing Coverage Status Goroutine leak detector to help avoid Goroutine leaks.

Installation You can use go get to get the latest version: go get -u go.uber.org/goleak goleak also supports semver releases.

N h l k l h i i f G goleak

CI CI passing passing Coverage Status Goroutine leak detector to help avoid Goroutine leaks.

Installation You can use go get to get the latest version: go get -u go.uber.org/goleak goleak also supports semver releases.

N h l k l h i i f G README Discover Packages > go.uber.org/goleak goleak package module Version: v1.3.0 Latest | Published: Oct 24, 2023 | License: MIT | Imports: 7 | Imported by: 111 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Okay Index func Find(options ...Option) error func VerifyNone(t TestingT, options ...Option) func VerifyTestMain(m TestingM, options ...Option) type Option func Cleanup(cleanupFunc func(exitCode int)) Option func IgnoreAnyFunction(f string) Option func IgnoreCurrent() Option func IgnoreTopFunction(f string) Option type TestingM type TestingT Constants This section is empty.

Variables This section is empty.

func Find func Find(options ...Option) error Find looks for extra goroutines, and returns a descriptive error if any are found.

func VerifyNone func VerifyNone(t TestingT, options ...Option) VerifyNone marks the given TestingT as failed if any extra goroutines are found by Find. This is a helper method to make it easier to integrate in tests by doing: defer VerifyNone(t) VerifyNone is currently incompatible with t.Parallel because it cannot associate specific goroutines with specific tests. Thus, non-leaking goroutines from other tests running in parallel could fail this check. If you need to run tests in parallel, use VerifyTestMain instead, which will verify that no leaking goroutines exist after ALL tests finish.

func VerifyTestMain func VerifyTestMain(m TestingM, options ...Option) go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

VerifyTestMain can be used in a TestMain function for package tests to verify that there were no goroutine leaks. To use it, your TestMain function should look like: func TestMain(m *testing.M) { goleak.VerifyTestMain(m) } See https://golang.org/pkg/testing/#hdr-Main for more details.

This will run all tests as per normal, and if they were successful, look for any goroutine leaks and fail the tests if any leaks were found.

Types type Option type Option interface { // contains filtered or unexported methods } Option lets users specify custom verifications.

func Cleanup added in v1.2.0 func Cleanup(cleanupFunc func(exitCode int)) Option Cleanup sets up a cleanup function that will be executed at the end of the leak check. When passed to VerifyTestMain, the exit code passed to cleanupFunc will be set to the exit code of TestMain.

When passed to VerifyNone, the exit code will be set to 0. This cannot be passed to Find.

func IgnoreAnyFunction added in v1.3.0 func IgnoreAnyFunction(f string) Option IgnoreAnyFunction ignores goroutines where the specified function is present anywhere in the stack.

The function name must be fully qualified, e.g., go.uber.org/goleak.IgnoreAnyFunction For methods, the fully qualified form looks like: go.uber.org/goleak.(*MyType).MyMethod func IgnoreCurrent added in v1.1.0 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

func IgnoreCurrent() Option IgnoreCurrent records all current goroutines when the option is created, and ignores them in any future Find/Verify calls.

func IgnoreTopFunction func IgnoreTopFunction(f string) Option IgnoreTopFunction ignores any goroutines where the specified function is at the top of the stack.

The function name should be fully qualified, e.g., go.uber.org/goleak.IgnoreTopFunction type TestingM type TestingM interface { Run() int } TestingM is the minimal subset of testing.M that we use.

type TestingT type TestingT interface { Error(...interface{}) } TestingT is the minimal subset of testing.TB that we use.

Source Files doc.go leaks.go options.go testmain.go tracestack_new.go Directories Why Go Use Cases Case Studies Get Started Playground Tour Stack Overflow Help Packages Standard Library Sub-repositories About Go Packages pkg.go.dev API About Download Blog Issue Tracker Release Notes Brand Guidelines View all Source files Show internal Expand all go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Code of Conduct Connect Twitter GitHub Slack r/golang Meetup Golang Weekly Copyright Terms of Service Privacy Policy Report an Issue Theme Toggle Shortcuts Modal go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Details Learn more about best practices Repository github.com/uber-go/goleak Links Open Source Insights README ¶ Expand ▾ Documentation Overview Package goleak is a Goroutine leak detector.

Valid go.mod file Redistributable license Tagged version Stable version goleak

CI CI passing passing Coverage Status Goroutine leak detector to help avoid Goroutine leaks.

Installation You can use go get to get the latest version: go get -u go.uber.org/goleak goleak also supports semver releases.

N h l k l h i i f G goleak

CI CI passing passing Coverage Status Goroutine leak detector to help avoid Goroutine leaks.

Installation You can use go get to get the latest version: go get -u go.uber.org/goleak goleak also supports semver releases.

N h l k l h i i f G README Discover Packages > go.uber.org/goleak goleak package module Version: v1.3.0 Latest | Published: Oct 24, 2023 | License: MIT | Imports: 7 | Imported by: 111 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Okay Index func Find(options ...Option) error func VerifyNone(t TestingT, options ...Option) func VerifyTestMain(m TestingM, options ...Option) type Option func Cleanup(cleanupFunc func(exitCode int)) Option func IgnoreAnyFunction(f string) Option func IgnoreCurrent() Option func IgnoreTopFunction(f string) Option type TestingM type TestingT Constants This section is empty.

Variables This section is empty.

func Find func Find(options ...Option) error Find looks for extra goroutines, and returns a descriptive error if any are found.

func VerifyNone func VerifyNone(t TestingT, options ...Option) VerifyNone marks the given TestingT as failed if any extra goroutines are found by Find. This is a helper method to make it easier to integrate in tests by doing: defer VerifyNone(t) VerifyNone is currently incompatible with t.Parallel because it cannot associate specific goroutines with specific tests. Thus, non-leaking goroutines from other tests running in parallel could fail this check. If you need to run tests in parallel, use VerifyTestMain instead, which will verify that no leaking goroutines exist after ALL tests finish.

func VerifyTestMain func VerifyTestMain(m TestingM, options ...Option) go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

VerifyTestMain can be used in a TestMain function for package tests to verify that there were no goroutine leaks. To use it, your TestMain function should look like: func TestMain(m *testing.M) { goleak.VerifyTestMain(m) } See https://golang.org/pkg/testing/#hdr-Main for more details.

This will run all tests as per normal, and if they were successful, look for any goroutine leaks and fail the tests if any leaks were found.

Types type Option type Option interface { // contains filtered or unexported methods } Option lets users specify custom verifications.

func Cleanup added in v1.2.0 func Cleanup(cleanupFunc func(exitCode int)) Option Cleanup sets up a cleanup function that will be executed at the end of the leak check. When passed to VerifyTestMain, the exit code passed to cleanupFunc will be set to the exit code of TestMain.

When passed to VerifyNone, the exit code will be set to 0. This cannot be passed to Find.

func IgnoreAnyFunction added in v1.3.0 func IgnoreAnyFunction(f string) Option IgnoreAnyFunction ignores goroutines where the specified function is present anywhere in the stack.

The function name must be fully qualified, e.g., go.uber.org/goleak.IgnoreAnyFunction For methods, the fully qualified form looks like: go.uber.org/goleak.(*MyType).MyMethod func IgnoreCurrent added in v1.1.0 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

func IgnoreCurrent() Option IgnoreCurrent records all current goroutines when the option is created, and ignores them in any future Find/Verify calls.

func IgnoreTopFunction func IgnoreTopFunction(f string) Option IgnoreTopFunction ignores any goroutines where the specified function is at the top of the stack.

The function name should be fully qualified, e.g., go.uber.org/goleak.IgnoreTopFunction type TestingM type TestingM interface { Run() int } TestingM is the minimal subset of testing.M that we use.

type TestingT type TestingT interface { Error(...interface{}) } TestingT is the minimal subset of testing.TB that we use.

Source Files doc.go leaks.go options.go testmain.go tracestack_new.go Directories Why Go Use Cases Case Studies Get Started Playground Tour Stack Overflow Help Packages Standard Library Sub-repositories About Go Packages pkg.go.
