FROM kaiju.base.python3.8:latest

ARG http_proxy=""
ARG https_proxy=""
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG no_proxy="localhost,127.0.0.1,::1"
ARG NO_PROXY="localhost,127.0.0.1,::1"

COPY ./setup.sh /root/
RUN chmod +x /root/setup.sh && /bin/bash /root/setup.sh

WORKDIR /testbed/

RUN apt-get update && apt-get install -y --no-install-recommends \
    gfortran \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

RUN uv pip install --system "numpy" "pytest" "pytest-json-report" "scikit-learn" "scipy" || pip install --no-cache-dir "numpy" "pytest" "pytest-json-report" "scikit-learn" "scipy"

RUN uv pip install --system -e "." || pip install --no-cache-dir -e "."

RUN python -c "import numpy" 2>/dev/null || echo "WARN: cannot import numpy"; python -c "import sklearn" 2>/dev/null || echo "WARN: cannot import sklearn"; python -c "import scipy" 2>/dev/null || echo "WARN: cannot import scipy"

RUN pip install --no-cache-dir -U pytest pytest-cov coverage pytest-json-report

RUN pip freeze > /testbed/.dep-manifest.txt

WORKDIR /testbed/
