# TRUTH.md

## Problem

The repository `Zahgon/colly` is a fork of the well-known Go web-scraping
framework **colly** (`github.com/gocolly/colly/v2`). Every non-test source file
of the library — plus all runnable examples under `_examples/` — has been
reduced to a *stub*: function bodies replaced with placeholders such as
`_ = "STUB: not implemented"; return nil`, and explanatory comments removed.

The task is to restore a fully working implementation so that the library
compiles and behaves as a correct colly release. Success is measured by a large
suite of unit/integration tests in the root package (`colly`) and in the
`queue` subpackage flipping from failing to passing.

The bulk of the meaningful work lives in the core library files
(`colly.go`, `request.go`, `response.go`, `http_backend.go`, `http_trace.go`,
`context.go`, `htmlelement.go`, `xmlelement.go`, `unmarshal.go`,
`queue/queue.go`, `storage/storage.go`, `proxy/proxy.go`, `debug/*`,
`extensions/*`). The `_examples/*` files are `package main` programs that only
need to be restored to compilable form (they are not exercised by the flipping
tests but must still build as part of the module).

## Behavioral contract

The observable contract is defined by the public colly API and the listed
tests. Below are the guarantees each area must satisfy.

### Collector construction and options
- `NewCollector(options ...CollectorFunc) *Collector` returns a collector with
  sane defaults, then applies each functional option. After construction, an
  `Init`-style step must populate internal maps/stores so callbacks can be
  registered immediately (`TestNewCollector` inspects default field values:
  a non-nil user agent, `MaxBodySize` default, initialized backend, store,
  context, ID counters, etc.).
- Functional options must exist and take effect for at least: `AllowedDomains`,
  `DisallowedDomains`, `DisallowedURLFilters`, `URLFilters`, `MaxDepth`,
  `UserAgent`, `Headers`, `Async`, `AllowURLRevisit`, `IgnoreRobotsTxt`,
  `CacheDir`, `CacheExpiration`, `MaxBodySize`, `ID`, `Debugger`,
  `CheckHead`, `DetectCharset`, `ParseHTTPErrorResponse`, `TraceHTTP`.
- Environment-variable configuration must be honored (`TestEnvSettings`):
  options like `COLLY_USER_AGENT`, `COLLY_MAX_DEPTH`, `COLLY_ALLOWED_DOMAINS`,
  `COLLY_DISALLOWED_DOMAINS`, `COLLY_MAX_BODY_SIZE`, `COLLY_IGNORE_ROBOTSTXT`,
  `COLLY_FOLLOW_REDIRECTS`, `COLLY_CACHE_DIR`, `COLLY_DETECT_CHARSET`,
  `COLLY_PARSE_HTTP_ERROR_RESPONSE`, `COLLY_DEBUG` map to the corresponding
  fields when set.

### Callback registration & dispatch
- `OnRequest`, `OnResponse`, `OnResponseHeaders`, `OnError`, `OnScraped`,
  `OnHTML`, `OnXML` register callbacks. Callbacks fire in the correct lifecycle
  order: request → (optional HEAD pre-check) → response headers → response body
  → HTML/XML selectors → scraped.
- `OnHTMLDetach` / `OnXMLDetach` remove a previously registered selector
  callback by selector string (`TestCallbackDetachment`).
- `OnHTML` callbacks are invoked once per matching element in document order.
  `OnXML` supports both XPath expressions against HTML documents and against XML
  documents (`TestCollectorOnXMLWithHtml`, `...WithXML`,
  `...WithXMLCompressed`).

### Requesting & responses
- `Visit(url)` performs a GET, subject to filtering (allowed/disallowed
  domains, URL filters, robots.txt, max depth, revisit rules). `Post`,
  `PostRaw`, `PostMultipart`, and `Request` provide other methods/bodies.
- Duplicate-request suppression: by default a URL (with method + body hash) is
  visited only once; `AllowURLRevisit()` disables this. GET dedup is keyed on
  URL; POST dedup incorporates the request body
  (`TestCollectorURLRevisit`, `TestCollectorPostRevisit`,
  `TestCollectorPostRawRevisit`, `...RevisitCheck`, `...PostURLRevisitCheck`).
- Filtering returns well-defined errors (e.g. already-visited, forbidden
  domain, missing URL, robots-disallowed, max-depth) surfaced through `OnError`
  and returned by `Visit`.
- `Response` exposes `StatusCode`, `Body`, `Headers`, `Request`, `Ctx`,
  `Save`, and `FileName`. Character-set detection / decompression is applied so
  `Response.Body` is decoded text when appropriate
  (`TestCollectorContentSniffing`, gzip handling).
- HTTP error statuses do not produce a parsed body unless
  `ParseHTTPErrorResponse` is enabled (`TestParseHTTPErrorResponse`).
- Requests without an `Accept` header default to a sensible accept value, but a
  caller-supplied/empty override is respected (`TestNoAcceptHeader`,
  `TestHeaders`, `TestUserAgent`).

### Redirects, cookies, robots
- Redirect handling honors `AllowedDomains`/disallowed URL filters and can be
  turned off; cookies set during redirects are carried forward
  (`TestRedirect`, `TestRedirectWithDisallowedURLs`, `TestSetCookieRedirect`,
  `TestSetCookieComplexRedirectCycle`, `TestIssue594`).
- Cookie jar management: `SetCookies`/`Cookies` operate on the underlying jar
  (`TestCollectorCookies`).
- robots.txt is fetched and cached; disallowed paths (including ones with query
  parameters) are blocked unless `IgnoreRobotsTxt` is set; a robots.txt
  connection error propagates as an error
  (`TestRobotsWhenAllowed`, `...Disallowed`,
  `...DisallowedWithQueryParameter`, `TestIgnoreRobotsWhenDisallowed`,
  `TestConnectionErrorOnRobotsTxtResultsInError`).

### Retries and HEAD checks
- Requests can be retried (`Request.Retry`) preserving method/body; retrying a
  non-seekable body must behave correctly (`TestCollectorPostRetry`,
  `TestCollectorGetRetry`, `TestCollectorPostRetryUnseekable`,
  `TestRedirectErrorRetry`).
- `CheckHead` issues a HEAD before the GET (`TestCollectorVisitWithCheckHead`).
- A request-header hook allows inspecting/modifying outgoing headers
  (`TestCheckRequestHeadersFunc`).
- 404 responses served with gzip content are handled gracefully
  (`TestIssue745GzipURLWith404Response`).

### Context
- `context.go` provides a concurrency-safe key/value store attached to each
  request/response: `Put`, `Get`, `GetAny`, `ForEach`, `MarshalBinary`,
  `UnmarshalBinary`. `ForEach` iterates all entries; the context is clonable
  across cloned collectors (`TestContextIteration`, `TestContextClone`,
  `TestCollectorContext`, `TestRequestContext`).

### Request marshalling
- `Request.Marshal` / the collector's `UnmarshalRequest` round-trip a request
  (URL including host, method, body, depth, ID, collector ID, context) so a
  serialized request reconstructs equivalently (`TestRequestMarshalRoundtripHost`).

### HTML/XML element helpers
- `HTMLElement` provides `Attr`, `Text`, `ChildText`, `ChildTexts`,
  `ChildAttr`, `ChildAttrs`, `ForEach`, `ForEachWithBreak`, and access to
  `DOM`, `Request`, `Response`, `Name`. These return values consistent with the
  underlying goquery selection (`TestHTMLElement`, `TestAttr`, `TestChildText`,
  `TestChildTexts`, `TestChildAttr`, `TestChildAttrs`, `TestCollectorOnHTML`).
- Base-tag and relative-URL resolution: `AbsoluteURL` resolves against the page
  URL, respecting a `<base href>` if present, and tolerates whitespace/tabs and
  malformed percent-encoding (`TestBaseTag`, `TestBaseTagRelative`,
  `TestTabsAndNewlines`, `TestLonePercent`).
- `XMLElement` provides analogous helpers for XML/HTML XPath navigation.

### Unmarshalling into structs
- `HTMLElement.Unmarshal(v)` populates a struct using `selector` struct tags,
  supporting nested structs, maps, slices of values, and slices of pointers
  (`TestBasicUnmarshal`, `TestNestedUnmarshal`, `TestNestedUnmarshalMap`,
  `TestPointerSliceUnmarshall`, `TestStructSliceUnmarshall`).

### Rate limiting
- `LimitRule`/`Limit`/`Limits` support per-domain delay, random delay, and
  parallelism; rules are compiled (regex) and can be shared across collectors
  without deadlocks or data races, and are clonable
  (`TestSharedLimitRule_AInitThenBInit_ANotStuck`, `TestSharedLimitRuleRace`,
  `TestLimitRuleClone`).

### HTTP tracing
- When `TraceHTTP` is enabled, a `HTTPTrace` records connect/first-byte timing
  and is attached to the response; it functions with and without artificial
  delay (`TestTraceWithNoDelay`, `TestTraceWithDelay`,
  `TestCollectorVisitWithTrace`).

### Queue subpackage
- `queue.New(threads, storage)` builds a request queue with a storage backend
  (default in-memory). `AddURL`/`AddRequest` enqueue; `Run(collector)` consumes
  requests, honoring thread count and draining until empty; `Size`, `IsEmpty`
  behave accordingly (`queue.TestQueue`).

### Depth & request counting
- `MaxDepth` limits recursion depth; each followed link increments depth.
  `Collector` tracks request count (`TestCollectorDepth`,
  `TestCollectorRequests`).

## Solution decomposition

A correct solution can be built roughly in this order; each sub-goal has a clear
done-signal.

1. **Core types & backend (`colly.go`, `http_backend.go`)** — Define
   `Collector`, `CollectorFunc` options, request lifecycle, filtering, the
   HTTP backend with client, cookie jar, caching, limit rules, and dedup set.
   Done when construction, GET/POST visits, callbacks, and dedup work.

2. **Request/Response (`request.go`, `response.go`)** — Request struct with
   `Visit/Post/PostRaw/PostMultipart/Retry/AbsoluteURL/Marshal`, response body
   decoding/charset/decompression, `Save`. Done when visit tests and marshalling
   round-trip pass.

3. **Context (`context.go`)** — thread-safe map with iteration and binary
   marshalling. Done: context tests pass.

4. **DOM helpers (`htmlelement.go`, `xmlelement.go`)** — goquery/xpath wrappers.
   Done: element/attr/child tests pass.

5. **Unmarshal (`unmarshal.go`)** — reflection-based struct population from
   `selector` tags. Done: unmarshal tests pass.

6. **Tracing (`http_trace.go`)** — `httptrace.ClientTrace` wiring. Done: trace
   tests pass.

7. **Storage & Queue (`storage/storage.go`, `queue/queue.go`)** — in-memory
   storage interface + queue consumer. Done: `queue.TestQueue` passes.

8. **Ancillary packages (`proxy/proxy.go`, `debug/*`, `extensions/*`,
   `cmd/colly/colly.go`)** — proxy round-robin switcher, debuggers
   (log/web/no-op), extension middlewares (random UA, referer,
   url-length-filter). Needed for module compilation.

9. **Examples (`_examples/**`)** — restore each `package main` to a compiling,
   logically complete program (recreate `generateFormData`, `setupServer`,
   scraping callbacks, etc.).

## Solution space

- **DOM engine**: The canonical implementation uses `goquery` for HTML and
  `htmlquery`/`xmlquery` for XPath. Any equivalent that produces the same
  attr/text/child results and XPath semantics is acceptable; you need not match
  internal field names.
- **Dedup keying**: hashing the URL (and body for POST) via any stable hash
  (FNV, etc.) is fine as long as revisit semantics match.
- **Robots handling**: using `temoto/robotstxt` or an equivalent parser is
  acceptable; only the allow/deny outcomes are contractually observed.
- **Caching**: the on-disk cache format is unspecified by the tests; any scheme
  that respects `CacheDir`/`CacheExpiration` is valid.
- **Queue storage**: default in-memory storage may be a slice or linked
  structure; only `Add/Get/Size/Init` behavior is observed.
- **Option style**: options may be implemented as closures over the collector or
  as a typed function set — either is fine provided env-var and functional
  configuration take effect.
- **Examples**: exact comments/log messages are irrelevant; only that they
  compile and use the public API sensibly. Multiple valid phrasings exist.
- **Concurrency primitives**: limit rules may use mutexes/channels/waitgroups in
  various combinations, provided shared-rule race and no-deadlock guarantees
  hold.

## Known pitfalls

- **Init/default population**: forgetting to initialize maps, the store, the
  backend, cookie jar, or the visited-set causes nil-map panics or every test
  failing at construction. `NewCollector` must leave the collector fully usable.
- **Revisit key correctness**: keying POST dedup on URL only (ignoring body)
  breaks `TestCollectorPostRevisit`; conversely hashing GET with body breaks GET
  dedup. Respect `AllowURLRevisit`.
- **Accept header**: hard-coding an `Accept` value overwriting user-supplied
  empty header fails `TestNoAcceptHeader`; only default when unset.
- **Charset/compression order**: decode content-encoding (gzip/deflate) before
  charset detection, and cap by `MaxBodySize`. Mishandling breaks content
  sniffing and gzip-404 tests.
- **Redirect cookie propagation**: cookies set on intermediate redirect
  responses must be stored in the jar and re-sent; complex redirect cycles must
  not lose or duplicate cookies.
- **Robots query parameters**: robots matching must consider the query string,
  not just the path.
- **Retry with unseekable body**: retrying must not attempt to re-read a
  consumed, non-seekable reader; buffer the body or fail gracefully as the test
  expects.
- **AbsoluteURL edge cases**: must trim tabs/newlines inside href values,
  tolerate a lone `%` (invalid percent-encoding) without erroring, and honor a
  `<base>` tag (including relative base).
- **Shared limit-rule deadlock**: initializing/locking a shared rule from two
  collectors must not stall the first (`ANotStuck`); guard against re-init and
  races.
- **Context binary round-trip**: `MarshalBinary`/`UnmarshalBinary` must preserve
  all entries for request marshalling round-trips.
- **XPath vs CSS**: `OnXML` uses XPath expressions, `OnHTML` uses CSS selectors;
  swapping engines breaks the XML tests.
- **Depth accounting**: increment depth on link-follow and enforce `MaxDepth`
  before enqueueing, else depth tests over/under-count.
- **Module must build fully**: leaving any stub (including in `_examples`,
  `extensions`, `debug`, `proxy`, `cmd`) with `STUB` placeholders or missing
  functions will fail `go build ./...` / `go vet`, preventing the test binary
  from compiling.

## Cheat surface

Reject solutions that do any of the following instead of implementing behavior:

- **Hard-coding test expectations**: detecting specific test URLs, ports, or
  response strings and returning canned values rather than performing real HTTP,
  parsing, or filtering.
- **Special-casing by input**: e.g., branching on the exact selector strings,
  struct types, or byte contents used in the tests to shortcut real DOM
  traversal / reflection.
- **Stubbing away network/goquery**: returning fixed HTML/DOM results without
  actually fetching or parsing the served content.
- **Disabling checks to force green**: making `Visit` always succeed by skipping
  robots/domain/depth/revisit logic, or making dedup a no-op just so counts
  line up for a particular test.
- **Faking the queue/limit concurrency**: serializing everything or sleeping to
  paper over race/deadlock tests instead of correct synchronization.
- **Leaving placeholders**: any residual `"STUB: not implemented"` string,
  `panic("TODO")`, or empty body that happens to satisfy a test by returning
  zero values.
- **Modifying or deleting test files** or the fail_to_pass assertions.

Legitimate solutions perform genuine HTTP requests, real HTML/XML parsing,
reflection-based unmarshalling, and correct concurrency — independent of which
specific inputs the tests use.

## Success criteria

- The entire module compiles: `go build ./...` and the test binaries for the
  root package and `queue` package build without errors (all stubs, including
  examples and ancillary packages, replaced with working code).
- All listed `fail_to_pass` tests pass, covering: collector construction &
  options, env settings, visit/post/multipart, revisit semantics, headers/UA,
  redirects & cookies, robots.txt, retries & HEAD checks, content sniffing/gzip,
  HTML/XML callbacks and element helpers, absolute-URL/base-tag edge cases,
  unmarshalling, context iteration/clone/round-trip, request marshalling,
  limit-rule sharing/cloning/races, HTTP tracing, depth/request counting, and
  `queue.TestQueue`.
- No previously passing behavior regresses; the race detector (used by the
  shared-limit-rule race test) reports no data races.
- Behavior is achieved through general implementation of the colly API, not
  input-specific shortcuts.