# Implement `distribution/distribution`

You are given a Go repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that panics on call.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `distribution/distribution`
- Source directory to implement: `./`
- Test command: `go test -json -count=1 ./...` (run against `.`)
- Specification / docs: https://pkg.go.dev/github.com/distribution/distribution/v3

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

Details Learn more about best practices Repository github.com/distribution/distribution Links Open Source Insights README ¶ Expand ▾ Documentation Overview Package distribution will define the interfaces for the components of docker distribution. The goal is to allow users to reliably package, ship and store content related to container images.

Valid go.mod file Redistributable license Tagged version Stable version build build no status no status go.dev reference License License Apache-2.0 Apache-2.0 codecov codecov 55% 55% build build no status no status go.dev reference License License Apache-2.0 Apache-2.0 codecov codecov 55% 55% README Discover Packages > github.com/distribution/distribution/v3 distribution package module Version: v3.1.1 Latest | Published: May 1, 2026 | License: Apache-2.0 | Imports: 11 | Imported by: 83 go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.

Okay This is currently a work in progress. More details are available in the README.md.

Index Variables func ManifestMediaTypes() (mediaTypes []string) func RegisterManifestSchema(mediaType string, u UnmarshalFunc) error type BlobCreateOption type BlobDeleter type BlobDescriptorService type BlobDescriptorServiceFactory type BlobEnumerator type BlobIngester type BlobProvider type BlobServer type BlobService type BlobStatter type BlobStore type BlobWriter type CreateOptions type Describable type Descriptor type ErrBlobInvalidDigest func (err ErrBlobInvalidDigest) Error() string type ErrBlobMounted func (err ErrBlobMounted) Error() string type ErrManifestBlobUnknown func (err ErrManifestBlobUnknown) Error() string type ErrManifestNameInvalid func (err ErrManifestNameInvalid) Error() string type ErrManifestUnknown func (err ErrManifestUnknown) Error() string type ErrManifestUnknownRevision func (err ErrManifestUnknownRevision) Error() string type ErrManifestUnverified func (ErrManifestUnverified) Error() string type ErrManifestVerification func (errs ErrManifestVerification) Error() string type ErrRepositoryNameInvalid func (err ErrRepositoryNameInvalid) Error() string type ErrRepositoryUnknown func (err ErrRepositoryUnknown) Error() string type ErrTagUnknown func (err ErrTagUnknown) Error() string type Manifest func UnmarshalManifest(ctHeader string, p []byte) (Manifest, v1.Descriptor, error) type ManifestEnumerator go.dev uses cookies from Google to deliver and enhance the quality of its services and to analyze traffic. Learn more.
