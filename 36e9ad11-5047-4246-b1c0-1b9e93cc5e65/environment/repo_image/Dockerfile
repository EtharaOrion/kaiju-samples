FROM commit0.base.python3.10:latest

ARG http_proxy=""
ARG https_proxy=""
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG no_proxy="localhost,127.0.0.1,::1"
ARG NO_PROXY="localhost,127.0.0.1,::1"

COPY ./setup.sh /root/
RUN chmod +x /root/setup.sh && /bin/bash /root/setup.sh

WORKDIR /testbed/

RUN uv pip install --system "dill" "graphviz" "mock" "pycodestyle" "pygraphviz" "pytest" "pytest-cov" "pytest-json-report" "pytest-runner" "pytest-xdist" "six" "tox" || pip install --no-cache-dir "dill" "graphviz" "mock" "pycodestyle" "pygraphviz" "pytest" "pytest-cov" "pytest-json-report" "pytest-runner" "pytest-xdist" "six" "tox"

RUN uv pip install --system -e "." || pip install --no-cache-dir -e "."

RUN python -c "import dill" 2>/dev/null || echo "WARN: cannot import dill"; python -c "import graphviz" 2>/dev/null || echo "WARN: cannot import graphviz"; python -c "import mock" 2>/dev/null || echo "WARN: cannot import mock"; python -c "import pycodestyle" 2>/dev/null || echo "WARN: cannot import pycodestyle"; python -c "import pygraphviz" 2>/dev/null || echo "WARN: cannot import pygraphviz"; python -c "import six" 2>/dev/null || echo "WARN: cannot import six"; python -c "import tox" 2>/dev/null || echo "WARN: cannot import tox"

RUN pip install --no-cache-dir -U pytest pytest-cov coverage pytest-json-report

RUN pip freeze > /testbed/.dep-manifest.txt

WORKDIR /testbed/
