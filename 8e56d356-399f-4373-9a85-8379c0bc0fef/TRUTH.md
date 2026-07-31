# TRUTH.md

## Problem

The repository `Zahgon/etl-parser` is a Python library for parsing Windows ETL (Event Trace Log) files, ETW (Event Tracing for Windows) provider events, kernel MOF events, and TraceLogging events. A large number of source files have been reduced to *stubs*: core utility/infrastructure modules have their function bodies replaced by `pass`, and several hundred auto‑generated ETW provider modules have had their module docstrings / provider‑identifying headers removed.

The task is to restore correct behavior so that the parsing pipeline works end‑to‑end for the exercised code paths. The overwhelming majority of the stubbed files (the `etl/parsers/etw/Microsoft_*`, `Intel_*`, provider modules, etc.) are boilerplate: they only need their provider identity metadata (name + GUID) present and their construct-based event structures/registrations intact. The *substantive* logic lives in a small set of infrastructure modules that the tests actually exercise:

- `etl/utils.py` — primitive parsers/helpers (`Guid`, `WString`, `CString`, `SystemTime`, and a `check_enum` helper).
- `etl/tracelogging.py` — TraceLogging event decoding.
- `etl/parsers/kernel/{core,header,image,process,thread,io,file}.py` — kernel MOF event parsing/dispatch.
- `etl/parsers/etw/core.py` — ETW provider dispatch (`build_etw` and the registration mechanism).
- `etl/event.py`, `etl/etl.py`, `etl/system.py`, `etl/error.py`, `etl/dtyp.py`, `etl/wmi.py`, and related glue.

The `fail_to_pass` tests target GUID parsing, the `check_enum` helper, kernel MOF header/image/process/thread parsing, and TraceLogging parsing.

## Behavioral contract

The solution must satisfy the following observable behaviors (as exercised by the named tests):

1. **GUID parsing (`etl/utils.py`)**
   - A `Guid` parser reads a Windows GUID from its binary on-disk layout: a little-endian 32-bit `Data1`, two little-endian 16-bit fields `Data2`/`Data3`, and 8 raw bytes `Data4`.
   - Its string representation is the canonical hyphenated form `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (lowercase hex), where the first three groups use the integer fields and the last two groups come from the 8 `Data4` bytes (first 2 bytes, then remaining 6 bytes), each rendered big-endian as hex.
   - Round-tripping a known byte sequence through the parser must yield exactly the expected canonical GUID string.

2. **`check_enum` helper (`etl/utils.py`)**
   - Given a raw integer value and a construct `Enum` definition (mapping of names↔values), `check_enum` returns/accepts the value when it corresponds to a defined enum member (`test_check_enum_ok`).
   - When the value is not a valid member of the enum, it must raise the library's dedicated exception for invalid enum/type values (`test_check_enum_ko`) rather than silently returning or raising a generic error.

3. **Kernel MOF parsing (`etl/parsers/kernel/*` + `etl/wmi.py` + dispatch)**
   - Kernel events are dispatched by `(group, version, event_type)`. Each concrete parser class registers itself so that a lookup by that triple resolves to the correct construct structure.
   - Header events (e.g. the `EventTrace` extension / typegroup, version 2, type 32) parse into the expected fields.
   - Image-load events across their supported versions (type 2, 3, 4) parse into the expected fields (base address, image size, process id, file name, etc.).
   - Process events (image load, process terminate/end, and version‑4 group‑1 type‑1/type‑2 create events) parse into expected fields.
   - Thread events (version‑3 group‑1 types 1–4) parse into expected fields.
   - Looking up an unknown group/version/event-type raises the corresponding "not found" exceptions (`GroupNotFound`, `VersionNotFound`, `EventTypeNotFound`).

4. **TraceLogging parsing (`etl/tracelogging.py`)**
   - `build_tracelogging(source)` (invoked from `Event.parse_tracelogging`) extracts the TraceLogging metadata from the event's extended data / user data, then decodes each declared field according to its TraceLogging type.
   - Supported field decodings tested include: scalar/array of `uint8`, array of `uint16`, wide strings (`wstring`), and `guid`; plus an "extended flag" metadata form.
   - When required metadata is absent, it raises `TlMetaDataNotFound` (`test_miss_meta`).
   - When metadata is malformed/unrecognized, or an unsupported field tag/type is encountered, it raises the appropriate TraceLogging error (`TlUnhandledTag` / metadata error) — covering `test_invalid_tag` and `test_wrong_meta`.

5. **Exceptions (`etl/error.py`)** — the exception hierarchy (base `EtlException` plus the specialized subclasses referenced above) exists with the correct constructor signatures and messages so that the dispatch layers can raise them. Restoring docstrings alone is *not* the deliverable; the constructors must remain functional.

6. **Event / ETL glue (`etl/event.py`, `etl/etl.py`, `etl/system.py`)**
   - `Event` exposes accessors: process id, thread id, an ISO‑formatted timestamp computed from boot time plus the event's 100‑ns interval offset (epoch = 1601‑01‑01 UTC), `parse_etw()`, and `parse_tracelogging()`.
   - `EtlFile.get_header()` returns the stored header; `build_from_stream(bytes)` parses the chunk stream, validates that the first chunk is a valid WMI/system trace header, and raises `InvalidEtlFileHeader` otherwise.

## Solution decomposition

Sub-goals a correct solution accomplishes:

1. **Restore primitive parsers in `etl/utils.py`.** Implement the `Guid` construct and its canonical string rendering; implement `WString`/`CString`/`SystemTime` as null-terminated / structured parsers; implement `check_enum` to validate an integer against a construct enum and raise `InvalidType` on failure.

2. **Restore the ETW dispatch core (`etl/parsers/etw/core.py`).** Provide the `Etw` base class + registration decorator (keyed by GUID / event id / version) and `build_etw(guid, event_id, version, user_data)` that resolves and parses, raising `GuidNotFound` / `EventIdNotFound` / `EtwVersionNotFound` when unresolved.

3. **Restore provider metadata for the hundreds of ETW modules.** Each provider module must carry its provider name and GUID (used for registration/lookup) and keep its construct event structures + registrations intact. These are mechanical/boilerplate.

4. **Restore kernel MOF parsing and dispatch (`etl/parsers/kernel/*`, `etl/wmi.py`).** Provide the `Mof` base + registration keyed by `(group, version, event_type)` and a `build_mof`-style resolver raising `GroupNotFound` / `VersionNotFound` / `EventTypeNotFound`. Restore the concrete header/image/process/thread/io/file structures for the tested versions/types.

5. **Restore TraceLogging decoding (`etl/tracelogging.py`).** Locate metadata, iterate declared fields, map each TraceLogging type to a decoder (including arrays and wstring/guid), and raise `TlMetaDataNotFound` / `TlUnhandledTag` appropriately.

6. **Restore event/etl/system glue** as described in the behavioral contract.

7. **Restore the exception hierarchy** with functional constructors.

## Solution space

- **GUID string formatting** may be implemented via manual hex formatting of the fields, via Python's `uuid` module fed the correctly ordered bytes, or via construct adapters — any approach that yields the exact canonical lowercase hyphenated string is acceptable.
- **`check_enum`** may be implemented by testing membership against the enum's declared values, by attempting a construct build/parse and catching failure, or by a direct dict lookup — as long as valid values pass and invalid ones raise the library's invalid-type exception.
- **Registration/dispatch** for ETW and kernel parsers can use a decorator populating a module-level registry, a metaclass, or an explicit mapping. The only contract is that the correct triple/tuple resolves to the correct structure and unknown keys raise the specific exceptions.
- **TraceLogging type dispatch** can be a mapping from type code to construct parser, an if/elif chain, or table-driven — any structure that decodes the tested types and raises on unsupported tags/metadata is valid.
- **Timestamp computation** can build a `datetime` from the 1601 epoch plus a `timedelta`, or compute via arithmetic then format; either is fine provided the ISO output (microsecond precision) matches.
- The provider-module restoration is inherently uniform; regenerating headers programmatically or restoring them by hand are equally valid so long as name+GUID metadata and the construct structures are present.

## Known pitfalls

- **GUID byte/endianness ordering.** `Data1`/`Data2`/`Data3` are little-endian integers, but the last 8 bytes (`Data4`) are rendered big-endian (byte order preserved) in the canonical string. Mixing these up produces a wrong GUID string and fails `test_guid_parser`. The output must be lowercase.
- **`check_enum` must raise the specific exception**, not a generic `KeyError`/`ValueError`; `test_check_enum_ko` expects the library's invalid-type/enum exception.
- **Kernel dispatch key granularity.** The lookup must key on all of group, version, and event type; collapsing versions/types will make some image/process/thread variants resolve to the wrong structure. Distinct versions (image type 2/3/4; process v4; thread v3) have different field layouts.
- **TraceLogging metadata location.** Metadata is carried in the event's extended-data/section, not the raw user payload; failing to detect its absence must yield `TlMetaDataNotFound` (not a crash) for `test_miss_meta`, and malformed metadata must yield the correct error for `test_wrong_meta`/`test_invalid_tag`.
- **Array vs scalar decoding.** `uint8`/`uint16` arrays require reading a count/length and iterating; treating them as scalars breaks `test_array_uint8`/`test_array_uint16`.
- **Timestamp epoch.** Windows FILETIME epoch is 1601-01-01 UTC and units are 100-ns intervals; using the Unix epoch or wrong scaling yields wrong timestamps.
- **Do not "solve" by only adding docstrings.** Restoring the removed docstrings/comment headers without restoring the actual function bodies and structures leaves the stubs (`pass`) non-functional and fails every test.
- **Provider registration completeness.** Missing GUID metadata in provider modules can break import-time registration or GUID lookups elsewhere; keep those modules importable and self-registering.

## Cheat surface

- The reference diff is a private authoring aid; a correct solution must be derivable from the specification and tests, not from copying diff lines. Do not reproduce provider-file contents verbatim as the "answer."
- Hard-coding the exact expected outputs of the named tests (e.g. returning the literal expected GUID string, the literal expected parsed dict, or short-circuiting `build_tracelogging` to return fixture values) is a cheat: it does not implement general parsing and would not generalize to other inputs.
- Special-casing the specific byte fixtures used in tests instead of implementing the real construct-based parsers is disallowed.
- Making tests pass by weakening/removing assertions, editing the test files, or stubbing exceptions to never raise is out of bounds.
- Catching all exceptions broadly to force the "raise" tests to pass with the wrong exception type is not acceptable — the *specific* exception classes are part of the contract.

## Success criteria

- All listed `fail_to_pass` tests pass:
  - `tests/test_guid_parser.py::GuidParser::test_guid_parser`
  - `tests/test_utils.py::TestUtilsModule::test_check_enum_ok` and `::test_check_enum_ko`
  - `tests/test_mof_header_parser.py::TestMofHeaderParser::test_header_extension_typegroup_type32`
  - `tests/test_mof_image_parser.py::TestMofImageParser::test_image_load_type2/3/4`
  - `tests/test_mof_process_parser.py::TestMofProcessParser::{test_image_load, test_process_terminate, test_process_v4_type_group1_type1, test_process_v4_type_group1_type2}`
  - `tests/test_mof_thread_parser.py::TestMofThreadParser::test_thread_v3_type_group_1_type1..4`
  - `tests/test_tracelogging_parser.py::TraceloggingParser::{test_array_uint16, test_array_uint8, test_extended_flag, test_invalid_tag, test_miss_meta, test_tracelogging_guid, test_tracelogging_wstring, test_wrong_meta}`
- No previously passing behavior regresses; all modules remain importable (the many provider modules must import cleanly so registration succeeds).
- The implemented parsers are general (driven by the construct definitions and dispatch tables), not tailored to individual test fixtures.
- The specific exception types (`InvalidType`, `TlMetaDataNotFound`, `TlUnhandledTag`, `GroupNotFound`, `VersionNotFound`, `EventTypeNotFound`, `GuidNotFound`, `EventIdNotFound`, `EtwVersionNotFound`, `InvalidEtlFileHeader`) are raised in their respective error conditions.