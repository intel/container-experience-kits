# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

FROM alpine:3.18

RUN apk update && \
    apk add --no-cache bash jq wget
WORKDIR /usr/local/bin
RUN wget -q "https://dl.k8s.io/release/$( wget -qO - \
        https://dl.k8s.io/release/stable.txt )/bin/linux/amd64/kubectl" && \
    chmod 755 kubectl

COPY image/ /cnf-validation/
WORKDIR /cnf-validation

ENV KUBECONFIG=/cnf-validation/kubeconfig

ENV USER=validation
ENV UID=65432
ENV GID=65432
RUN addgroup --gid "${GID}" "${USER}" && \
    adduser --disabled-password --gecos "" --home "$(pwd)" --ingroup \
        "${USER}" --no-create-home --uid "${UID}" -s /bin/bash "${USER}" && \
    chown -R validation:validation /cnf-validation
USER validation

HEALTHCHECK NONE
