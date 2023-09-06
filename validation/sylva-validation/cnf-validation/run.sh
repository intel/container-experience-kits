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

TMP_KUBECONFIG=/tmp/kubeconfig
rm -rf ${TMP_KUBECONFIG}
cp "${KUBECONFIG}" "${TMP_KUBECONFIG}"
chmod o+r ${TMP_KUBECONFIG}

if [[ -z "${http_proxy+x}" ]] || [[ -z "${https_proxy+x}" ]]; then
    echo "docker run -it --network host --rm \\"
    echo "    -v ${TMP_KUBECONFIG}:/${IMAGENAME}/kubeconfig ${IMAGENAME}"
    docker run -it --network host --rm \
        -v "${TMP_KUBECONFIG}:/${IMAGENAME}/kubeconfig" "${IMAGENAME}"
else
    echo "docker run -it --network host --rm \\"
    echo "    -e http_proxy=${http_proxy} -e https_proxy=${https_proxy} \\"
    echo "    -v ${TMP_KUBECONFIG}:/${IMAGENAME}/kubeconfig ${IMAGENAME}"
    docker run -it --network host --rm \
        -e "http_proxy=${http_proxy}" -e "https_proxy=${https_proxy}" \
        -v "${TMP_KUBECONFIG}:/${IMAGENAME}/kubeconfig" "${IMAGENAME}"
fi

rm -rf ${TMP_KUBECONFIG}
