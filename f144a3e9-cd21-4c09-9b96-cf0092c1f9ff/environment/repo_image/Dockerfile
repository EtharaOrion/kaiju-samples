FROM python:3.11-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/btclib.git && git fetch --depth 1 origin fe5cb942954e2645f2f7b65c5367634dbbc306fa && git checkout fe5cb942954e2645f2f7b65c5367634dbbc306fa
WORKDIR /testbed
RUN pip install --no-cache-dir autoflake bandit black btclib_libsecp256k1 check-manifest coverage flake8 isort mypy pip pre-commit pylint pyroma pytest pytest-cov pytest-json-report pytest-xdist pyupgrade setuptools tox twine wheel
RUN pip install -e "." || true
RUN git config --global --add safe.directory /testbed
