FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends suricata \
    && rm -rf /var/lib/apt/lists/*

COPY rules/local.rules /etc/suricata/rules/local.rules

CMD ["suricata", "-i", "eth0", "-c", "/etc/suricata/suricata.yaml", "-S", "/etc/suricata/rules/local.rules", "-l", "/var/log/suricata"]
