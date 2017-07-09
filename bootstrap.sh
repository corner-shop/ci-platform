#!/bin/bash

echo "starting... "
# disable all services
/bin/chmod -x /etc/service/*/run

# clean up config.yml and old target files
cd /
rm -f config.yml ; rm -rf target

# get a config.yaml from the tempurl service if available
# and generate a new config.tar.gz artifact
curl $TEMPURL > config.yml && \
    python -u /render.py && \
    tar -C /target -cvzf /config/config.tar.gz . && \
    rm -rf /target && \
    rm -f config.yml && \
    echo "finished"

# cleanup any jenkins plugins
/bin/rm -rf /var/lib/jenkins/plugins/*

# and re-apply the latest available config.tar.gz file
/bin/tar -C / -xvzf /config/config.tar.gz

# re-enable all services
/bin/chmod +x /etc/service/*/run

exec /sbin/my_init

