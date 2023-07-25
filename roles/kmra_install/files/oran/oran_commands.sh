#!/bin/bash -e
export no_proxy="$no_proxy,localhost,127.0.0.1/8"

export NETOPEER2_SERVER_HOSTNAME="${NETOPEER2_SERVER_HOSTNAME:=netopeer2-server}"
export NETOPEER2_SERVER_PORT="${NETOPEER2_SERVER_PORT:=6513}"

export CLIENT_TOKEN="${CLIENT_TOKEN:=client_token}"
export CLIENT_KEY_LABEL="${CLIENT_KEY_LABEL:=client_key_priv}"
export TEST_UNIQUE_UID="${TEST_UNIQUE_UID:=unique_id_1234}"

export DEFAULT_USER_PIN="${DEFAULT_USER_PIN:=1234}"
export DEFAULT_SO_PIN="${DEFAULT_SO_PIN:=12345678}"

export PKCS11_PROXY_TLS_PSK_FILE="/etc/p11_proxy_tls.psk"

set -eu

# Import the certificate
pkcs11-tool --module=/usr/local/lib/libpkcs11-proxy.so -l -p "${DEFAULT_USER_PIN}" --type cert --read-object --label client_cert -o /tmp/cert.der

# Convert DER to PEM
openssl x509 -inform der -in /tmp/cert.der -out /tmp/oran_cert.pem

PKCS11_ENGINE_NAME="pkcs11"
TOKEN_KEY_URI="${PKCS11_ENGINE_NAME}:token=${CLIENT_TOKEN};object=${CLIENT_KEY_LABEL};pin-value=${DEFAULT_USER_PIN}"

export MODULE=/usr/local/lib/libpkcs11-proxy.so
export OPENSSL_CONF=/etc/openssl.cnf
export ansible_user_id="${CTK_USER}"
export ctk_loadkey_token_cert_path=/tmp/oran_cert.pem
export token_key_uri="${TOKEN_KEY_URI}"

cp -R /opt/intel/sysrepo /tmp/sysrepo

# Configure sysrepo
cd /opt/intel/sysrepo_config
sysrepocfg --edit=tls_keystore.xml --format=xml --datastore=running --module=ietf-keystore -v3
sysrepocfg --edit=tls_truststore.xml --format=xml --datastore=running --module=ietf-truststore -v3
sysrepocfg --edit=tls_listen.xml --format=xml --datastore=running --module=ietf-netconf-server -v3
sysrepocfg --copy-from=running --datastore=startup

echo -e "\033[0;31m------------------------------------------------------------"
echo -e "KMRA (Key Management Reference Application) is a proof-of-concept"
echo -e "software not suitable for production usage. Please note that the enclave"
echo -e "is signed with a test signing key. A production enclave should go through"
echo -e "the process of signing an enclave as explained in the section Enclave"
echo -e "Signing Tool in the Intel(R) SGX Developer Reference for Linux* OS"
echo -e "(https://download.01.org/intel-sgx/latest/linux-latest/docs/)"
echo -e "---------------------------------------------------------------\033[0m"

if [[ ${NETOPEER_TYPE} == "server" ]]; then
    echo "Starting netopeer2-server..."
    /usr/local/sbin/netopeer2-server -d -v3 -p /tmp/netopeer2-server.pid -f /tmp/.netopeer2-server
fi

if [[ ${NETOPEER_TYPE} == "client" ]]; then
    echo "Starting netopeer2-client..."
    # add the root ca to netopeer2 server
    echo -----BEGIN CERTIFICATE----- > /tmp/ca.pem
    sysrepocfg --export -v3 --xpath "/ietf-truststore:truststore/certificates[name='cacerts']/certificate[name='cacert']" --format json | grep "\"cert\":" | awk '{print $2}' | sed "s/\"//g" >> /tmp/ca.pem
    echo -----END CERTIFICATE----- >> /tmp/ca.pem
    # the server certificate was issued for localhost
    ncat -k -l localhost 6513 --sh-exec "ncat ${NETOPEER2_SERVER_HOSTNAME} 6513" &
    netopeer2-cli <<END
    cert add /tmp/ca.pem
    connect --tls --host localhost --port "${NETOPEER2_SERVER_PORT}" --cert "${ctk_loadkey_token_cert_path}" --key "${TOKEN_KEY_URI}"
END
fi

sleep infinity
