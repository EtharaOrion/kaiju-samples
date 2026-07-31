FROM python:3.8-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/tryalgo.git && git fetch --depth 1 origin ee032b235e7af28b6cc56b95c0aa093551353d9d && git checkout ee032b235e7af28b6cc56b95c0aa093551353d9d
WORKDIR /testbed
RUN pip install --no-cache-dir pytest pytest-json-report
RUN pip install -e "." || true
RUN git config --global --add safe.directory /testbed
