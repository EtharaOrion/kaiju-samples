FROM python:3.7-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/jsons.git && git fetch --depth 1 origin 8d69e8cd3e1322e2225577df5da1da4a3fa32a2f && git checkout 8d69e8cd3e1322e2225577df5da1da4a3fa32a2f
WORKDIR /testbed
RUN pip install --no-cache-dir pytest pytest-json-report typish>=1.9.2 attrs
RUN pip install -e "." || true
RUN git config --global --add safe.directory /testbed
