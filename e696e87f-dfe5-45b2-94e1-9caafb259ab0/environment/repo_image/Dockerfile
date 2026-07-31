FROM python:3.9-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/datasketch.git && git fetch --depth 1 origin b97eb128d016f10e3164857a16179f51720b2308 && git checkout b97eb128d016f10e3164857a16179f51720b2308
WORKDIR /testbed
RUN pip install --no-cache-dir cassandra-driver>=3.20 coverage mock>=2.0.0 mockredispy nose>=1.3.7 nose-exclude>=0.5.0 numpy>=1.11 pygments>=2.20.0 pymongo>=3.9.0 pytest pytest-asyncio pytest-cov pytest-json-report pytest-rerunfailures redis>=2.10.0 scipy>=1.0.0 motor
RUN pip install -e ".[test]" || true
RUN git config --global --add safe.directory /testbed
