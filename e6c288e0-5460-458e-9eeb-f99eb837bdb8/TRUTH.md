# TRUTH.md

## Problem

The `kui` package (an ASGI/WSGI web framework in the style of Starlette/Index.py) has had a large number of its modules gutted: the bodies of many functions and methods were replaced with `pass` (or files left empty). The public API surface — routing, request/response handling, background tasks, lifespan management, exception handling, parameter injection, OpenAPI generation, and a handful of utilities — must be restored so the package imports cleanly and behaves per its documented contracts.

The task is to (re)implement the stubbed functions/methods so that the enumerated `fail_to_pass` tests pass. The tests exercise focused, self-contained behaviors: background task queues, lifespan startup/shutdown protocol, exception-handler lookup, response converters, radix-tree route matching, `Routes` composition operators, contextvar-bound state, dynamic imports, and OpenAPI doc merging — for both the `asgi` and `wsgi` variants where applicable.

A working solution restores each behavior without changing existing test expectations, and keeps the two parallel implementations (`kui/asgi/*` and `kui/wsgi/*`) consistent with each other apart from the sync/async distinction.

## Behavioral contract

Restore the following observable behaviors. Each bullet is independently testable.

### Utilities

- **Singleton metaclass / helper** (`utils`): constructing the same singleton type repeatedly returns the identical object instance.
- **State container** (`utils/state.py`): a mapping-and-attribute hybrid. Attribute assignment/read/delete mirror item assignment/read/delete over the same backing store; missing keys raise `AttributeError` (attribute access) / `KeyError` (item access); it can be initialized from a dict/kwargs and supports containment and iteration.
- **Contextvar-bound proxy** (`utils` bind): a proxy bound to a `ContextVar` forwards attribute set (`setattr`), attribute delete (`delattr`), item get (`getitem`), item set (`setitem`), and item delete (`delitem`) to the object currently stored in the contextvar. Mutations are visible on the underlying object.
- **Importer** (`utils` import helpers): `import_module`-style helper imports and returns a module by dotted path; `import_from_string`-style helper accepts `"pkg.module:attr"` form, imports the module and returns the named attribute. Invalid strings/targets raise a clear error.
- **Inspect helpers** (`utils/inspect.py`):
  - "get raw handler" unwraps `functools.wraps`-wrapped callables down to the original function; a non-wrapped function is returned unchanged.
  - "get object filepath" returns the absolute filesystem path of the file defining an object, correct even when the object lives outside the current working directory.

### Responses (`kui/responses.py`, `kui/asgi/responses.py`, `kui/wsgi/responses.py`)

- Response classes construct correctly and expose the expected `status_code`, `media_type`/`Content-Type`, `body`/content, and headers: HTML, plain-text, JSON, redirect (Location header + 3xx status), file (streams a file, sets content-type/attachment), server-sent-event stream, and generic streaming responses.
- The "docs" helpers/annotations for `FileResponse`, `SendEventResponse`, and `StreamResponse` produce OpenAPI-style descriptors that honor a supplied `content_type`, `status`, and `headers`.

### Background tasks (`kui/asgi/background.py`, `kui/wsgi/background.py`)

- A background task wraps a callable plus positional and keyword args; invoking the task runs the callable with those args/kwargs.
- The ASGI variant supports both sync and async callables (awaiting coroutine functions, calling sync functions directly).
- A background-tasks collection executes appended tasks in append order; an empty collection runs without error.

### Lifespan (`kui/asgi/lifespan.py`, application wiring)

- The primary API is an **async-generator lifespan function**: code before the single `yield` runs on startup, code after runs on shutdown.
- An `asynccontextmanager`-style lifespan is supported: entering the context on startup, exiting on shutdown (a startup helper enters the manager; a shutdown helper exits it).
- Legacy `on_startup`/`on_shutdown` registration still works but emits a `DeprecationWarning`.
- Mixing a `lifespan=` async generator with legacy `on_startup`/`on_shutdown` callbacks raises an error.
- During the ASGI `lifespan` protocol: on a startup exception, a `lifespan.startup.failed` message is sent (with the error text); on a shutdown exception, a `lifespan.shutdown.failed` message is sent. Successful phases send the corresponding `complete` messages.

### Exceptions (`kui/exceptions.py`, `kui/asgi/exceptions.py`, `kui/wsgi/exceptions.py`)

- The exception middleware keeps a registry keyed by both integer status codes and exception classes.
- `lookup_handler` walks the exception's MRO to find the most specific registered handler; returns `None` when nothing matches.
- For an `HTTPException`, a handler registered for its specific **status code** takes precedence over a handler registered for the exception **type**; when no status-code handler exists it falls back to the type handler.
- `RequestValidationError` exposes the failing location via an `in_` field; both its JSON serialization and its `errors()` include that `in_`/location information.
- The middleware installs internal default handlers for `HTTPException` and `RequestValidationError`.

### Routing

- **Routes** (`kui/routing/routes.py`):
  - Decorator form registers a handler at a path (and can require specific HTTP methods).
  - Left-shift / operator composition (`<<`, `+`, `|`, prefixing, radd) builds and merges route collections while **preserving order**.
  - `url_for(name, ...)` reverses a named route to a path; an unknown name raises a "no route found" error.
  - Slicing/iteration over a `Routes` collection works.
  - Middleware attached to routes wraps handlers (wrapper identity/`functools.wraps` preserved as asserted).
  - Empty path and empty file-route collections are handled without error.
- **Router** (`kui/routing/routers.py`):
  - Duplicate route **name** registration raises.
  - Searching with an invalid protocol (not `"http"`/`"websocket"`) raises.
  - HTTP/socket **middleware added after routes** raises; middleware added **before** routes is accepted.
  - Appending an object of an invalid route type raises.
- **Radix tree** (`kui/routing/tree.py`):
  - Adds paths with typed converters (`{name:int}`, `{name:decimal}`, `{name:uuid}`, `{name:any}`, plain `{name}`, static suffixes like `avatar.png`) and matches concrete paths, populating captured params with correctly converted types.
  - Rejects malformed additions: duplicate/conflicting converter on the same node, illegal converter combinations (e.g. `:any` not last, a `{filename}.py` static-suffix conflict, unknown converter, path not starting with `/`, etc.).
  - Failed searches (trailing slash mismatch, missing segment, wrong static suffix, empty path) return "no match".
  - **Static segments are preferred over dynamic siblings** regardless of insertion order (static-first or dynamic-first), while dynamic segments still match other values; preference holds on sibling branches. The tree is iterable over its registered routes.
- **Multimethod extension** (`kui/routing/extensions/multimethod.py`): rejects a class-based view target; permits a socket (websocket) route.
- **Commands** (`kui/routing/commands.py`): a "display urls" command lists registered routes/URLs.

### OpenAPI (`kui/openapi/*`, `kui/parameters/docs.py`)

- Merging OpenAPI info dicts (first/second → result) deep-merges as the parametrized cases expect.
- `describe_extra_docs` attaches extra OpenAPI documentation to a function or a class-view handler; applying it repeatedly **merges** rather than overwrites.

### Export surface (`test_export_all`)

- The package's `__all__` / re-exports resolve: every name the top-level (and sub-)packages advertise is importable and defined. No stub leaves a dangling/undefined public name.

## Solution decomposition

Independent sub-goals (roughly the order that unblocks the most tests):

1. **Make the package import.** Fill every empty/`pass` module enough that `import kui`, `import kui.asgi`, `import kui.wsgi` succeed and all `__all__` names resolve (unblocks `test_export_all` and everything else).
2. **Utilities** (`utils/state.py`, `utils/inspect.py`, importer, singleton, contextvar bind) — pure, dependency-free; implement first.
3. **Responses** — construct baize-style response objects and the doc-descriptor helpers.
4. **Background tasks** — thin wrapper storing `func, *args, **kwargs`; sync vs async dispatch; ordered queue runner.
5. **Exceptions** — registry with dual keys, MRO-walking `lookup_handler`, precedence rules, default internal handlers, `RequestValidationError.in_`.
6. **Routing tree** — radix insertion/search with converters and static-over-dynamic preference; the trickiest algorithmic piece.
7. **Routes & Router** — collection operators, ordering, `url_for`, name-uniqueness, middleware-ordering guards, protocol validation.
8. **Lifespan** — async-generator/asynccontextmanager adapters, deprecation warnings, mixing guard, ASGI protocol failure events.
9. **Parameter injection & OpenAPI** — dependency resolution, response conversion registration, `describe_extra_docs`, info merging.
10. **Multimethod & commands** — view-type checks and the URL-listing command.
11. **CI workflow** — a `.github/workflows/ci.yml` exists (not test-verified; presence only).

The `asgi` and `wsgi` variants share structure; implement one, then mirror it with the sync/async difference (await vs direct call, async generators vs generators, `AsyncExitStack` vs `ExitStack`).

## Solution space

- **Response conversion registration** is naturally a `functools.singledispatch` dispatching on the return value's type (None→error, `HttpResponse`→identity, `dict`/`list`/`tuple`/`BaseModel`→JSON, `str`/`bytes`→plain text, `PurePath`→file, `URL`→redirect, async generator→SSE, plus route-container passthroughs). An explicit `if/elif` type ladder or a dict-of-type→converter is equally valid, provided subclass dispatch and the None-error case behave identically.
- **MRO-walking handler lookup** may iterate `type(exc).__mro__` and stop at the first registered class, or use Python's own MRO via `singledispatch`-like resolution — either is fine as long as status-code handlers take precedence over type handlers for `HTTPException`.
- **State/bind proxies** can be implemented via `__getattr__`/`__setattr__`/`__delattr__` and `__getitem__`/`__setitem__`/`__delitem__` on a wrapper, or via a mapping subclass; only the observable forwarding matters.
- **Radix tree** can be a node tree with separate static-children map and an ordered list of dynamic children, or any structure that guarantees static-before-dynamic matching. Converters can be a registry of `{name: (regex, python_type)}`. Storing convert functions vs regex+cast is a free choice.
- **Lifespan adapter**: the async-generator form can be normalized into startup/shutdown callbacks by wrapping in `asynccontextmanager`, or handled directly by stepping the generator; both are valid. The mixing guard can raise at construction time or at first use.
- **Deprecation warnings**: `warnings.warn(..., DeprecationWarning, stacklevel=...)` — the exact message text is not asserted beyond category; tests check the warning category is emitted.
- **`url_for` reverse**: build from stored path templates; error type must be the framework's "no route found" exception (whatever the tests import), not a bare `KeyError`.
- **Importer**: `importlib.import_module` for modules; split on `:` for the attribute form. Accept either raising `ImportError`/`ValueError` on malformed input.
- **CI file** contents are not verified by tests; any reasonable workflow (or minimal file) satisfies "present."

## Known pitfalls

- **Static-vs-dynamic ordering must be insertion-order-independent.** Adding a dynamic segment first then a static sibling (or vice-versa) must still prefer the static match. This is the subtlest requirement and is directly tested from both directions and on sibling branches.
- **Trailing-slash and exact-suffix strictness.** `/hello/` must NOT match a route registered as `/hello`; `avatar.png` static suffix must not match `avatar`. Empty path is a failed search, not a root match.
- **Converter type coercion.** Matched params must be converted to the declared Python types (`int`, `Decimal`, `uuid.UUID`, `str`), not left as raw strings.
- **Malformed-add rejection.** `:any` must be terminal; unknown converters, conflicting converters on one node, non-leading-slash paths, and static-suffix-on-typed conflicts must raise on add, not silently succeed.
- **HTTPException handler precedence.** Registering both a status-code handler and a type handler and picking the wrong one is the classic bug — status code wins; absence falls back to type.
- **`lookup_handler` must return `None` (not raise) when unregistered.**
- **RequestValidationError `in_`.** Both `.json()` output and `.errors()` entries must carry the location; forgetting to thread `in_` through the model breaks two tests.
- **Ordering in Routes operators.** `+`, `<<`, radd, prefixing, and slicing must preserve declaration order; a set/dict-based merge that reorders will fail.
- **Duplicate-name detection** must trigger when a name repeats, and **middleware-after-routes** must raise while middleware-before-routes is allowed — the guards are stateful and order-sensitive.
- **Middleware wrapping identity.** The test checks `functools.wraps`-style preservation; wrap handlers with `@functools.wraps` (or equivalent) so introspection/unwrapping works.
- **Lifespan failure events.** On startup/shutdown exceptions the ASGI app must *send* the `*.failed` message (with the message text) rather than propagate/crash silently; success paths send `*.complete`.
- **Mixing lifespan + legacy callbacks must raise**, and legacy callbacks must still emit `DeprecationWarning`.
- **Background sync vs async.** The ASGI runner must await coroutine functions but call plain functions directly; passing through `*args, **kwargs` intact is asserted.
- **Response converter for `None`** must raise a helpful error (a returned `None` is a programming mistake), not produce an empty 200.
- **`describe_extra_docs` must merge** across multiple applications and work on both function and class-view targets — a plain overwrite fails the merge test.
- **Do not break `__all__`.** Every advertised export must exist; a lingering `pass` that removes a symbol fails `test_export_all`.

## Cheat surface

- **Do not special-case the literal test inputs.** The tree tests use fixed sample paths (`/hello`, `/sayhi/aber/avatar.png`, a specific UUID, `1.111`, etc.) — matching them by hardcoded string comparison instead of implementing general radix matching + converters is a cheat. The static-over-dynamic tests deliberately probe generality from multiple insertion orders.
- **Do not hardcode expected merged dicts** for the OpenAPI `test_merge_openapi_info[f0..f2]` cases; implement a real deep-merge.
- **Do not stub `lookup_handler` to return a fixed handler**; it must genuinely walk the MRO and respect status-vs-type precedence, verified across several handler-registration combinations.
- **Do not fake `url_for`** by returning the input; it must reverse registered named routes and raise for unknown names.
- **No test-detection / environment sniffing** (e.g. branching on test names, `PYTEST_CURRENT_TEST`, or file paths) to shortcut behavior.
- **Do not weaken assertions** by editing tests, conftest, or fixtures; the tests are the fixed oracle.
- **`asgi` and `wsgi` variants must both be genuinely implemented** — the wsgi background tests exist precisely to prevent implementing only the async side.
- Presence of a plausible response object is not enough — status codes, media types, and headers are individually asserted; returning a generic 200 for everything is a cheat.

## Success criteria

- All listed `fail_to_pass` tests pass: background (asgi + wsgi), lifespan (+edge), OpenAPI extra-docs (+edge), routing (fileroutes, commands, multimethod edge, router edge, routes + edge, tree), exceptions edge, `test_export_all`, responses (+edge), utils (contextvars edge, importer, inspect edge, objects singleton, state).
- `import kui`, `import kui.asgi`, `import kui.wsgi` succeed and every public/`__all__` name resolves.
- No previously passing behavior regresses; existing tests continue to pass.
- The `asgi` and `wsgi` implementations remain structurally parallel, differing only where sync/async semantics require.
- No test files, fixtures, or configuration were modified to force passage; behavior is general, not input-specific.