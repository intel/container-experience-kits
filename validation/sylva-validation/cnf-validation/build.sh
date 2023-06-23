#!/bin/bash

# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

IMAGENAME="cnf-validation"

if [[ "$( docker image ls | grep -c "^${IMAGENAME}" || true )" -eq 1 ]]; then
    docker rmi -f "${IMAGENAME}"
fi

if [[ -z "${http_proxy+x}" ]] || [[ -z "${https_proxy+x}" ]]; then
    docker build --rm . -t "${IMAGENAME}"
else
    echo -n "Building with http_proxy=${http_proxy} "
    echo "and https_proxy=${https_proxy}"
    docker build --rm . -t "${IMAGENAME}" \
        --build-arg="http_proxy=${http_proxy}" \
        --build-arg="https_proxy=${https_proxy}"
fi
