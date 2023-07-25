FROM ubuntu:22.04 as builder

RUN apt-get update -y && \
    apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        build-essential \
        git \
        libglib2.0-dev \
        libssl-dev \
        python3-pip \
        python3 \
        libseccomp-dev \
        cmake

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /workspace

COPY openssl.cnf.j2 openssl.cnf.j2

RUN python3 -m pip install --no-cache-dir j2cli==0.3.10
ENV openssl_install_path=/usr/
ENV p11_module_path=/usr/local/lib/libpkcs11-proxy.so
RUN j2 openssl.cnf.j2 > /workspace/openssl.cnf

RUN git clone https://github.com/SUNET/pkcs11-proxy.git /workspace/pkcs11-proxy
COPY 0001-Fix-slotID.patch /workspace
WORKDIR /workspace/pkcs11-proxy

RUN git apply /workspace/0001-Fix-slotID.patch && \
    cmake . && make && make install

FROM ubuntu:22.04 as runtime

EXPOSE 6513

HEALTHCHECK --interval=5s --timeout=3s CMD curl -s --insecure https://localhost:6513 || exit 1

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        ncat \
        opensc \
        libengine-pkcs11-openssl \
        python3-pip \
        python3 \
        curl \
        g++ \
        git \
        libc6-dev \
        libglib2.0-dev \
        libssl-dev \
        libssh-dev \
        make \
        cmake && \
    apt-get clean && \
    rm -rf  /var/log/*log /var/lib/apt/lists/* /var/log/apt/* /var/lib/dpkg/*-old /var/cache/debconf/*-old

WORKDIR /oran/NetConfServer
RUN git clone https://github.com/CESNET/libyang.git
WORKDIR /oran/NetConfServer/libyang/build
RUN cmake -DENABLE_BUILD_TESTS=OFF .. && make && make install

WORKDIR /oran/NetConfServer/libyang
RUN git clone https://github.com/sysrepo/sysrepo.git
WORKDIR /oran/NetConfServer/libyang/sysrepo/build
RUN cmake -DSHM_DIR=/tmp/shm -DREPO_PATH=/tmp/sysrepo -DENABLE_TESTS=OFF .. && make && make install
RUN ldconfig

WORKDIR /oran/NetConfServer/libyang/sysrepo
RUN git clone https://github.com/CESNET/libnetconf2.git
WORKDIR /oran/NetConfServer/libyang/sysrepo/libnetconf2
COPY 0003-libnetconf2-add-pkcs11-support.patch .
RUN git apply 0003-libnetconf2-add-pkcs11-support.patch
WORKDIR /oran/NetConfServer/libyang/sysrepo/libnetconf2/build
RUN cmake -DENABLE_TLS=ON -DENABLE_SSH=ON -DENABLE_DNSSEC=OFF .. && make && make install

WORKDIR /oran/NetConfServer/libyang/sysrepo/libnetconf2
RUN git clone https://github.com/CESNET/netopeer2.git
WORKDIR /oran/NetConfServer/libyang/sysrepo/libnetconf2/netopeer2
COPY 0004-netopeer2-comms-fix.patch .
RUN git apply 0004-netopeer2-comms-fix.patch
WORKDIR /oran/NetConfServer/libyang/sysrepo/libnetconf2/netopeer2/build
RUN cmake .. && make && make install    

# create new user
ARG USER=kmra
ARG UID=1000
ENV CTK_USER=${USER}

RUN useradd -m -d /tmp ${USER} --uid=${UID} --user-group

WORKDIR /

COPY --from=builder /usr/local/lib/lib* /usr/local/lib/
COPY --from=builder --chown=${USER}:${USER} /workspace/openssl.cnf /etc/openssl.cnf
COPY --from=builder /workspace/pkcs11-proxy/lib* /usr/local/lib/

ENV LD_LIBRARY_PATH="/usr/lib:/usr/local/lib"

COPY oran_commands.sh /workspace/oran_commands.sh
RUN chmod u+x /workspace/oran_commands.sh && \
    mkdir /opt/intel/ && cp -R /tmp/sysrepo /opt/intel/ && \
    chown -R ${USER}:${USER} /opt/intel/sysrepo && \
    chown -R ${USER}:${USER} /workspace/oran_commands.sh

USER ${USER}

ENTRYPOINT ["/workspace/oran_commands.sh"]
