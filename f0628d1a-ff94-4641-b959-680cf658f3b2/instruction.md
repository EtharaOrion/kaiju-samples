# Implement `google/uuid`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `google/uuid`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://pkg.go.dev/github.com/google/uuid

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Details Learn more about best practices Repository github.com/google/uuid Links Open Source Insights Code Wiki README ¶ Expand ▾ Documentation Overview Package uuid generates and inspects UUIDs.

Valid go.mod file Redistributable license Tagged version Stable version uuid The uuid package generates and inspects UUIDs based on RFC 4122 and DCE 1.1: Authentication and Security Services.

This package is based on the github.com/pborman/uuid package (previously named code.google.com/p/go-uuid). It differs from these earlier packages in that a UUID is a 16 byte array rather than a byte slice. One loss due to this change is the ability to represent an invalid UUID (vs a NIL UUID).

Install go get github.com/google/uuid uuid The uuid package generates and inspects UUIDs based on RFC 4122 and DCE 1.1: Authentication and Security Services.

This package is based on the github.com/pborman/uuid package (previously named code.google.com/p/go-uuid). It differs from these earlier packages in that a UUID is a 16 byte array rather than a byte slice. One loss due to this change is the ability to represent an invalid UUID (vs a NIL UUID).

Install go get github.com/google/uuid linux/amd64 README Discover Packages > github.com/google/uuid uuid package module Version: v1.6.0 Latest | Published: Jan 23, 2024 | License: BSD-3-Clause | Imports: 17 | Imported by: 113,457 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Okay UUIDs are based on RFC 4122 and DCE 1.1: Authentication and Security Services.

A UUID is a 16 byte (128 bit) array. UUIDs may be used as keys to maps or compared directly.

Index Constants Variables func ClockSequence() int func DisableRandPool() func EnableRandPool() func IsInvalidLengthError(err error) bool func NewString() string func NodeID() []byte func NodeInterface() string func SetClockSequence(seq int) func SetNodeID(id []byte) bool func SetNodeInterface(name string) bool func SetRand(r io.Reader) func Validate(s string) error type Domain func (d Domain) String() string type NullUUID func (nu NullUUID) MarshalBinary() ([]byte, error) func (nu NullUUID) MarshalJSON() ([]byte, error) func (nu NullUUID) MarshalText() ([]byte, error) func (nu *NullUUID) Scan(value interface{}) error func (nu *NullUUID) UnmarshalBinary(data []byte) error func (nu *NullUUID) UnmarshalJSON(data []byte) error func (nu *NullUUID) UnmarshalText(data []byte) error func (nu NullUUID) Value() (driver.Value, error) type Time func GetTime() (Time, uint16, error) func (t Time) UnixTime() (sec, nsec int64) type UUID func FromBytes(b []byte) (uuid UUID, err error) func Must(uuid UUID, err error) UUID func MustParse(s string) UUID func New() UUID func NewDCEGroup() (UUID, error) func NewDCEPerson() (UUID, error) func NewDCESecurity(domain Domain, id uint32) (UUID, error) func NewHash(h hash.Hash, space UUID, data []byte, version int) UUID func NewMD5(space UUID, data []byte) UUID func NewRandom() (UUID, error) func NewRandomFromReader(r io.Reader) (UUID, error) func NewSHA1(space UUID, data []byte) UUID go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

func NewUUID() (UUID, error) func NewV6() (UUID, error) func NewV7() (UUID, error) func NewV7FromReader(r io.Reader) (UUID, error) func Parse(s string) (UUID, error) func ParseBytes(b []byte) (UUID, error) func (uuid UUID) ClockSequence() int func (uuid UUID) Domain() Domain func (uuid UUID) ID() uint32 func (uuid UUID) MarshalBinary() ([]byte, error) func (uuid UUID) MarshalText() ([]byte, error) func (uuid UUID) NodeID() []byte func (uuid *UUID) Scan(src interface{}) error func (uuid UUID) String() string func (uuid UUID) Time() Time func (uuid UUID) URN() string func (uuid *UUID) UnmarshalBinary(data []byte) error func (uuid *UUID) UnmarshalText(data []byte) error func (uuid UUID) Value() (driver.Value, error) func (uuid UUID) Variant() Variant func (uuid UUID) Version() Version type UUIDs func (uuids UUIDs) Strings() []string type Variant func (v Variant) String() string type Version func (v Version) String() string Constants View Source const ( Person = Domain(0) Group = Domain(1) Org = Domain(2) ) Domain constants for DCE Security (Version 2) UUIDs.

View Source const ( Invalid = Variant(iota) // Invalid UUID RFC4122 // The variant specified in RFC4122 Reserved // Reserved, NCS backward compatibility.

Microsoft // Reserved, Microsoft Corporation backward compatibility.

Future // Reserved for future definition.

) go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Constants returned by Variant.

Variables View Source var ( NameSpaceDNS = Must(Parse("6ba7b810-9dad-11d1-80b4-00c04fd430c8")) NameSpaceURL = Must(Parse("6ba7b811-9dad-11d1-80b4-00c04fd430c8")) NameSpaceOID = Must(Parse("6ba7b812-9dad-11d1-80b4-00c04fd430c8")) NameSpaceX500 = Must(Parse("6ba7b814-9dad-11d1-80b4-00c04fd430c8")) Nil UUID // empty UUID, all zeros // The Max UUID is special form of UUID that is specified to have all 128 bits set t Max = UUID{ 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, } ) Well known namespace IDs and UUIDs func ClockSequence func ClockSequence() int ClockSequence returns the current clock sequence, generating one if not already set. The clock sequence is only used for Version 1 UUIDs.

The uuid package does not use global static storage for the clock sequence or the last time a UUID was generated. Unless SetClockSequence is used, a new random clock sequence is generated the first time a clock sequence is requested by ClockSequence, GetTime, or NewUUID. (section 4.2.1.1) func DisableRandPool added in v1.3.0 func DisableRandPool() DisableRandPool disables the randomness pool if it was previously enabled with EnableRandPool.

Both EnableRandPool and DisableRandPool are not thread-safe and should only be called when there is no possibility that New or any other UUID Version 4 generation function will be called concurrently.

func EnableRandPool added in v1.3.0 func EnableRandPool() go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

EnableRandPool enables internal randomness pool used for Random (Version 4) UUID generation.

The pool contains random bytes read from the random number generator on demand in batches.

Enabling the pool may improve the UUID generation throughput significantly.

Since the pool is stored on the Go heap, this feature may be a bad fit for security sensitive applications.

Both EnableRandPool and DisableRandPool are not thread-safe and should only be called when there is no possibility that New or any other UUID Version 4 generation function will be called concurrently.

func IsInvalidLengthError added in v1.3.0 func IsInvalidLengthError(err error) bool IsInvalidLengthError is matcher function for custom error invalidLengthError func NewString added in v1.2.0 func NewString() string NewString creates a new random UUID and returns it as a string or panics. NewString is equivalent to the expression uuid.New().String() func NodeID func NodeID() []byte NodeID returns a slice of a copy of the current Node ID, setting the Node ID if not already set.

func NodeInterface func NodeInterface() string NodeInterface returns the name of the interface from which the NodeID was derived. The interface "user" is returned if the NodeID was set by SetNodeID.

func SetClockSequence func SetClockSequence(seq int) SetClockSequence sets the clock sequence to the lower 14 bits of seq. Setting to -1 causes a new sequence to be generated.

func SetNodeID go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

func SetNodeID(id []byte) bool SetNodeID sets the Node ID to be used for Version 1 UUIDs. The first 6 bytes of id are used. If id is less than 6 bytes then false is returned and the Node ID is not set.

func SetNodeInterface func SetNodeInterface(name string) bool SetNodeInterface selects the hardware address to be used for Version 1 UUIDs. If name is "" then the first usable interface found will be used or a random Node ID will be generated. If a named interface cannot be found then false is returned.

SetNodeInterface never fails when name is "".

func SetRand func SetRand(r io.Reader) SetRand sets the random number generator to r, which implements io.Reader. If r.Read returns an error when the package requests random data then a panic will be issued.

Calling SetRand with nil sets the random number generator to the default generator.

func Validate added in v1.5.0 func Validate(s string) error Validate returns an error if s is not a properly formatted UUID in one of the following formats: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx urn:uuid:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx {xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx} It returns an error if the format is invalid, otherwise nil.

Types type Domain type Domain byte A Domain represents a Version 2 domain func (Domain) String func (d Domain) String() string go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

type NullUUID added in v1.3.0 type NullUUID struct { UUID UUID Valid bool // Valid is true if UUID is not NULL } NullUUID represents a UUID that may be null. NullUUID implements the SQL driver.Scanner interface so it can be used as a scan destination: var u uuid.NullUUID err := db.QueryRow("SELECT name FROM foo WHERE id=?", id).Scan(&u) ...

if u.Valid { // use u.UUID } else { // NULL value } func (NullUUID) MarshalBinary added in v1.3.0 func (nu NullUUID) MarshalBinary() ([]byte, error) MarshalBinary implements encoding.BinaryMarshaler.

func (NullUUID) MarshalJSON added in v1.3.0 func (nu NullUUID) MarshalJSON() ([]byte, error) MarshalJSON implements json.
