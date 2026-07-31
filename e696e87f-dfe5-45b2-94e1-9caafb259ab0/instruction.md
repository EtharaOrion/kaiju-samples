# Implement `ekzhu/datasketch`

You are given a Python repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a `pass` statement.

You need to complete the implementations for all functions (i.e., those with `pass` statements) and pass the unit tests.
Do not change the names of existing functions or classes, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `ekzhu/datasketch`
- Source directory to implement: `datasketch/`
- Test command: `pytest` (run against `test`)
- Specification / docs: 

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

 / API Documentation API Documentation MinHash MinHash is a probabilistic data structure for computing Jaccard similarity between sets.

Parameters: num_perm (int) – Number of random permutation functions. It will be ignored if hashvalues is not None.

seed (int) – The random seed controls the set of random permutation functions generated for this MinHash.

gpu_mode – {‘disable’, ‘detect’, ‘always’}, default ‘disable’ Controls GPU use in update_batch() .

'disable' — always CPU.

'detect' — use GPU if available, otherwise CPU.

'always' — require GPU; raise RuntimeError if CuPy/CUDA is unavailable.

hashfunc (Optional[Callable]) – The hash function used by this MinHash. It takes the input passed to the update() method and returns an integer that can be encoded with 32 bits for the “affine32” and “legacy” schemes, or with 64 bits for the “affine64” scheme. If None (default), a SHA1-based hash function matching the scheme width is used ( datasketch.hashfunc.sha1_hash32() or datasketch.hashfunc.sha1_hash64() ). Users can use farmhash for better performance. See the example in update() .

hashobj (deprecated) – This argument is deprecated since version 1.4.0. It is a no-op and has been replaced by hashfunc.

hashvalues (Optional[Iterable]) – The hash values is the internal state of the MinHash. It can be specified for faster initialization using the existing hashvalues of another MinHash. scheme must then be specified explicitly, because hash values carry no trace of the scheme that produced them.

permutations (Optional[Tuple[Iterable, Iterable]]) – The permutation function parameters as a tuple of two lists. This argument can be specified for faster initialization using the existing permutations class datasketch.MinHash(num_perm: int = 128, seed: int = 1, gpu_mode: Literal['disable', 'detect', 'always'] = 'disable', hashfunc: Callable | None = None, hashobj: object | None = None, hashvalues: ArrayLike | None = None, permutations: tuple[ArrayLike, ArrayLike] | ArrayLike | None = None, scheme: Literal['affine32', 'affine64', 'legacy'] | None = None) [source] from another MinHash. scheme must then be specified explicitly.

scheme (Optional[str]) – The permutation scheme: one of "affine32" , "affine64" , and "legacy" . If None (the default), the scheme is "affine32" ; however, when hashvalues or permutations are given, the scheme of the MinHash they came from must be passed explicitly ( "legacy" for values created by datasketch before 2.0.0).

"affine32" — the input hash is pre-mixed once with the 32-bit MurmurHash3 finalizer, then permuted with a * h + b mod 2^32 ( a odd, a bijection). Hash values are stored as uint32, halving memory use compared to "legacy" , and the permutation step is collision-free.

"affine64" — same construction over 64-bit hash values, for very large sets (roughly 100 million elements or more) where any 32-bit input hash saturates and inflates similarity estimates regardless of the permutation scheme.

"legacy" — the scheme used before version 2.0.0, kept for compatibility with existing serialized sketches. It is biased on large sets and slower; do not use it for new data.

MinHash created with different schemes cannot be compared, merged, or unioned.

Note Hashing and permutation generation always run on CPU to preserve existing semantics; only the permutation application and the columnwise min-reduction inside update_batch() may run on GPU.

Note To save memory usage, consider using datasketch.LeanMinHash .

Note Since version 1.1.1, MinHash will only support serialization using pickle. serialize and deserialize methods are removed, and are supported in datasketch.LeanMinHash instead. MinHash serialized before version 1.1.1 cannot be deserialized properly in newer versions (need to migrate?).

Note Since version 1.1.3, MinHash uses Numpy’s random number generator instead of Python’s built-in random package. This change makes the hash values consistent across different Python versions. The side-effect is that now MinHash created before version 1.1.3 won’t work (i.e., jaccard() , merge() and union() ) with those created after.

Note Since version 2.0.0, the default permutation scheme is "affine32" , which produces different hash values than earlier versions. MinHash pickled by earlier versions deserializes with scheme="legacy" and keeps working, but new MinHash interoperates with it only when created with scheme="legacy" explicitly. Any persisted LSH index must be rebuilt with sketches of a single scheme.

Update this MinHash with a new value. The value will be hashed using the hash function specified by the hashfunc argument in the constructor.

Parameters: b – The value to be hashed using the hash function specified.

Example To update with a new string value (using the default SHA1 hash function, which requires bytes as input): minhash = Minhash() minhash.update("new value".encode("utf-8")) We can also use a different hash function, for example, pyfarmhash: import farmhash def _hash_32(b): return farmhash.hash32(b) minhash = MinHash(hashfunc=_hash_32) minhash.update("new value") __init__(num_perm: int = 128, seed: int = 1, gpu_mode: Literal['disable', 'detect', 'always'] = 'disable', hashfunc: Callable | None = None, hashobj: object | None = None, hashvalues: ArrayLike | None = None, permutations: tuple[ArrayLike, ArrayLike] | ArrayLike | None = None, scheme: Literal['affine32', 'affine64', 'legacy'] | None = None)→ None [source] update(b)→ None [source] update_batch(b: Iterable)→ None [source] Update this MinHash with new values. The values will be hashed using the hash function specified by the hashfunc argument in the constructor.

Notes Hashing of input values always runs on CPU.

Permutation application + min-reduction may run on GPU depending on gpu_mode: ‘disable’ : CPU ‘detect’ : GPU if available else CPU ‘always’ : GPU (error if unavailable) Parameters: b (Iterable) – Values to be hashed using the hash function specified.

Examples Basic usage with string values (default SHA1 hash, requires bytes): from datasketch import MinHash m = MinHash() m.update_batch([s.encode("utf-8") for s in ["token1", "token2"]]) Using GPU mode if available: from datasketch import MinHash m = MinHash(num_perm=256, gpu_mode="detect") m.update_batch([b"token1", b"token2"]) Estimate the Jaccard similarity (resemblance) between the sets represented by this MinHash and the other.

Parameters: other (MinHash) – The other MinHash.

Returns: The Jaccard similarity, which is between 0.0 and 1.0.

Return type: float Raises: ValueError – If the two MinHashes have different numbers of permutation functions, different seeds, or different permutation schemes.

Estimate the cardinality count based on the technique described in this paper.

Returns: The estimated cardinality of the set represented by this MinHash.

jaccard(other: MinHash)→ float [source] count()→ float [source] Return type: int Merge the other MinHash with this one, making this one the union of both.

Parameters: other (MinHash) – The other MinHash.

Raises: ValueError – If the two MinHashes have different numbers of permutation functions, different seeds, or different permutation schemes.

Export the hash values, which is the internal state of the MinHash.

Returns: The hash values which is a Numpy array.

Return type: numpy.ndarray Returns: bool: If the current MinHash is empty - at the state of just initialized.

Clear the current state of the MinHash. All hash values are reset.

Return a copy; preserves gpu_mode (rehydrates caches lazily).

Returns: int: The number of hash values.

Returns: bool: If their schemes, seeds and hash values are all equal then two are equivalent.

Create a MinHash which is the union of the MinHash objects passed as arguments.

Parameters: *mhs (MinHash) – The MinHash objects to be united. The argument list length is variable, but must be at least 2.

Returns: a new union MinHash.

Return type: MinHash merge(other: MinHash)→ None [source] digest()→ ndarray [source] is_empty()→ bool [source] clear()→ None [source] copy()→ MinHash [source] __len__()→ int [source] __eq__(other: MinHash)→ bool [source] classmethod union(*mhs: MinHash)→ MinHash [source] Raises: ValueError – If the number of MinHash objects passed as arguments is less than 2, or if the MinHash objects passed as arguments have different seeds, different numbers of permutation functions, or different permutation schemes.

Example from datasketch import MinHash import numpy as np m1 = MinHash(num_perm=128) m1.update_batch(np.random.randint(low=0, high=30, size=10)) m2 = MinHash(num_perm=128) m2.update_batch(np.random.randint(low=0, high=30, size=10)) # Union m1 and m2.

m = MinHash.union(m1, m2) Compute MinHashes in bulk. This method avoids unnecessary overhead when initializing many minhashes by reusing the initialized state.

Parameters: b (Iterable) – An Iterable of lists of bytes, each list is hashed in to one MinHash in the output.

**minhash_kwargs – Keyword arguments used to initialize MinHash, will be used for all minhashes.

Returns: A list of computed MinHashes.

Return type: list[datasketch.MinHash] Example from datasketch import MinHash data = [[b"token1", b"token2", b"token3"], [b"token4", b"token5", b"token6"]] minhashes = MinHash.bulk(data, num_perm=64) Compute MinHashes in a generator. This method avoids unnecessary overhead when initializing many minhashes by reusing the initialized state.

Parameters: b (Iterable) – An Iterable of lists of bytes, each list is hashed in to one MinHash in the output.

minhash_kwargs – Keyword arguments used to initialize MinHash, will be used for all minhashes.

classmethod bulk(b: Iterable, **minhash_kwargs)→ list[MinHash] [source] classmethod generator(b: Iterable, **minhash_kwargs)→ Generator[MinHash, None, None] [source] Returns: a generator of computed MinHashes.
