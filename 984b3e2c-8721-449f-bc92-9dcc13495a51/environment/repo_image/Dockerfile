FROM python:3.9-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/oauthlib.git && git fetch --depth 1 origin 228f9d3cce7b32099972e39639f2d5369cf07628 && git checkout 228f9d3cce7b32099972e39639f2d5369cf07628
WORKDIR /testbed
RUN pip install --no-cache-dir blinker==1.4 cryptography>=3.0.0 pyjwt>=2.0.0,<3 pytest pytest-cov>=2.6 pytest-json-report pytest-subtests
RUN pip install -e "." || true
RUN git config --global --add safe.directory /testbed
