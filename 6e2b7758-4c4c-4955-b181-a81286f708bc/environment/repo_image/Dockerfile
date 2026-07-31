FROM python:3.10-bookworm
RUN apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git && rm -rf /var/lib/apt/lists/*
RUN git init /testbed && cd /testbed && git remote add origin https://github.com/Zahgon/BlackSheep.git && git fetch --depth 1 origin 5cb9476fe374b49f2835c86cece5f07b61af074b && git checkout 5cb9476fe374b49f2835c86cece5f07b61af074b
WORKDIR /testbed
RUN pip install --no-cache-dir async-timeout>=4.0.0; python_version < '3.11' certifi>=2025.4.26 cryptography>=45.0.2,<47.0.0 Cython==3.1.4 defusedxml>=0.7.1 essentials>=1.1.8,<2.0 essentials-openapi>=1.2.0,<2.0 Flask[async]==3.1.1 guardpost>=1.0.4 h11>=0.14.0,<1.0.0 h2>=4.0.0,<5.0.0 httptools>=0.7.1; platform_python_implementation != 'PyPy' Hypercorn==0.17.3 itsdangerous~=2.2.0 Jinja2~=3.1.6 pydantic==2.12.3 pydantic_core==2.41.4 PyJWT==2.12.0 pytest==8.3.5 pytest-asyncio==1.2.0 pytest-cov==6.1.1 pytest-json-report requests==2.32.4 rodi~=2.0.8 setuptools==80.7.1 starlette>=0.37.0 uvicorn==0.34.2 websockets~=15.0.1
RUN BLACKSHEEP_NO_EXTENSIONS=1 pip install -e "." || true
RUN git config --global --add safe.directory /testbed
