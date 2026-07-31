FROM rust:stable-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git build-essential pkg-config libssl-dev cmake python3 && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/erg.git && git fetch --depth 1 origin faba6bedfd67bfbe90aa958f43f81ba7228fd37b && git checkout faba6bedfd67bfbe90aa958f43f81ba7228fd37b
WORKDIR /testbed
RUN cargo fetch || true
RUN git config --global --add safe.directory /testbed
