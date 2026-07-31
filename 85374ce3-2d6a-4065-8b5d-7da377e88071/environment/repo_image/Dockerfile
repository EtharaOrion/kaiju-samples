FROM python:3.8-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/neat-python.git && git fetch --depth 1 origin c59d829cb32a41f06bfae8591be76048640e2d8a && git checkout c59d829cb32a41f06bfae8591be76048640e2d8a
WORKDIR /testbed
RUN pip install --no-cache-dir coveralls>=3.0 pytest pytest-cov>=4.0 pytest-json-report
RUN pip install -e ".[dev]" || true
RUN git config --global --add safe.directory /testbed
