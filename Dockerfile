frOM  phusion/baseimage:0.9.18

CMD ["/sbin/my_init"]

ARG DEB_URL

RUN curl -sL https://jenkins-ci.org/debian/jenkins-ci.org.key | apt-key add -

RUN curl -sl 'http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xDF7D54CBE56151BF' | \
     awk '/-----BEGIN PGP PUBLIC KEY BLOCK-----/{flag=1}/-----END PGP PUBLIC KEY BLOCK-----/{print;flag=0}flag' | \
     apt-key add -

RUN echo "deb http://repos.mesosphere.io/ubuntu trusty main" > /etc/apt/sources.list.d/mesosphere.list

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive \
    apt-get upgrade -y \
        -o Dpkg::Options::="--force-confold" && \
  apt-get install -y \
    asciidoc \
    build-essential \
    bzr \
    cvs \
    cvsps \
    daemon \
    docbook-xsl \
    dpkg-dev \
    fakeroot \
    gettext \
    git \
    groovy \
    libcurl4-nss-dev \
    libdbd-sqlite3-perl \
    libexpat1-dev \
    libhttp-date-perl  \
    libio-pty-perl \
    libpcre3-dev \
    libsvn-perl \
    libyaml-dev \
    libyaml-perl \
    mesos \
    openjdk-7-jre \
    python-bzrlib \
    python-dev \
    python-pip \
    python-virtualenv \
    subversion \
    tcl \
    unzip \
    xmlto

RUN curl -sL "$DEB_URL" \
    > /tmp/jenkins.deb && \
    dpkg -i /tmp/jenkins.deb && \
    rm -f /tmp/jenkins.deb && \
    rm -rf /var/lib/jenkins

RUN mkdir /etc/service/bootstrap && \
    echo "#!/bin/bash" >  /etc/service/bootstrap/run && \
    echo "/bin/rm -rf /var/lib/jenkins/plugins/*" >>  /etc/service/bootstrap/run && \
    echo "/bin/tar -C / -xvzf /config/config.tar.gz " >> /etc/service/bootstrap/run && \
    echo "/bin/chmod +x /etc/service/*/run" >> /etc/service/bootstrap/run && \
    echo "while true; do sleep 6000; done" >> /etc/service/bootstrap/run && \
    chmod +x /etc/service/*/run

RUN apt-get clean && \
	rm -rf /var/lib/apt/lists/* \
	/tmp/* \
	/var/tmp/* \
	/var/cache/apt/archives/* \
	/etc/apt/apt.conf \
    /etc/apt/conf.d/18proxy

VOLUME /config
VOLUME /var/lib/jenkins
