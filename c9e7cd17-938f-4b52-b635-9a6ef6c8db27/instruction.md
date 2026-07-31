# Implement `allegro/bigcache`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `allegro/bigcache`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://pkg.go.dev/github.com/allegro/bigcache/v3

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Details Learn more about best practices Repository github.com/allegro/bigcache Links Open Source Insights README ¶ Expand ▾ Documentation Overview Example Valid go.mod file Redistributable license Tagged version Stable version BigCache build build passing passing coverage coverage 92% 92% go report go report retired retired Fast, concurrent, evicting in-memory cache written to keep big number of entries without impact on performance. BigCache keeps entries on heap but omits GC for them. To achieve that, operations on byte slices take place, therefore entries (de)serialization in front of the cache will be needed in most use cases.

Requires Go 1.12 or newer.

Usage Si l i iti li ti BigCache build build passing passing coverage coverage 92% 92% go report go report retired retired Fast, concurrent, evicting in-memory cache written to keep big number of entries without impact on performance. BigCache keeps entries on heap but omits GC for them. To achieve that, operations on byte slices take place, therefore entries (de)serialization in front of the cache will be needed in most use cases.

Requires Go 1.12 or newer.

Usage Si l i iti li ti README Discover Packages > github.com/allegro/bigcache/v3 bigcache package module Version: v3.1.0 Latest | Published: Oct 24, 2022 | License: Apache-2.0 | Imports: 11 | Imported by: 356 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Okay Example (Custom) Index Constants Variables func DefaultLogger() *log.Logger type BigCache func New(ctx context.Context, config Config) (*BigCache, error) func NewBigCache(config Config) (*BigCache, error) DEPRECATED func (c *BigCache) Append(key string, entry []byte) error func (c *BigCache) Capacity() int func (c *BigCache) Close() error func (c *BigCache) Delete(key string) error func (c *BigCache) Get(key string) ([]byte, error) func (c *BigCache) GetWithInfo(key string) ([]byte, Response, error) func (c *BigCache) Iterator() *EntryInfoIterator func (c *BigCache) KeyMetadata(key string) Metadata func (c *BigCache) Len() int func (c *BigCache) Reset() error func (c *BigCache) ResetStats() error func (c *BigCache) Set(key string, entry []byte) error func (c *BigCache) Stats() Stats type Config func DefaultConfig(eviction time.Duration) Config func (c Config) OnRemoveFilterSet(reasons ...RemoveReason) Config type EntryInfo func (e EntryInfo) Hash() uint64 func (e EntryInfo) Key() string func (e EntryInfo) Timestamp() uint64 func (e EntryInfo) Value() []byte type EntryInfoIterator func (it *EntryInfoIterator) SetNext() bool func (it *EntryInfoIterator) Value() (EntryInfo, error) type Hasher type Logger type Metadata type RemoveReason type Response type Stats Examples Package Package (Custom) go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Constants View Source const ( // Expired means the key is past its LifeWindow.

Expired = RemoveReason(1) // NoSpace means the key is the oldest and the cache size was at its maximum when Se // entry exceeded the maximum shard size.

NoSpace = RemoveReason(2) // Deleted means Delete was called and this key was removed as a result.

Deleted = RemoveReason(3) ) View Source const ErrCannotRetrieveEntry = iteratorError("Could not retrieve entry from cache") ErrCannotRetrieveEntry is reported when entry cannot be retrieved from underlying View Source const ErrInvalidIteratorState = iteratorError("Iterator is in invalid state. Use SetNext ErrInvalidIteratorState is reported when iterator is in invalid state Variables View Source var ( // ErrEntryNotFound is an error type struct which is returned when entry was not fou ErrEntryNotFound = errors.New("Entry not found") ) func DefaultLogger func DefaultLogger() *log.Logger DefaultLogger returns a `Logger` implementation backed by stdlib's log Types type BigCache type BigCache struct { // contains filtered or unexported fields } BigCache is fast, concurrent, evicting cache created to keep big number of entries without impact on performance. It keeps entries on heap but omits GC for them. To achieve that, operations take go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

place on byte arrays, therefore entries (de)serialization in front of the cache will be needed in most use cases.

func New added in v3.1.0 func New(ctx context.Context, config Config) (*BigCache, error) New initialize new instance of BigCache func NewBigCache DEPRECATED Show func (*BigCache) Append func (c *BigCache) Append(key string, entry []byte) error Append appends entry under the key if key exists, otherwise it will set the key (same behaviour as Set()). With Append() you can concatenate multiple entries under the same key in an lock optimized way.

func (*BigCache) Capacity func (c *BigCache) Capacity() int Capacity returns amount of bytes store in the cache.

func (*BigCache) Close func (c *BigCache) Close() error Close is used to signal a shutdown of the cache when you are done with it. This allows the cleaning goroutines to exit and ensures references are not kept to the cache preventing GC of the entire cache.

func (*BigCache) Delete func (c *BigCache) Delete(key string) error Delete removes the key func (*BigCache) Get func (c *BigCache) Get(key string) ([]byte, error) Get reads entry for the key. It returns an ErrEntryNotFound when no entry exists for the given key.

func (*BigCache) GetWithInfo func (c *BigCache) GetWithInfo(key string) ([]byte, Response, error) go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

GetWithInfo reads entry for the key with Response info. It returns an ErrEntryNotFound when no entry exists for the given key.

func (*BigCache) Iterator func (c *BigCache) Iterator() *EntryInfoIterator Iterator returns iterator function to iterate over EntryInfo's from whole cache.

func (*BigCache) KeyMetadata func (c *BigCache) KeyMetadata(key string) Metadata KeyMetadata returns number of times a cached resource was requested.

func (*BigCache) Len func (c *BigCache) Len() int Len computes number of entries in cache func (*BigCache) Reset func (c *BigCache) Reset() error Reset empties all cache shards func (*BigCache) ResetStats added in v3.1.0 func (c *BigCache) ResetStats() error ResetStats resets cache stats func (*BigCache) Set func (c *BigCache) Set(key string, entry []byte) error Set saves entry under the key func (*BigCache) Stats func (c *BigCache) Stats() Stats Stats returns cache's statistics type Config type Config struct { // Number of cache shards, value must be a power of two go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Shards int // Time after which entry can be evicted LifeWindow time.Duration // Interval between removing expired entries (clean up).

// If set to <= 0 then no action is performed. Setting to < 1 second is counterprodu CleanWindow time.Duration // Max number of entries in life window. Used only to calculate initial size for cac // When proper value is set then additional memory allocation does not occur.

MaxEntriesInWindow int // Max size of entry in bytes. Used only to calculate initial size for cache shards.

MaxEntrySize int // StatsEnabled if true calculate the number of times a cached resource was requeste StatsEnabled bool // Verbose mode prints information about new memory allocation Verbose bool // Hasher used to map between string keys and unsigned 64bit integers, by default fn Hasher Hasher // HardMaxCacheSize is a limit for BytesQueue size in MB.

// It can protect application from consuming all available memory on machine, theref // Default value is 0 which means unlimited size. When the limit is higher than 0 an // the oldest entries are overridden for the new ones. The max memory consumption wi // HardMaxCacheSize due to Shards' s additional memory. Every Shard consumes additio // and statistics (map[uint64]uint32) the size of this map is equal to number of ent // cache ~ 2×(64+32)×n bits + overhead or map itself.

HardMaxCacheSize int // OnRemove is a callback fired when the oldest entry is removed because of its expi // for the new entry, or because delete was called.

// Default value is nil which means no callback and it prevents from unwrapping the // ignored if OnRemoveWithMetadata is specified.

OnRemove func(key string, entry []byte) // OnRemoveWithMetadata is a callback fired when the oldest entry is removed because // for the new entry, or because delete was called. A structure representing details // Default value is nil which means no callback and it prevents from unwrapping the OnRemoveWithMetadata func(key string, entry []byte, keyMetadata Metadata) // OnRemoveWithReason is a callback fired when the oldest entry is removed because o // for the new entry, or because delete was called. A constant representing the reas // Default value is nil which means no callback and it prevents from unwrapping the // Ignored if OnRemove is specified.

OnRemoveWithReason func(key string, entry []byte, reason RemoveReason) // Logger is a logging interface and used in combination with `Verbose` // Defaults to `DefaultLogger()` Logger Logger // contains filtered or unexported fields } Config for BigCache func DefaultConfig func DefaultConfig(eviction time.Duration) Config go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

DefaultConfig initializes config with default values. When load for BigCache can be predicted in advance then it is better to use custom config.

func (Config) OnRemoveFilterSet func (c Config) OnRemoveFilterSet(reasons ...RemoveReason) Config OnRemoveFilterSet sets which remove reasons will trigger a call to OnRemoveWithReason.
