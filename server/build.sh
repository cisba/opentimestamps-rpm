#!/usr/bin/env bash

cp -a otsd.service otsd.sysconfig bitcoind-ready.sh ${HOME}/rpmbuild/SOURCES
cp -a opentimestamps-server.spec ${HOME}/rpmbuild/SPECS
rpmbuild --undefine=_disable_source_fetch -bb opentimestamps-server.spec


