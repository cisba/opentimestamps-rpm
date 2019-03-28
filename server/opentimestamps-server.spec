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
#Source3:	README.redhat
#Source5:	bitcoin.te
#Source6:	bitcoin.fc
#Source7:	bitcoin.if

BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

BuildRequires:	python36 python36-devel 
BuildRequires:	systemd
#Requires(pre):	shadow-utils
Requires(post):	systemd
Requires(preun):	systemd
Requires(postun):	systemd
Requires(post):	/usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires(postun):	/usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles
Requires:	selinux-policy
Requires:	policycoreutils-python
Requires:   bitcoin-server 

%description
This package provides the otsd daemon, a calendar server which provides aggregation, Bitcoin timestamping, and remote calendar services for OpenTimestamps clients. You do not need to run a server to use the OpenTimestamps protocol - public servers exist that are free to use. That said, running a server locally can be useful for developers of OpenTimestamps protocol clients, particularly with a local Bitcoin node running in regtest mode.

%prep
%setup -q -n %{name}-%{name}-v%{version}%{?prerelease}

# Install README files
#cp -p %{SOURCE8} %{SOURCE9} %{SOURCE10} .

# Prep SELinux policy
#mkdir SELinux
#cp -p %{SOURCE5} %{SOURCE6} %{SOURCE7} SELinux

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

# Build SELinux policy
#pushd SELinux
#for selinuxvariant in %{selinux_variants}
#do
#  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile
#  mv bitcoin.pp bitcoin.pp.${selinuxvariant}
#  make NAME=${selinuxvariant} -f %{_datadir}/selinux/devel/Makefile clean
#done
#popd

#%check
# Run all the tests

%install
rm -rf %{buildroot}

# executables directory made by pyinstaller
install -d %{buildroot}%{_prefix}/lib/%{name}-%{version}
cp -a dist/otsd %{buildroot}%{_prefix}/lib/%{name}-%{version}
cp -a dist/otsd-backup %{buildroot}%{_prefix}/lib/%{name}-%{version}

# doc stuff
#install -d -m755 %{buildroot}%{_docdir}/%{name}-%{version}/contrib
#install -m644 -p LICENSE README.md release-notes.md %{buildroot}%{_docdir}/%{name}-%{version}
#install -m644 -p doc/merkle-mountain-range.md %{buildroot}%{_docdir}/%{name}-%{version}
#install -m644 -p contrib/nginx/a.pool.opentimestamps.org %{buildroot}%{_docdir}/%{name}-%{version}/contrib/nginx.example
cp -a contrib/nginx/a.pool.opentimestamps.org contrib/nginx.example

# systemd service and cocnfig files
sed -i 's/\/usr\/local\/bin\/bitcoind-ready.sh/\/usr\/sbin\/bitcoind-ready.sh/g' contrib/systemd/otsd.service
install -d %{buildroot}%{_prefix}/sbin
install -m750 -p contrib/systemd/bitcoind-ready.sh %{buildroot}%{_prefix}/sbin
install -d -m755 -p %{buildroot}%{_unitdir}
install -m644 -p %{SOURCE1} %{buildroot}%{_unitdir}/otsd.service
install -d -m755 -p %{buildroot}%{_sysconfdir}/sysconfig
install -m644 -p %{SOURCE2} %{buildroot}%{_sysconfdir}/sysconfig/otsd

# calendar dir
install -d -m755 %{buildroot}%{_localstatedir}/lib/otsd/calendar

# TBD: man pages
#install -D -m644 -p doc/man/bitcoin-qt.1 %{buildroot}%{_mandir}/man1/bitcoin-qt.1
#gzip %{buildroot}%{_mandir}/man1/bitcoin-qt.1

# Install SELinux policy
#for selinuxvariant in %{selinux_variants}
#do
#	install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
#	install -p -m 644 SELinux/bitcoin.pp.${selinuxvariant} \
#		%{buildroot}%{_datadir}/selinux/${selinuxvariant}/bitcoin.pp
#done

%clean
rm -rf %{buildroot}

%pre 
#getent group bitcoin >/dev/null || groupadd -r bitcoin
#getent passwd bitcoin >/dev/null ||
#	useradd -r -g bitcoin -d /var/lib/bitcoin -s /sbin/nologin \
#	-c "Bitcoin wallet server" bitcoin
#exit 0

%post 

# links to executables
ln -s -t /usr/sbin/otsd %{_prefix}/lib/%{name}-%{version}/otsd/otsd
ln -s -t /usr/sbin/otsd-backup %{_prefix}/lib/%{name}-%{version}/otsd/otsd-backup

# generate random hmac-key
dd if=/dev/random of=%{_localstatedir}/lib/otsd/calendar/hmac-key bs=32 count=1

# setup systemd service 
%systemd_post otsd.service

#for selinuxvariant in %{selinux_variants}
#do
#	/usr/sbin/semodule -s ${selinuxvariant} -i \
#		%{_datadir}/selinux/${selinuxvariant}/bitcoin.pp \
#		&> /dev/null || :
#done
# FIXME This is less than ideal, but until dwalsh gives me a better way...
#/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 8332
#/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 8333
#/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 18332
#/usr/sbin/semanage port -a -t bitcoin_port_t -p tcp 18333
#/sbin/fixfiles -R bitcoin-server restore &> /dev/null || :
#/sbin/restorecon -R %{_localstatedir}/lib/bitcoin || :

%posttrans 
/usr/bin/systemd-tmpfiles --create

%preun 
%systemd_preun bitcoin.service


%postun 
%systemd_postun bitcoin.service
#if [ $1 -eq 0 ] ; then
	# FIXME This is less than ideal, but until dwalsh gives me a better way...
#	/usr/sbin/semanage port -d -p tcp 8332
#	/usr/sbin/semanage port -d -p tcp 8333
#	/usr/sbin/semanage port -d -p tcp 18332
#	/usr/sbin/semanage port -d -p tcp 18333
#	for selinuxvariant in %{selinux_variants}
#	do
#		/usr/sbin/semodule -s ${selinuxvariant} -r bitcoin \
#		&> /dev/null || :
#	done
#	/sbin/fixfiles -R bitcoin-server restore &> /dev/null || :
#	[ -d %{_localstatedir}/lib/bitcoin ] && \
#		/sbin/restorecon -R %{_localstatedir}/lib/bitcoin \
#		&> /dev/null || :
#fi


%files 
%defattr(-,root,root,-)
%dir %attr(750,bitcoin,bitcoin) %{_localstatedir}/lib/otsd
%config(noreplace) %attr(600,root,root) %{_sysconfdir}/sysconfig/otsd
%{_prefix}/lib/%{name}-%{version}
%{_unitdir}/otsd.service
%license LICENSE
%doc doc/merkle-mountain-range.md README.md release-notes.md contrib/nginx.example
%attr(750,bitcoin,bitcoin) %{_sbindir}/bitcoind-ready.sh
#%{_mandir}/man1/bitcoind.1*
#%doc SELinux/*
#%{_datadir}/selinux/*/bitcoin.pp


%changelog
* Thu Mar 28 2019 Emanuele Cisbani <emanuele.cisbani@gmail.com> 0.3.0-1
- First release

