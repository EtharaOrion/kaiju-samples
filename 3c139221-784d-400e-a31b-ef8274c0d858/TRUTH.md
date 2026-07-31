# TRUTH.md

## Problem

`async-h1` is an asynchronous HTTP/1.1 implementation (client + server) built on `http-types` and `futures-lite`. A number of core modules have been reduced to stubs that `panic!("STUB: not implemented")`. The task is to implement these modules so that the crate correctly:

- Encodes and decodes HTTP/1.1 requests and responses over an async byte stream.
- Handles both fixed-length (`Content-Length`) and chunked (`Transfer-Encoding: chunked`) bodies.
- Formats and parses HTTP dates.
- Drives the full server accept-loop (with connection keep-alive and close semantics) and the client connect/encode/decode flow.

The stubbed files span body encoding, chunked codec, client encode/decode/connect, server encode/decode/accept, HTTP date handling, a read-notification wrapper, and shared constants in `lib.rs`.

The definition of "correct" is: the listed `fail_to_pass` tests pass, no previously-passing behavior regresses, and observed wire output/semantics match HTTP/1.1 (RFC 7230) and the crate's existing test expectations.

## Behavioral contract

Externally observable behavior that a correct solution must exhibit:

1. **Body encoder selection.** When encoding a body, if the body advertises a known length it is streamed as-is (fixed-length); if the length is unknown, it is wrapped in chunked framing. `poll_read` must delegate to the chosen inner encoder.

2. **Chunked decoding (RFC 7230 §4.1).** Given a chunked stream, the decoder must:
   - Parse hexadecimal chunk sizes (accepting `0-9`, `a-f`, `A-F`), terminated by CRLF.
   - Read exactly `chunk_size` body bytes per chunk, then consume the trailing CRLF.
   - Treat a zero-size chunk as the end-of-body marker and transition into trailer parsing.
   - Parse trailer headers after the last chunk, deliver them via the trailer channel, then report EOF (`Ok(0)`).
   - Surface an "unexpected byte" error (`InvalidData`) when a byte does not match the grammar (e.g., a non-hex, non-CR byte where a size digit or CR is expected; a missing CR/LF; malformed trailers).
   - Surface an "unexpected EOF" error (`UnexpectedEof`) when the stream ends mid-frame.
   - Detect chunk-size arithmetic overflow beyond 64 bits and report `InvalidData`.

3. **Chunked encoding.** Each read produces a chunk prefixed by its hex length and CRLF and suffixed by CRLF: `{hex-len}\r\n{data}\r\n`. A final zero-length chunk (`0\r\n\r\n`) is emitted once the source is exhausted, after which reads return `Ok(0)`. The framing computation must never overflow the caller's buffer.

4. **`max_bytes_to_read` framing budget.** Given a caller buffer length, the encoder must reserve room for the hex length prefix plus the two CRLFs, and choose the largest content read size that still fits after framing. It must produce exactly the values asserted in the encoder test table (e.g., 6→1, 7→2, 20→15, 21→15, 22→16, 260→254, 261→254, 262→255, 263→256, 4100→4093 … 4104→4096). Buffers smaller than 6 bytes are unsupported.

5. **HTTP date formatting.** The date type formats to the RFC 1123 / IMF-fixdate form (`Wdy, DD Mon YYYY HH:MM:SS GMT`), round-trips through parsing, and satisfies the module's size and known-example tests.

6. **Server request decode.** Parse the request line and headers, construct the target `Url` correctly for the full range of request-target forms (origin-form paths, absolute-form, authority-form CONNECT, host header combination, queries, fragments/anchors, double/triple slash, and malformed paths — rejecting the malformed case). Select the correct body reader based on framing headers, and honor `Expect: 100-continue`.

7. **Server response encode.** Emit a correct status line, headers (including a `Date` header and correct body framing header — either `Content-Length` or `Transfer-Encoding: chunked`), and the body. HEAD requests must emit headers but no body bytes. Chunked responses must use chunked framing.

8. **Server accept loop.** Continuously read requests and write responses on one connection, supporting keep-alive across multiple requests (including draining unread request bodies of both fixed and chunked forms) and closing the connection when `Connection: close` is present on either side or otherwise indicated.

9. **Client encode/decode.** Encode a request (request line, headers, added `Date`, correct body framing including CONNECT and fragment handling, chunked bodies) and decode a response (status line, headers, multiple values for the same header name, differing newline conventions, missing `Date`, and connection-closure signaling end-of-body).

10. **Read notifier.** Wrapping a reader must transparently forward reads while notifying (via a channel/signal) when the underlying body has been read, enabling the accept loop to know when a body is fully consumed.

## Solution decomposition

Sub-goals, roughly in dependency order:

1. **Shared helpers (`lib.rs`).** Provide the header/head-length constants (`MAX_HEADERS`, `MAX_HEAD_LENGTH`) and any shared utility functions the codecs depend on.

2. **Date (`date.rs`).** Implement construction from a timestamp, formatting to IMF-fixdate, and parsing. Must satisfy the size-of, format, and RFC-example tests.

3. **Chunked encoder (`chunked/encoder.rs`).** Implement `new`, the `max_bytes_to_read` budget function, and `poll_read` that frames each read and emits the terminating zero chunk exactly once.

4. **Chunked decoder (`chunked/decoder.rs`).** Implement the `State` enum `Debug`, `new`, byte-reading helpers (`poll_read_byte`, `expect_byte`), the error constructors (`eof`, `unexpected`, `overflow`), trailer sending, and the `poll_read` state machine.

5. **Body encoder (`body_encoder.rs`).** Implement `new` (fixed vs chunked selection) and `poll_read` delegation via the projection.

6. **Read notifier (`read_notifier.rs`).** Implement the wrapping reader that forwards reads and signals completion.

7. **Server body reader (`server/body_reader.rs`).** Implement the reader variants (chunked, fixed-length, and no/empty body) used to expose the request body.

8. **Server decode (`server/decode.rs`).** Parse the head, build the `Url` for all target forms, select the body reader, and implement `Expect` handling.

9. **Server encode (`server/encode.rs`).** Serialize status line + headers (date, framing) + body, honoring HEAD.

10. **Server accept (`server/mod.rs`).** The connection loop with keep-alive/close and body-draining.

11. **Client encode/decode/connect (`client/*.rs`).** Mirror the server encode/decode for the client side, plus the connect entry point.

## Solution space

Valid variations that should NOT be penalized:

- **Chunked decoder structure.** The state machine may use a different set/naming of states or a nested/loop-based dispatch, as long as it correctly parses sizes, bodies, CRLFs, and trailers and produces the same error kinds at the same points. Reading body bytes directly into the caller buffer vs. an internal buffer is an implementation choice, provided framing bytes are not leaked to the caller.

- **`max_bytes_to_read` computation.** The reference derives the hex-framing width via `log2/4`; an equivalent integer approach (counting hex digits of the candidate content length and iterating/decrementing until it fits) is equally valid as long as it produces the exact test-table values and never overflows the buffer.

- **Error messages.** Exact error text is not contractual; only the `io::ErrorKind` (`UnexpectedEof` vs `InvalidData`) and the fact that an error is produced at the right condition matter. Tests generally assert on kind/behavior, not string contents — but note trailer tests may check that an invalid trailer is rejected.

- **Date implementation.** May be hand-rolled or delegate to a formatting routine, as long as output is the canonical IMF-fixdate and parsing round-trips. Storage as seconds-since-epoch vs. broken-down fields is free.

- **URL construction (`server/decode`).** Different sequencing of "is this absolute / authority / origin form?" checks is fine, provided every enumerated test case (anchor, connect, conflicting-connect, double/triple slash, host+absolute, host+path, malformed, query) yields the expected `Url` (or rejection for malformed).

- **Buffered reading.** Using `BufReader` vs. manual buffering for head parsing is an implementation choice.

- **Body-encoder selection.** Any equivalent check of "known length vs. unknown length" (e.g., matching an `Option<usize>` length) is acceptable.

## Known pitfalls

- **Off-by-one in chunk framing.** The framing budget must account for the fact that increasing the content read size can push the hex length across an order-of-magnitude boundary (F→10, FF→100, …), adding a framing byte. Failing to reserve for this overflows the buffer; the test table specifically pins the boundary rows (21, 261, 262, 4101, 4102, 4103).

- **Emitting the terminating zero chunk exactly once.** After the source returns 0, mark done and still frame that read as `0\r\n\r\n`; subsequent reads must return `Ok(0)`, not another zero chunk.

- **Chunk size arithmetic.** Multiply-by-16-then-add per hex digit must use checked arithmetic and report overflow rather than wrap.

- **CRLF discipline.** Every chunk body must be followed by CR then LF; the chunk size line ends with CRLF. Missing either should raise `InvalidData` (unexpected byte), not be silently skipped.

- **Zero-length chunk vs. body byte.** On the size line, a size of 0 transitions to trailer parsing — do not attempt to read a body.

- **Trailers.** A bare CRLF (empty trailer section) must still deliver empty trailers and finish. Partial trailer parses need to either wait (Pending) or error on buffer exhaustion; a trailing offset mismatch is an error.

- **EOF vs. graceful end.** Reaching stream end mid-frame is an error (`UnexpectedEof`); reaching the `Done` state returns `Ok(0)`. For client response decode with connection-closure framing, EOF legitimately terminates the body.

- **HEAD responses.** Must send framing headers but zero body bytes; a naive encoder that writes the body will fail the head-request tests.

- **Body draining for keep-alive.** Unread request bodies (fixed and chunked, short and long) must be consumed before the next request is read, or the connection desynchronizes. The read-notifier mechanism supports detecting completion.

- **Date header presence.** Both client request encode and server response encode add a `Date` header when appropriate; tests check its addition.

- **Multiple header values.** Response decoding must preserve multiple values under the same header name rather than overwriting.

- **Pin/projection correctness.** `poll_read` implementations on pinned self must project fields correctly and re-poll inner readers through `Pin::new`.

## Cheat surface

Ways a solution could appear to pass without genuinely solving the task — these should be rejected:

- Hard-coding the `max_bytes_to_read` test table (or the specific date example strings) rather than computing them, so any untested input breaks.
- Special-casing exact byte sequences from the chunked/decode tests instead of implementing the general state machine.
- Returning canned `Response`/`Request`/`Url` values keyed off recognizable test inputs rather than genuinely parsing.
- Suppressing errors (returning `Ok(0)` or empty) where the contract requires `UnexpectedEof`/`InvalidData`, just to avoid failing an assertion.
- Making tests pass by weakening or deleting the assertions, the test bodies, or the `fail_to_pass` tests themselves.
- Implementing only the branches exercised by the current tests while leaving `panic!`/`todo!` in sibling branches that the contract requires.
- Faking chunked framing by echoing input unchanged for inputs that "happen" to already be framed.

## Success criteria

A correct solution satisfies all of the following:

- All listed `fail_to_pass` tests pass, specifically:
  - `chunked::decoder::tests::{test_chunked_big,test_chunked_mdn,test_chunked_wiki,test_ff7}`
  - `chunked::encoder::test_bytes_to_read::simple_check_of_known_values`
  - `date::tests::{size_of,test2,test3,test_fmt,test_rfc_example}`
  - `server::decode::tests::url_for_*` (anchor, conflicting_connect, connect, double_slash_path, host_plus_absolute_url, host_plus_path, malformed_resource_path, query, triple_slash_path)
  - `accept::*` (basic, request_close, response_close, and the four keep-alive long/short × chunked/fixed unread-body cases)
  - `client_decode::*` (connection_closure, multiple_header_values_for_same_header_name, response_newlines, response_no_date)
  - `client_encode::*` (chunked_body, request_add_date, request_with_connect, request_with_fragment)
  - `test_with_expect_when_reading_body`, `test_without_expect_when_not_reading_body`
  - `server_chunked_large`
  - `server_decode::{chunked,invalid_trailer,post_with_body,unexpected_eof}`
  - `server_encode::{basic,basic_404,chunked,head_request_chunked_body,head_request_fixed_body}`
- No stubbed `panic!`/`todo!` paths remain reachable in normal operation.
- No previously-passing tests regress.
- The crate builds cleanly (no unresolved `panic!("STUB")` placeholders, no type/borrow errors), and behavior conforms to HTTP/1.1 framing as described in the Behavioral contract.