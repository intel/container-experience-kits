FROM opnfv/barometer-collectd:stable

LABEL purpose="SDLE Compliance"

RUN dnf update -y && dnf upgrade -y && dnf autoremove -y

ENTRYPOINT ["/run_collectd.sh"]
