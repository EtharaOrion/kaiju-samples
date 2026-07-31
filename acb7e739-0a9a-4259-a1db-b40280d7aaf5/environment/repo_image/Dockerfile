FROM rust:stable-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git build-essential pkg-config libssl-dev cmake python3 && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/nexosim.git && git fetch --depth 1 origin e1c25de58d8e09fc9b6a93b4ab200abd61790264 && git checkout e1c25de58d8e09fc9b6a93b4ab200abd61790264
WORKDIR /testbed
RUN cargo fetch || true
RUN git config --global --add safe.directory /testbed
