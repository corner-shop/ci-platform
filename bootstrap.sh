#!/bin/bash

echo "starting... "
cd /
rm -f config.yml ; rm -rf target
curl $TEMPURL > config.yml && \
    python -u /render.py && \
    tar -C /target -cvzf /config/config.tar.gz . && \
    rm -rf /target && \
    rm -f config.yml && \
    echo "finished"

/bin/rm -rf /var/lib/jenkins/plugins/*
/bin/tar -C / -xvzf /config/config.tar.gz
/bin/chmod +x /etc/service/*/run

exec /sbin/my_init

