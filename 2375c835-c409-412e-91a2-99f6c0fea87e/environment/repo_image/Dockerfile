FROM kaiju.base.python3.7:latest

ARG http_proxy=""
ARG https_proxy=""
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG no_proxy="localhost,127.0.0.1,::1"
ARG NO_PROXY="localhost,127.0.0.1,::1"

COPY ./setup.sh /root/
RUN chmod +x /root/setup.sh && /bin/bash /root/setup.sh

WORKDIR /testbed/

RUN printf '%s\n' 'pytest' 'pytest-json-report' > /tmp/kaiju-pip-requirements.txt && (uv pip install --system -r /tmp/kaiju-pip-requirements.txt || pip install --no-cache-dir -r /tmp/kaiju-pip-requirements.txt)

RUN uv pip install --system -e "." || pip install --no-cache-dir -e "."

RUN pip install --no-cache-dir -U pytest pytest-cov coverage pytest-json-report

RUN pip freeze > /testbed/.dep-manifest.txt

WORKDIR /testbed/
