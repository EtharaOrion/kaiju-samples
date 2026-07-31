ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LANG=C.UTF-8
RUN (nop) set -eux;  apt-get update;  apt-get install -y --no-install-recommends   ca-certificates   netbase   tzdata  ;  rm -rf /var/lib/apt/lists/* # buildkit
ENV GPG_KEY=E3FF2839C048B25C084DEBE9B26995E310250568
ENV PYTHON_VERSION=3.9.25
ENV PYTHON_SHA256=00e07d7c0f2f0cc002432d1ee84d2a40dae404a99303e3f97701c10966c91834
RUN (nop) set -eux;   savedAptMark="$(apt-mark showmanual)";  apt-get update;  apt-get install -y --no-install-recommends   dpkg-dev   gcc   gnupg   libbluetooth-dev   libbz2-dev   libc6-dev   libdb-dev   libffi-dev   libgdbm-dev   liblzma-dev   libncursesw5-dev   libreadline-dev   libsqlite3-dev   libssl-dev   make   tk-dev   uuid-dev   wget   xz-utils   zlib1g-dev  ;   wget -O python.tar.xz "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz";  echo "$PYTHON_SHA256 *python.tar.xz" | sha256sum -c -;  wget -O python.tar.xz.asc "https://www.python.org/ftp/python/${PYTHON_VERSION%%[a-z]*}/Python-$PYTHON_VERSION.tar.xz.asc";  GNUPGHOME="$(mktemp -d)"; export GNUPGHOME;  gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys "$GPG_KEY";  gpg --batch --verify python.tar.xz.asc python.tar.xz;  gpgconf --kill all;  rm -rf "$GNUPGHOME" python.tar.xz.asc;  mkdir -p /usr/src/python;  tar --extract --directory /usr/src/python --strip-components=1 --file python.tar.xz;  rm python.tar.xz;   cd /usr/src/python;  gnuArch="$(dpkg-architecture --query DEB_BUILD_GNU_TYPE)";  ./configure   --build="$gnuArch"   --enable-loadable-sqlite-extensions   --enable-optimizations   --enable-option-checking=fatal   --enable-shared   --with-ensurepip  ;  nproc="$(nproc)";  EXTRA_CFLAGS="$(dpkg-buildflags --get CFLAGS)";  LDFLAGS="$(dpkg-buildflags --get LDFLAGS)";  LDFLAGS="${LDFLAGS:--Wl},--strip-all";  make -j "$nproc"   "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}"   "LDFLAGS=${LDFLAGS:-}"  ;  rm python;  make -j "$nproc"   "EXTRA_CFLAGS=${EXTRA_CFLAGS:-}"   "LDFLAGS=${LDFLAGS:--Wl},-rpath='\$\$ORIGIN/../lib'"   python  ;  make install;   cd /;  rm -rf /usr/src/python;   find /usr/local -depth   \(    \( -type d -a \( -name test -o -name tests -o -name idle_test \) \)    -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \)   \) -exec rm -rf '{}' +  ;   ldconfig;   apt-mark auto '.*' > /dev/null;  apt-mark manual $savedAptMark;  find /usr/local -type f -executable -not \( -name '*tkinter*' \) -exec ldd '{}' ';'   | awk '/=>/ { so = $(NF-1); if (index(so, "/usr/local/") == 1) { next }; gsub("^/(usr/)?", "", so); printf "*%s\n", so }'   | sort -u   | xargs -rt dpkg-query --search   | awk 'sub(":$", "", $1) { print $1 }'   | sort -u   | xargs -r apt-mark manual  ;  apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false;  rm -rf /var/lib/apt/lists/*;   export PYTHONDONTWRITEBYTECODE=1;  python3 --version;   pip3 install   --disable-pip-version-check   --no-cache-dir   --no-compile   'setuptools==79.0.1'   'wheel<0.46'  ;  pip3 --version # buildkit
RUN (nop) set -eux;  for src in idle3 pip3 pydoc3 python3 python3-config; do   dst="$(echo "$src" | tr -d 3)";   [ -s "/usr/local/bin/$src" ];   [ ! -e "/usr/local/bin/$dst" ];   ln -svT "$src" "/usr/local/bin/$dst";  done # buildkit
CMD ["python3"]
ARG TARGETARCH
ARG http_proxy=
ARG https_proxy=
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG no_proxy=localhost,127.0.0.1,::1
ARG NO_PROXY=localhost,127.0.0.1,::1
ARG CA_CERT_PATH=/etc/ssl/certs/ca-certificates.crt
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt HTTPLIB2_CA_CERTS=/etc/ssl/certs/ca-certificates.crt PIP_CERT=/etc/ssl/certs/ca-certificates.crt
RUN |8 TARGETARCH=arm64 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 CA_CERT_PATH=/etc/ssl/certs/ca-certificates.crt (nop) apt-get update && apt-get install -y --no-install-recommends     git     build-essential     ca-certificates     curl     jq     libatomic1     locales     locales-all     && rm -rf /var/lib/apt/lists/* # buildkit
RUN |8 TARGETARCH=arm64 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 CA_CERT_PATH=/etc/ssl/certs/ca-certificates.crt (nop) pip install --no-cache-dir --upgrade pip # buildkit
RUN |8 TARGETARCH=arm64 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 CA_CERT_PATH=/etc/ssl/certs/ca-certificates.crt (nop) mkdir -p /etc/pki/tls/certs /etc/pki/tls /etc/pki/ca-trust/extracted/pem /etc/ssl/certs &&     ln -sf /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt 2>/dev/null;     ln -sf /etc/ssl/certs/ca-certificates.crt /etc/ssl/cert.pem 2>/dev/null;     ln -sf /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/cert.pem 2>/dev/null;     ln -sf /etc/ssl/certs/ca-certificates.crt /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem 2>/dev/null;     ln -sf /etc/ssl/certs /etc/pki/tls/certs 2>/dev/null;     true # buildkit
RUN |8 TARGETARCH=arm64 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 CA_CERT_PATH=/etc/ssl/certs/ca-certificates.crt (nop) if [ -f /run/secrets/mitm_ca ]; then         cp /run/secrets/mitm_ca /usr/local/share/ca-certificates/mitm-ca.crt &&         update-ca-certificates &&         echo "MITM CA certificate installed successfully";     else         echo "No MITM CA certificate found, skipping";     fi # buildkit
ARG http_proxy=
ARG https_proxy=
ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG no_proxy=localhost,127.0.0.1,::1
ARG NO_PROXY=localhost,127.0.0.1,::1
COPY ./setup.sh /root/ # buildkit
RUN |6 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 (nop) chmod +x /root/setup.sh && /bin/bash /root/setup.sh # buildkit
WORKDIR /testbed/
RUN |6 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 (nop) pip install --no-cache-dir "construct" "pytest" "pytest-json-report" # buildkit
RUN |6 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 (nop) pip install --no-cache-dir -e "." # buildkit
RUN |6 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 (nop) python -c "import construct" 2>/dev/null || echo "WARN: cannot import construct" # buildkit
RUN |6 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 (nop) pip install --no-cache-dir -U pytest pytest-cov coverage pytest-json-report # buildkit
RUN |6 http_proxy= https_proxy= HTTP_PROXY= HTTPS_PROXY= no_proxy=localhost,127.0.0.1,::1 NO_PROXY=localhost,127.0.0.1,::1 (nop) pip freeze > /testbed/.dep-manifest.txt # buildkit
WORKDIR /testbed/
