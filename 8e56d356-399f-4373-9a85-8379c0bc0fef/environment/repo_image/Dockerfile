FROM python:3.9-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/etl-parser.git && git fetch --depth 1 origin 365736dd243606bd07764bbf6bbf9465ef019a75 && git checkout 365736dd243606bd07764bbf6bbf9465ef019a75
WORKDIR /testbed
RUN pip install --no-cache-dir pytest pytest-json-report
RUN git config --global --add safe.directory /testbed
