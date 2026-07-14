# Implement `algesten/str0m`

You are given a Rust repository at `/testbed`, reset to a skeleton commit: every function body has been replaced with a stub that calls `todo!()` (or `unimplemented!()`) on invocation.

You need to complete the implementations for all functions and pass the unit tests.
Do not change the names of existing functions, types, traits, or methods, as they may be referenced from other code like unit tests, etc.
When you generate code, you must maintain the original formatting of the original function stubs (such as whitespaces), otherwise we will not be able to search/replace blocks for code modifications, and therefore you will receive a score of 0 for your generated code.

## Repository details

- Upstream project: `algesten/str0m`
- Source directory to implement: `src/`
- Test command: `cargo test` (run against `tests`)
- Specification / docs: https://docs.rs/str0m

Implement only the library source under the source directory. Do not modify the test files.

>>> Here is the Specification Information:

A Sans I/O WebRTC implementation in Rust.

This is a Sans I/O implementation meaning the Rtc instance itself is not doing any network talking.

Furthermore it has no internal threads or async tasks. All operations are happening from the calls of the public API.

This is deliberately not a standard RTCPeerConnection API since that isn’t a great fit for Rust. See more details in below section.

Join us We are discussing str0m things on Discord. Join us using this invitation link.

Usage The chat example shows how to connect multiple browsers together and act as an SFU (Selective Forwarding Unit). The example multiplexes all traffic over one server UDP socket and uses two threads (one for the web server, and one for the SFU loop).

TLS For the browser to do WebRTC, all traffic must be under TLS. The project ships with a self-signed certificate that is used for the examples. The certificate is for hostname str0m.test since TLD .test should never resolve to a real DNS name.

cargo run --example chat The log should prompt you to connect a browser to https://10.0.0.103:3000 – this will most likely cause a security warning that you must get the browser to accept.

The http-post example roughly illustrates how to receive media data from a browser client. The example is single threaded and is a bit simpler than the chat. It is a good starting point to understand the API.

Real example To see how str0m is used in a real project, check out BitWHIP – a CLI WebRTC Agent written in Rust.

Passive For passive connections, i.e. where the media and initial OFFER is made by a remote peer, we need these steps to open the connection.

Active Active connections means we are making the inital OFFER and waiting for a remote ANSWER to start the connection.

cargo run --example http-post // Instantiate a new Rtc instance.

A “mutation” is anything that takes &mut Rtc (directly or through a handle obtained from it). The common ones are: Rtc::handle_input — feeding a network packet or a timeout Writer::write / Writer::request_keyframe — sending media Channel::write — sending data channel data SdpApi::apply / DirectApi::* — negotiation Rtc::add_local_candidate / Rtc::add_remote_candidate Always: mutate → drain to Timeout → mutate → drain to Timeout → … Doing two mutations back-to-back without draining in between, or waiting on I/O while the engine still has output queued, leaves the engine in an inconsistent state and produces wrong behavior. Mutations issued from inside the drain loop (e.g. calling Writer::write in response to an Output::Event) are fine — the drain loop naturally continues calling poll_output afterward and so the invariant holds.

rtc.sdp_api().accept_answer(pending, answer).unwrap(); // Go to _run loop_ Canonical shape Driving an Rtc forward follows the same six-step shape, regardless of sync or async: 1. Wait for one of: the next timeout firing, an incoming network packet, or the application wanting to perform a mutation (e.g. write media).

2. Perform that ONE mutation — feed Input to handle_input, or call into a writer / channel / SDP API.

3. Poll Rtc::poll_output .

4. Handle the output: Output::Transmit is sent on the socket, Output::Event is dispatched to the application, Output::Timeout records the next deadline.

5. Goto 3 until poll_output returns Output::Timeout. Only then is the engine fully drained.

6. The returned timeout is what we wait on next — goto 1.

Output::Timeout(t) => break t, // Step 4: transmit on the socket and keep draining.

Output::Transmit(t) => { socket.send_to(&t.contents, t.destination).unwrap(); } // Step 4: hand the event to the application and keep draining // Events are mainly incoming media data from the remote peer, // but also data channel data and statistics.

Output::Event(e) => { if e == Event::IceConnectionStateChange(IceConnectionState return; } // TODO: handle other events here, such as incoming media d } } }; // === Step 1: wait for ONE of: the timeout firing, an incoming // packet, or application-side data. The example below uses a // blocking UDP socket with a read timeout. With async you would // `select!` over multiple futures; with application-side data you // would also include a channel.

Err(e) if matches!(e.kind(), ErrorKind::WouldBlock | ErrorKind::Tim Input::Timeout(Instant::now()) } Err(e) => { eprintln!("Error: {:?}", e); return; } }; rtc.handle_input(input).unwrap(); // === Step 6: back to the top of the outer loop (goto step 3). === } Sending media data When creating the media, we can decide which codecs to support, and they are negotiated with the remote side. Each codec corresponds to a “payload type” (PT). To send media data we need to figure out which PT to use when sending.

Writer::write is a mutation, so the single-mutation invariant applies: after writing, drain Rtc::poll_output to Output::Timeout before the next mutation on this Rtc.

Media time, wallclock and local time str0m has three main concepts of time. “now”, media time and wallclock.

Now Some calls in str0m, such as Rtc::handle_input takes a now argument that is a std::time::Instant . These calls “drive the time forward” in the internal state. This is used for everything like deciding when to produce various feedback reports (RTCP) to remote peers, to bandwidth estimation (BWE) and statistics.

Str0m has no internal clock calls. I.e. str0m never calls Instant::now() itself. All time is external input. That means it’s possible to construct test cases driving an Rtc instance faster than realtime (see the integration tests).

Media time Each RTP header has a 32 bit number that str0m calls media time. Media time is in some time base that is dependent on the codec, however all codecs in str0m use 90_000Hz for video and 48_000Hz for audio.

For video the MediaTime type is <timestamp>/90_000 str0m extends the 32 bit number in the RTP header to 64 bit taking into account “rollover”. 64 bit is such a large number the user doesn’t need to think about rollovers.

Wallclock // Obtain mid from Event::MediaAdded let mid: Mid = todo!(); // Create a media writer for the mid.

We can’t know the exact wallclock for media from a remote peer since not every device is synchronized with NTP. Every sender does periodically produce a Sender Report (SR) that contains the peer’s idea of its wallclock, however this number can be very wrong compared to “real” NTP time.

Furthermore, not all remote devices will have a linear idea of time passing that exactly matches the local time. A minute on the remote peer might not be exactly one minute locally.

These timestamps become important when handling simultaneous audio from multiple peers.

When writing media we need to provide str0m with an estimated wallclock. The simplest strategy is to only trust local time and use arrival time of the incoming UDP packet. Another simple strategy is to lock some time T at the first UDP packet, and then offset each wallclock using MediaTime, i.e. for video we could have T + <media time>/90_000 A production worthy SFU probably needs an even more sophisticated strategy weighing in all possible time sources to get a good estimate of the remote wallclock for a packet.

Crypto backends str0m supports multiple crypto backends via feature flags. The default is aws-lc-rs.

Feature Crate DTLS Platforms aws-lc-rs str0m-aws-lc-rs dimpl + AWS-LC-RS All rust-crypto str0m-rust-crypto dimpl + RustCrypto All openssl str0m-openssl OpenSSL (DTLS 1.2 only) All openssl-dimpl str0m-openssl dimpl + OpenSSL crypto All apple-crypto str0m-apple-crypto dimpl + Apple CryptoKit macOS/iOS wincrypto str0m-wincrypto Windows SChannel (DTLS 1.2 only) Windows wincrypto-dimpl str0m-wincrypto dimpl + Windows CNG Windows If multiple backend features are enabled, str0m automatically selects the backend in this priority order: aws-lc-rs , rust-crypto , openssl-dimpl, openssl, apple-crypto (Apple platforms only), wincrypt-dimpl (Windows only), wincrypto (Windows only).

If you disable the default features, you MUST explicitly configure an alternative crypto backend either process-wide or per-instance.

Process-wide default For applications, the easiest is to set a process-wide default at startup. Note that you can use any backend crate directly without enabling its feature flag: Crypto provider per Rtc instance Project status Str0m was originally developed by Martin Algesten of Lookback. We use str0m for a specific use case: str0m as a server SFU (as opposed to peer-2-peer). That means we are heavily testing and developing the parts needed for our use case. Str0m is intended to be an all-purpose WebRTC library, which means it also works for peer-2-peer, though that aspect has received less testing.

Performance is very good, there have been some work the discover and optimize bottlenecks. Such efforts are of course never ending with diminishing returns. While there are no glaringly obvious performance bottlenecks, more work is always welcome – both algorithmically and allocation/cloning in hot paths etc.

Design Output from the Rtc instance can be grouped into three kinds.

1. Events (such as receiving media or data channel data).

2. Network output. Data to be sent, typically from a UDP socket.

3. Timeouts. Indicates when the instance next expects a time input.

Input to the Rtc instance is: 1. User operations (such as sending media or data channel data).

2. Network input. Typically read from a UDP socket.

3. Timeouts. As obtained from the output above.

The correct use can be seen in the above Run loop or in the examples.

Sans I/O is a pattern where we turn both network input/output as well as time passing into external input to the API. This means str0m has no internal threads, just an enormous state machine that is // Set process default (will panic if called twice) // No need to enable the "rust-crypto" feature flag str0m_rust_crypto::default_provider().install_process_default(); use std::sync::Arc; use std::time::Instant; use str0m::Rtc; let rtc = Rtc::builder() .
