#!/usr/bin/env bash

# check or setup rpmbuild toos and stuff
sudo yum install -y rpmdevtools rpmlint selinux-policy-devel
[ ! -f ~/.rpmmacros ] && rpmdev-setuptree
TOPDIR=$(rpm --eval "%{_topdir}")
[ ! -d ${TOPDIR} ] && rpmdev-setuptree

# setup files
cp -a otsd.service otsd.sysconfig bitcoind-ready.sh ${HOME}/rpmbuild/SOURCES
cp -a *.patch ${HOME}/rpmbuild/SOURCES
cp -a opentimestamps-server.spec ${HOME}/rpmbuild/SPECS

# build
rpmbuild --undefine=_disable_source_fetch -bb opentimestamps-server.spec


