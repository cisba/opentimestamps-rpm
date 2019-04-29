%define _hardened_build 1
%global selinux_variants mls strict targeted

# avoid empty debug rpm (TBD: add debug tar)
%define debug_package %{nil}

Name:		opentimestamps-server
Version:	0.3.0
Release:	1%{?prerelease}%{?dist}
Summary:	Calendar server for Bitcoin timestamping

Group:		Applications/System
License:	LGPLv3
URL:		http://opentimestamps.org/
Source0:	https://github.com/opentimestamps/opentimestamps-server/archive/opentimestamps-server-v%{version}%{?prerelease}.tar.gz
Source1:	otsd.service
Source2:	otsd.sysconfig
Source3:        bitcoind-ready.sh

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

# links to executables
ln -s -t /usr/sbin %{_prefix}/lib/%{name}-%{version}/otsd/otsd
ln -s -t /usr/sbin %{_prefix}/lib/%{name}-%{version}/otsd-backup/otsd-backup

# generate random hmac-key
[ -f %{_localstatedir}/lib/otsd/calendar/hmac-key ] || dd if=/dev/random of=%{_localstatedir}/lib/otsd/calendar/hmac-key bs=32 count=1 > /dev/null 2>&1

# workaround to missing options for calendar server
ln -s /var/lib/bitcoin/testnet3 /var/lib/bitcoin/testnet
ln -s /var/lib/otsd/ /var/lib/bitcoin/.otsd

# setup systemd service 
%systemd_post otsd.service

%posttrans 
/usr/bin/systemd-tmpfiles --create

%preun 
%systemd_preun ots.service


%postun 
%systemd_postun ots.service

# remove links 
rm -f /usr/sbin/otsd
rm -f /usr/sbin/otsd-backup
rm -f /var/lib/bitcoin/testnet
rm -f /var/lib/bitcoin/.otsd

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
* Thu Mar 28 2019 Emanuele Cisbani <emanuele.cisbani@gmail.com> 0.3.0-1
- First release
