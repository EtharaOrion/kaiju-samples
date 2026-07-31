FROM commit0.base.rust:1.96

ARG http_proxy=""
ARG https_proxy=""
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG no_proxy="localhost,127.0.0.1,::1"
ARG NO_PROXY="localhost,127.0.0.1,::1"

COPY ./setup.sh /root/
RUN chmod +x /root/setup.sh && /bin/bash /root/setup.sh

WORKDIR /testbed/

RUN cargo fetch

RUN cargo --version > /testbed/.dep-manifest.txt && rustc --version >> /testbed/.dep-manifest.txt

WORKDIR /testbed/
