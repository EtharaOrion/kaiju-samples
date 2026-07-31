FROM commit0.base.node22:latest

ARG http_proxy=""
ARG https_proxy=""
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG no_proxy="localhost,127.0.0.1,::1"
ARG NO_PROXY="localhost,127.0.0.1,::1"

COPY ./setup.sh /root/
RUN chmod +x /root/setup.sh && /bin/bash /root/setup.sh

WORKDIR /testbed/

RUN if [ -d node_modules ] && [ "$(ls -A node_modules 2>/dev/null | wc -l)" -gt 0 ]; then echo "node_modules OK: $(ls node_modules | wc -l) packages"; else echo "ERROR: node_modules missing or empty after install — refusing to publish broken image" >&2; exit 1; fi

RUN ls node_modules > /testbed/.dep-manifest.txt 2>/dev/null || true

WORKDIR /testbed/
