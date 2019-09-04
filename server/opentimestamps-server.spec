%define _hardened_build 1
%global selinux_variants mls strict targeted

# avoid empty debug rpm (TBD: add debug tar)
%define debug_package %{nil}

Name:		opentimestamps-server
Version:	0.3.0
Release:	3%{?prerelease}%{?dist}
Summary:	Calendar server for Bitcoin timestamping

Group:		Applications/System
License:	LGPLv3
URL:		http://opentimestamps.org/
Source0:	https://github.com/opentimestamps/opentimestamps-server/archive/opentimestamps-server-v%{version}%{?prerelease}.tar.gz
Source1:	otsd.service
Source2:	otsd.sysconfig
Source3:        bitcoind-ready.sh
Patch0:         p0-working-hour-9141e3ab.patch
Patch1:         p1-workshit_done-9616245e.patch
Patch2:         p2-estimatesmartfee-14f181e9.patch
Patch3:         p3-debug-file-backup-count-3f89d066.patch

BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	python36 python36-devel 
BuildRequires:	systemd
Requires(post):	systemd
Requires(preun):	systemd
Requires(postun):	systemd
Requires:   bitcoin-server 

%description
This package provides the otsd daemon, a calendar server which provides aggregation, Bitcoin timestamping, and remote calendar services for OpenTimestamps clients. You do not need to run a server to use the OpenTimestamps protocol - public servers exist that are free to use. That said, running a server locally can be useful for developers of OpenTimestamps protocol clients, particularly with a local Bitcoin node running in regtest mode.

%prep
%setup -q -n %{name}-%{name}-v%{version}%{?prerelease}

# Fake configure to skip build process
echo "exit 0" > ./configure
chmod +x ./configure

%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1

%build

# executables directory made by pyinstaller
python3.6 -m venv venv
source venv/bin/activate
pip3 install --upgrade pip
pip3 install safety
pip3 install -r requirements.txt 
pip3 install pyinstaller
safety check
pyinstaller otsd
pyinstaller otsd-backup.py
deactivate

#%check
# Run all the tests

%install
rm -rf %{buildroot}

# install exec
install -d %{buildroot}%{_prefix}/lib/%{name}-%{version}
cp -a dist/otsd %{buildroot}%{_prefix}/lib/%{name}-%{version}
cp -a dist/otsd-backup %{buildroot}%{_prefix}/lib/%{name}-%{version}

# install contrib
cp -a contrib/nginx/a.pool.opentimestamps.org contrib/nginx.example

# systemd service and cocnfig files
install -d -m755 -p %{buildroot}%{_prefix}/sbin
install -m750 -p %{SOURCE3} %{buildroot}%{_prefix}/sbin/bitcoind-ready.sh
install -d -m755 -p %{buildroot}%{_unitdir}
install -m644 -p %{SOURCE1} %{buildroot}%{_unitdir}/otsd.service
install -d -m755 -p %{buildroot}%{_sysconfdir}/sysconfig
install -m644 -p %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/otsd

# calendar dir
install -d -m755 -p %{buildroot}%{_localstatedir}/lib/otsd/calendar

%clean
rm -rf %{buildroot}

%pre 

%post 

# generate random hmac-key
[ -f %{_localstatedir}/lib/otsd/calendar/hmac-key ] || dd if=/dev/random of=%{_localstatedir}/lib/otsd/calendar/hmac-key bs=32 count=1 > /dev/null 2>&1

# links to executables
[ -e /usr/sbin/otsd ] || ln -s -t /usr/sbin %{_prefix}/lib/%{name}-%{version}/otsd/otsd
[ -e /usr/sbin/otsd-backup ] || ln -s -t /usr/sbin %{_prefix}/lib/%{name}-%{version}/otsd-backup/otsd-backup
# workaround to missing options for calendar server
[ -e /var/lib/bitcoin/testnet ] || ln -s /var/lib/bitcoin/testnet3/ /var/lib/bitcoin/testnet
[ -e /var/lib/bitcoin/.otsd ] || ln -s /var/lib/otsd/ /var/lib/bitcoin/.otsd

# setup systemd service 
%systemd_post otsd.service

%posttrans 
/usr/bin/systemd-tmpfiles --create

%preun 
%systemd_preun otsd.service

%postun 
%systemd_postun_with_restart otsd.service

# remove links only if uninstall, not if upgrade 
if [ $1 -eq 0 ] ; then # 0 := remove/uninstall
    [ -h /usr/sbin/otsd ] && rm -f /usr/sbin/otsd
    [ -h /usr/sbin/otsd-backup ] && rm -f /usr/sbin/otsd-backup
    [ -h /var/lib/bitcoin/testnet ] && rm -f /var/lib/bitcoin/testnet
    [ -h /var/lib/bitcoin/.otsd ] && rm -f /var/lib/bitcoin/.otsd
fi

%files 
%defattr(-,root,root,-)
%dir %{_localstatedir}/lib/otsd
%attr(750,bitcoin,bitcoin) %{_localstatedir}/lib/otsd
%attr(750,bitcoin,bitcoin) %{_localstatedir}/lib/otsd/calendar
%config(noreplace) %attr(644,root,root) %{_sysconfdir}/sysconfig/otsd
%{_prefix}/lib/%{name}-%{version}
%{_unitdir}/otsd.service
%license LICENSE
%doc doc/merkle-mountain-range.md README.md release-notes.md contrib/nginx.example
%attr(750,bitcoin,bitcoin) %{_sbindir}/bitcoind-ready.sh

%changelog
* Tue Sep  3 2019 Emanuele Cisbani <emanuele.cisbani@gmail.com> 0.3.0-3
- workshit_done flag patch
- estimatesmartfee patch
- debug file rotation backup-count param patch
- fixed stop before uninstall and restart after upgrade
* Tue Aug  6 2019 Emanuele Cisbani <emanuele.cisbani@gmail.com> 0.3.0-2
- working hour patch
- fixed links deletion during upgrade
* Thu Mar 28 2019 Emanuele Cisbani <emanuele.cisbani@gmail.com> 0.3.0-1
- First release
