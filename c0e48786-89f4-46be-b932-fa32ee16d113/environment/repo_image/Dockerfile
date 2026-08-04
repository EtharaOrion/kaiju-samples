FROM kaiju.base.go:1.25.0

ARG http_proxy=""
ARG https_proxy=""
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG no_proxy="localhost,127.0.0.1,::1"
ARG NO_PROXY="localhost,127.0.0.1,::1"

COPY ./setup.sh /root/
RUN chmod +x /root/setup.sh && /bin/bash /root/setup.sh

WORKDIR /testbed/
