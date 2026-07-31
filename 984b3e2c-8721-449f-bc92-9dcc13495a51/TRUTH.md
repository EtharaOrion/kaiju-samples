# TRUTH.md

## Problem

The `oauthlib` library has had a large fraction of its implementation gutted: dozens of modules across the OAuth 1.0 (RFC 5849), OAuth 2.0 (RFC 6749), device flow (RFC 8628), and OpenID Connect Core packages have had their function/method bodies replaced with `pass` (or otherwise stubbed out), and several GitHub Actions workflow files removed. A correct solution restores full, spec-conformant behavior so that the enumerated `fail_to_pass` test suites — spanning OAuth1 endpoints/client/signatures/parameters/utils/validator, OAuth2 clients/endpoints/grant types, and shared `common.py` helpers — all pass.

This is a *restoration* task: the destination is the well-known public behavior of the real `oauthlib` package at the version the repository targets. Each stubbed callable must be reimplemented to satisfy its docstring/API contract and the tests that exercise it.

## Behavioral contract

The observable contracts, grouped by area. Every item below is exercised (directly or transitively) by the listed tests.

### Shared (`oauthlib/common.py`, `signals.py`, `uri_validate.py`)
- `quote`/`unquote` percent-encode/decode returning `str` (unicode), accepting both `str` and `bytes` input.
- `urldecode(query)` rejects non-url-encoded input and malformed hex escapes with `ValueError`, otherwise returns a list of decoded `(key, value)` 2-tuples (blank values preserved), UTF-8 decoded.
- `generate_signed_token(private_pem, request)` produces a JWT (RS256) whose claims include `scope`, an `exp` derived from `request.expires_in`, merged with `request.claims`; returns a unicode string.
- `verify_signed_token(public_pem, token)` decodes/verifies an RS256 JWT and returns the claims dict.
- `Request` object: `uri_query` returns the query portion of the URI; `uri_query_params` returns parsed 2-tuples (empty list when no query, strict parsing); `duplicate_params` returns keys appearing more than once across decoded body + query params. `CaseInsensitiveDict` behaves case-insensitively for string keys.
- `to_unicode` recursively unicode-izes strings, lists, and dict-like structures.

### OAuth 1 (`oauth1/rfc5849/...`)
- `utils`: `escape`/`unescape` implement RFC 3986 percent-encoding (only unreserved chars unescaped); `filter_params` decorator and `filter_oauth_params` (keep only `oauth_`-prefixed params); `parse_authorization_header` parses an `OAuth ...` header into a list of 2-tuples.
- `signature`: base-string URI normalization (lowercase scheme/host, default-port removal, path preservation), parameter collection & normalization (exclude `oauth_signature`, sort, encode), signature base string construction, and HMAC-SHA1/256/512, RSA-SHA1/256/512, and PLAINTEXT signing plus verification. Verify functions must be robust against malformed input (return `False`, never raise) — the "false positives" tests assert this.
- `parameters`: `prepare_headers` (build `Authorization: OAuth ...`, leave non-oauth data untouched), `prepare_form_encoded_body`, `prepare_request_uri_query`, and `_append_params`.
- `Client` (test_client): constructor normalizes/decodes credentials to unicode, supports explicit `nonce`/`timestamp`, signature-method registration and dispatch (HMAC-SHA1/256, RSA, PLAINTEXT), rejects unknown methods, requires an RSA key for RSA, and signs in header/body/query per `signature_type`. Missing realm handling.
- `request_validator.RequestValidator`: `check_*` length/realm helpers, and abstract methods raising `NotImplementedError`.
- Endpoints (`base`, `access_token`, `authorization`, `request_token`, `resource`, `signature_only`): request construction and enforcement of SSL, mandated params, timestamp/nonce, version, duplicate params, signature-method whitelist; per-endpoint validation flows (validate client key, token, verifier, realms, redirect_uri, signature, access token) returning `(valid, request)` tuples; and response builders returning `(headers, body, status)` with correct status codes (200 success, 400 OAuth1Error, 401 unauthorized) and urlencoded bodies.

### OAuth 2 (`oauth2/rfc6749/...`) and RFC 8628 / OpenID
- `utils`: scope list/string conversion, param helpers, `is_secure_transport`.
- `parameters`: prepare authorization/token/grant requests and parse authorization/token responses (including `expires_in`/`expires_at` handling and scope-change warnings/errors).
- `tokens`: bearer & MAC token preparation/validation, PKCE code-verifier/code-challenge (plain & S256) generation with length constraints.
- Clients (`base` + backend/legacy/mobile/service/web/device): `prepare_authorization_request`, `prepare_token_request`, `prepare_refresh_token_request`, `prepare_request_body`, token/grant response parsing populating attributes, revocation request preparation, and per-grant request-body construction.
- Grant types (authorization_code, implicit, client_credentials, resource_owner_password, refresh_token, device_code, and OIDC variants/dispatchers) and endpoints (authorization, token, introspect, metadata, revocation, resource, pre_configured, userinfo): request validation, error responses, and correctly formed success responses. `errors`/`exceptions` classes carry proper `error`, `status_code`, `description`, and urlencoded/JSON serialization.

### CI workflow files
- The three `.github/workflows/*.yml` files must exist and be valid YAML defining the lint/build/dependency-review jobs. These are not covered by pytest; their exact contents are not asserted by the test suite.

## Solution decomposition

1. **Restore shared primitives first** (`common.py`, `utils` modules). Everything else depends on `quote`/`unquote`/`urldecode`/`Request`/`to_unicode` and the OAuth1/2 `utils`.
2. **OAuth1 signing core** (`signature.py`, `parameters.py`, `utils.py`) — needed by both `Client` and all endpoints.
3. **OAuth1 client & request validator** — `Client` composes signing; `RequestValidator` defines the abstract surface endpoints rely on.
4. **OAuth1 endpoints** — `base.py` provides shared validation; the four concrete endpoints layer their specific checks and response construction on top.
5. **OAuth2 primitives** (`utils`, `parameters`, `tokens`, `errors`) then **clients**, then **grant_types**, then **endpoints** and **pre_configured** wiring.
6. **RFC 8628 and OpenID Connect** layers reuse OAuth2 base classes; implement their grant types, dispatchers, endpoints, validators, tokens, and exceptions.
7. **Add the CI workflow YAML files** (behaviorally inert for tests but part of the change set).

Recommended ordering follows the dependency graph (shared → oauth1 signing → oauth1 endpoints → oauth2 → rfc8628/openid) so intermediate test runs are meaningful.

## Solution space

- **Any implementation that reproduces the documented public API semantics is acceptable.** Because this restores a well-known library, the reference matches upstream `oauthlib`, but a valid solution need not be byte-identical — helper decomposition, private helper names, and internal ordering may differ as long as observable behavior matches the tests.
- **JWT dependency**: `generate_signed_token`/`verify_signed_token` may import `jwt` at module or function scope; either is fine. Algorithm must be RS256 and claims must include `scope` and `exp`.
- **Signature verification robustness** can be achieved via broad try/except returning `False`, or via targeted validation — tests only require malformed inputs never raise and never yield a false accept.
- **Timestamp source** for `exp` / nonce generation may use `datetime.utcnow()` or equivalent; only the relative/expiry semantics matter.
- **Workflow YAML contents are essentially free-form** — any valid workflows (or minimal placeholders) satisfy the repo since no test inspects them. They exist mainly to complete the diff.
- Data structures for parameter lists may be built via comprehensions, loops, or helper utilities interchangeably.

## Known pitfalls

- **Return-type discipline**: many functions must return `str` (unicode), not `bytes`; endpoints must return the `(headers, body, status)` (OAuth1) or the analogous tuples/response objects (OAuth2) in the exact positional order tests unpack.
- **Status codes**: OAuth1 access/request-token responses must return 200 on success, 401 on unauthorized (empty body), and the error's `status_code` (typically 400) with an urlencoded error body on `OAuth1Error`.
- **`uri_query_params` empty case**: must short-circuit to `[]` when there is no query; strict parsing otherwise (feeding empty string to `parse_qsl(strict_parsing=True)` raises).
- **`duplicate_params`**: count across *both* decoded body and query params; guard against `None` body.
- **Signature base string / normalization**: correct percent-encoding (RFC 3986 unreserved set), exclusion of `oauth_signature`, default-port stripping, and lowercase scheme/host are subtle and directly tested.
- **`filter_oauth_params` / `parse_authorization_header`**: must keep only `oauth_`-prefixed keys and correctly strip the `OAuth` scheme and quotes.
- **PKCE code verifier/challenge**: length bounds (43–128) and S256 base64url (no padding) encoding must be exact.
- **Token response parsing**: `expires_in` may arrive as a string and must be coerced; `expires_at` should be an int; scope changes must emit the documented warning/attribute.
- **Not-implemented surface**: abstract validator methods must raise `NotImplementedError` (tests assert this), while concrete `check_*` helpers must return booleans.
- **Case-insensitive headers**: header handling in both `common.CaseInsensitiveDict` and endpoint request construction must be case-insensitive.

## Cheat surface

- **Do not** make tests pass by weakening/short-circuiting validation (e.g. always returning `(True, request)` from validators, or always returning status 200). Tests explicitly assert failure paths (invalid client key, expired timestamp, bad signature, unsupported grant type, etc.).
- **Do not** hardcode expected token strings, signatures, or response bodies to match specific test fixtures; signatures and tokens must be genuinely computed from inputs.
- **Do not** stub `verify_*` signature functions to unconditionally return `True` — the false-positive tests require rejecting tampered inputs.
- **Do not** catch-and-swallow exceptions solely to bypass assertions about raised errors (`NotImplementedError`, `OAuth1Error`, OAuth2 error classes).
- Do not import from or reconstruct the reference diff verbatim as a marker of correctness — correctness is defined by behavior, not by matching upstream source line-for-line.
- The workflow YAML files are the only "free" deliverables; nothing else may be left as a no-op.

## Success criteria

- All listed `fail_to_pass` tests pass: OAuth1 endpoints (`test_access_token`, `test_authorization`, `test_base`, `test_request_token`, `test_resource`, `test_signature_only`), `test_client`, `test_parameters`, `test_request_validator`, `test_signatures`, `test_utils`; and OAuth2 client tests (backend/base/legacy/mobile/service/web) plus endpoint tests (base, client_authentication, credentials_preservation, error_responses, extra_credentials, introspect, metadata, resource_owner_association, revocation).
- No previously passing test regresses (import-time integrity across the whole package is required, since these modules import each other transitively — a broken stub anywhere can fail collection).
- All stubbed modules are fully implemented (no residual `pass`-only bodies that a test would reach), and the three CI workflow files are present as valid YAML.
- Signature/token computations are correct and reversible (sign/verify round-trips, PKCE challenge matches verifier), and error/validation paths produce the correct error identifiers, status codes, and serialized bodies.