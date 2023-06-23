#!/bin/bash

# Copyright (C) 2023 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

IMAGENAME="cnf-validation"

if [[ -z "${KUBECONFIG}" ]] && [[ -f ~/.kube/config ]]; then
    KUBECONFIG=~/.kube/config
fi

if [[ -z "${KUBECONFIG}" ]]; then
    echo "Error: no KUBECONFIG environment variable"
    exit 1
fi

if [[ -z "${http_proxy+x}" ]] || [[ -z "${https_proxy+x}" ]]; then
    echo "docker run -it --network host --rm \\"
    echo "    -v ${KUBECONFIG}:/${IMAGENAME}/kubeconfig ${IMAGENAME}"
    docker run -it --network host --rm \
        -v "${KUBECONFIG}:/${IMAGENAME}/kubeconfig" "${IMAGENAME}"
else
    echo "docker run -it --network host --rm \\"
    echo "    -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} \\"
    echo "    -v ${KUBECONFIG}:/${IMAGENAME}/kubeconfig ${IMAGENAME}"
    docker run -it --network host --rm \
        -e "http_proxy=${http_proxy}" -e "https_proxy=${https_proxy}" \
        -v "${KUBECONFIG}:/${IMAGENAME}/kubeconfig" "${IMAGENAME}"
fi

