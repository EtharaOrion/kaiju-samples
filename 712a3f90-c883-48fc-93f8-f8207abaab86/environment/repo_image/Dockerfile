FROM rust:beta, nightly, stable-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git build-essential pkg-config libssl-dev cmake python3 && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/etherparse.git && git fetch --depth 1 origin 893b0fe3f77474ef7ee005b1ec6c84e2acbc9e85 && git checkout 893b0fe3f77474ef7ee005b1ec6c84e2acbc9e85
WORKDIR /testbed
RUN cargo fetch || true
RUN git config --global --add safe.directory /testbed
