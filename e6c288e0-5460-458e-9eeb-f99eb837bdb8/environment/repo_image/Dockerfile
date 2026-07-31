FROM python:3.9-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/kui.git && git fetch --depth 1 origin e1f5ce5506cfa3b35e37103b9d0895d5e83b1db0 && git checkout e1f5ce5506cfa3b35e37103b9d0895d5e83b1db0
WORKDIR /testbed
RUN pip install --no-cache-dir baize>=0.22.0 pydantic>=2 pytest pytest-json-report typing-extensions>=4.2.0 httpx httpx_ws pytest-asyncio
RUN pip install -e ".[test]" || true
RUN git config --global --add safe.directory /testbed
