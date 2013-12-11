%define logmsg logger -t %{name}/rpm
%if %{defined suse_version}
%define apacheuser wwwrun
%define apachegroup www
%define apachedir apache2
%else
%define apacheuser apache
%define apachegroup apache
%define apachedir httpd
%endif

Summary: Open Source Host, Service And Network Monitoring Program
Name: naemon
Version: 0.0.1
Release: 1%{?dist}
License: GPLv2
Group: Applications/System
URL: http://www.naemon.org/
Packager: Sven Nierlein <sven.nierlein@consol.de>
Vendor: Naemon Core Development Team
Source0: http://www.naemon.org/download/naemon/naemon-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}
BuildRequires: gd-devel > 1.8
BuildRequires: zlib-devel
BuildRequires: libpng-devel
BuildRequires: libjpeg-devel
BuildRequires: mysql-devel
BuildRequires: doxygen
BuildRequires: gperf
BuildRequires: perl
BuildRequires: logrotate
BuildRequires: gd
BuildRequires: autoconf
BuildRequires: automake
BuildRequires: libtool
Requires(pre): shadow-utils
Requires: %{name}-core       = %{version}-%{release}
Requires: %{name}-livestatus = %{version}-%{release}
Requires: %{name}-thruk      = %{version}-%{release}
# https://fedoraproject.org/wiki/Packaging:DistTag
# http://stackoverflow.com/questions/5135502/rpmbuild-dist-not-defined-on-centos-5-5

%description
Naemon is an application, system and network monitoring application.
It can escalate problems by email, pager or any other medium. It is
also useful for incident or SLA reporting. It is originally a fork
of Nagios, but with extended functionality, stability and performance.

It is written in C and is designed as a background process,
intermittently running checks on various services that you specify.

The actual service checks are performed by separate "plugin" programs
which return the status of the checks to Naemon. The plugins are
compatible with Nagios, and can be found in the nagios-plugins package.

Naemon ships the Thruk gui with extended reporting and dashboard features.

# disable binary striping
%global __os_install_post %{nil}



%package core
Summary:   Naemon Monitoring Core
Group:     Applications/System

%description core
contains the %{name} core


%package livestatus
Summary:        Naemon Livestatus Eventbroker Module
Group:          Applications/System
Requires:       %{name}-core = %{version}-%{release}
Requires(post): %{name}-core = %{version}-%{release}

%description livestatus
contains the %{name} livestatus eventbroker module


%package thruk-libs
Summary:     Perl Librarys For Naemons Thruk Gui
Group:       Applications/System
AutoReqProv: no
Requires:    %{name}-thruk = %{version}-%{release}

%description thruk-libs
This package contains the library files for the thruk gui


%package thruk
Summary:     Thruk Gui For Naemon
Group:       Applications/System
Requires:    %{name}-thruk-libs = %{version}-%{release}
Requires(preun): %{name}-thruk-libs = %{version}-%{release}
Requires(post): %{name}-thruk-libs = %{version}-%{release}
Requires:    perl logrotate gd wget
Conflicts:   thruk
AutoReqProv: no
%if %{defined suse_version}
Requires:    apache2 apache2-mod_fcgid cron
%else
Requires:    httpd mod_fcgid
%endif

%description thruk
This package contains the thruk gui for %{name}


#%package devel
#Summary: Development Files For Naemon
#Group: Development/Libraries
#Requires: %{name} = %{version}-%{release}
#
#%description devel
#This package contains the header files, static libraries and development
#documentation for %{name}. If you are a NEB-module author or wish to
#write addons for Naemon using Naemons own APIs, you should install
#this package.


%prep
%setup

%build
%configure \
    --bindir="%{_bindir}" \
    --datadir="%{_datadir}/naemon" \
    --libexecdir="%{_libdir}/naemon/plugins" \
    --libdir="%{_libdir}/naemon" \
    --localstatedir="%{_localstatedir}/lib/naemon" \
    --with-temp-dir="%{_localstatedir}/cache/naemon" \
    --with-checkresult-dir="%{_localstatedir}/cache/naemon/checkresults" \
    --sysconfdir="%{_sysconfdir}/naemon" \
    --mandir="%{_mandir}" \
    --enable-event-broker \
    --with-init-dir="%{_initrddir}" \
    --with-logrotate-dir="%{_sysconfdir}/logrotate.d" \
    --with-naemon-user="naemon" \
    --with-naemon-group="naemon" \
    --with-lockfile="%{_localstatedir}/cache/naemon/naemon.pid" \
    --with-thruk-user="%{apacheuser}" \
    --with-thruk-group="%{apachegroup}" \
    --with-thruk-libs="%{_libdir}/naemon/perl5" \
    --with-thruk-temp-dir="%{_localstatedir}/cache/naemon/thruk" \
    --with-thruk-var-dir="%{_localstatedir}/lib/naemon/thruk" \
    --with-httpd-conf="%{_sysconfdir}/%{apachedir}/conf.d" \
    --with-htmlurl="/naemon"
%{__make} %{?_smp_mflags} all

%install
%{__rm} -rf %{buildroot}
%{__make} install \
    DESTDIR="%{buildroot}" \
    INSTALL_OPTS="" \
    COMMAND_OPTS="" \
    INIT_OPTS=""
# because we globally disabled binary striping, we have to do this manually for some files
strip %{buildroot}%{_bindir}/naemon
strip %{buildroot}%{_bindir}/unixcat
mv %{buildroot}%{_sysconfdir}/logrotate.d/thruk %{buildroot}%{_sysconfdir}/logrotate.d/naemon-thruk

%clean
%{__rm} -rf %{buildroot}



%pre core
if ! /usr/bin/id naemon &>/dev/null; then
    /usr/sbin/useradd -r -d %{_localstatedir}/lib/naemon -s /bin/sh -c "naemon" naemon || \
        %logmsg "Unexpected error adding user \"naemon\". Aborting installation."
fi
if ! /usr/bin/getent group naemon &>/dev/null; then
    /usr/sbin/groupadd naemon &>/dev/null || \
        %logmsg "Unexpected error adding group \"naemon\". Aborting installation."
fi

%post core
/sbin/chkconfig --add naemon

if /usr/bin/id %{apacheuser} &>/dev/null; then
    if ! /usr/bin/id -Gn %{apacheuser} 2>/dev/null | grep -q naemon ; then
%if %{defined suse_version}
        /usr/sbin/groupmod -A %{apacheuser} naemon >/dev/null
%else
        /usr/sbin/usermod -a -G naemon %{apacheuser} >/dev/null
%endif
    fi
else
    %logmsg "User \"%{apacheuser}\" does not exist and is not added to group \"naemon\". Sending commands to naemon from the CGIs is not possible."
fi

%preun core
case "$*" in
  0)
    # POSTUN
    chkconfig --del naemon >/dev/null 2>&1
    %{insserv_cleanup}
    ;;
  1)
    # POSTUPDATE
    ;;
  *) echo case "$*" not handled in postun
esac
exit 0


%post livestatus
if [ -e /etc/naemon/naemon.cfg ]; then
  sed -i /etc/naemon/naemon.cfg -e 's~#\(broker_module=/usr/lib[0-9]*/naemon/livestatus.o.*\)~\1~'
fi
exit 0

%postun livestatus
if [ -e /etc/naemon/naemon.cfg ]; then
  sed -i /etc/naemon/naemon.cfg -e 's~\(broker_module=/usr/lib[0-9]*/naemon/livestatus.o.*\)~#\1~'
fi
exit 0


%pre thruk
# save themes, plugins so we don't reenable them on every update
rm -rf /tmp/thruk_update
if [ -d /etc/naemon/themes/themes-enabled/. ]; then
  mkdir -p /tmp/thruk_update/themes
  cp -rp /etc/naemon/themes/themes-enabled/* /tmp/thruk_update/themes/
fi
if [ -d /etc/naemon/plugins/plugins-enabled/. ]; then
  mkdir -p /tmp/thruk_update/plugins
  cp -rp /etc/naemon/plugins/plugins-enabled/* /tmp/thruk_update/plugins/
fi
exit 0

%post thruk
chkconfig --add thruk
mkdir -p /var/lib/naemon/thruk /var/cache/naemon/thruk /etc/naemon/bp /var/log/thruk
touch /var/log/thruk/thruk.log
chown -R %{apacheuser}:%{apachegroup} /var/cache/naemon/thruk /var/log/thruk/thruk.log /etc/naemon/plugins/plugins-enabled /etc/naemon/thruk_local.conf /etc/naemon/bp /var/lib/naemon/thruk
/usr/bin/crontab -l -u %{apacheuser} 2>/dev/null | /usr/bin/crontab -u %{apacheuser} -
%if %{defined suse_version}
a2enmod alias
a2enmod fcgid
a2enmod auth_basic
a2enmod rewrite
/etc/init.d/apache2 restart || /etc/init.d/apache2 start
%else
/etc/init.d/httpd restart || /etc/init.d/httpd start
if [ "$(getenforce 2>/dev/null)" = "Enforcing" ]; then
  echo "******************************************";
  echo "Thruk will not work when SELinux is enabled";
  echo "SELinux: "$(getenforce);
  echo "******************************************";
fi
%endif
if [ -d %{_libdir}/naemon/perl5 ]; then
  /usr/bin/thruk -a clearcache,installcron --local > /dev/null
fi
if /usr/bin/id %{apacheuser} &>/dev/null; then
    if ! /usr/bin/id -Gn %{apacheuser} 2>/dev/null | grep -q naemon ; then
%if %{defined suse_version}
        /usr/sbin/groupmod -A %{apacheuser} naemon >/dev/null
%else
        /usr/sbin/usermod -a -G naemon %{apacheuser} >/dev/null
%endif
    fi
else
    %logmsg "User \"%{apacheuser}\" does not exist and is not added to group \"naemon\". Sending commands to naemon from the CGIs is not possible."
fi


echo "Thruk has been configured for http://$(hostname)/naemon/. User and password is 'thrukadmin'."
exit 0

%posttrans thruk
# restore themes and plugins
if [ -d /tmp/thruk_update/themes/. ]; then
  rm -f /etc/naemon/themes/themes-enabled/*
  cp -rp /tmp/thruk_update/themes/* /etc/naemon/themes/themes-enabled/
fi
if [ -d /tmp/thruk_update/plugins/. ]; then
  rm -f /etc/naemon/plugins/plugins-enabled/*
  cp -rp /tmp/thruk_update/plugins/* /etc/naemon/plugins/plugins-enabled/
fi
echo "plugins enabled:" $(ls /etc/naemon/plugins/plugins-enabled/)
rm -rf /tmp/thruk_update

%preun thruk
if [ $1 = 0 ]; then
  # last version will be deinstalled
  if [ -d %{_libdir}/naemon/perl5 ]; then
    /usr/bin/thruk -a uninstallcron --local
  fi
fi
/etc/init.d/thruk stop
chkconfig --del thruk >/dev/null 2>&1
rmdir /etc/naemon/bp 2>/dev/null
rmdir /etc/naemon 2>/dev/null
exit 0

%postun thruk
case "$*" in
  0)
    # POSTUN
    rm -rf /var/cache/naemon/thruk
    rm -rf %{_datadir}/naemon/root/thruk/plugins
    %{insserv_cleanup}
    ;;
  1)
    # POSTUPDATE
    rm -rf /var/cache/naemon/thruk/*
    mkdir -p /var/cache/naemon/thruk/reports
    chown -R %{apacheuser}:%{apachegroup} /var/cache/naemon/thruk
    ;;
  *) echo case "$*" not handled in postun
esac
exit 0


%preun thruk-libs
if [ $1 = 0 ]; then
  # last version will be deinstalled
  if [ -e /usr/bin/thruk ]; then
    /usr/bin/thruk -a uninstallcron --local
  fi
fi
exit 0

%post thruk-libs
if [ -e /usr/bin/thruk ]; then
  /usr/bin/thruk -a clearcache,installcron --local > /dev/null
fi
exit 0


%files

%files core
%attr(755,root,root) %{_bindir}/naemon
%attr(0755,root,root) %{_initrddir}/naemon
%attr(0755,root,root) %dir %{_sysconfdir}/naemon/
%attr(0755,root,root) %dir %{_sysconfdir}/naemon/conf.d
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/naemon/naemon.cfg
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/naemon/resource.cfg
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/naemon/conf.d/*.cfg
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/naemon/conf.d/templates/*.cfg
%attr(0755,naemon,naemon) %dir %{_localstatedir}/cache/naemon/checkresults
%attr(0755,naemon,naemon) %dir %{_localstatedir}/cache/naemon
%attr(0755,naemon,naemon) %dir %{_localstatedir}/lib/naemon

#%files devel
#%attr(0755,root,root) %{_includedir}/naemon/

%files livestatus
%attr(0755,root,root) %{_bindir}/unixcat
%attr(0644,root,root) %{_libdir}/naemon/livestatus.o

%files thruk
%attr(0755,root, root) %{_bindir}/thruk
%attr(0755,root, root) %{_bindir}/naglint
%attr(0755,root, root) %{_bindir}/nagexp
%attr(0755,root, root) %{_initrddir}/thruk
%config %{_sysconfdir}/naemon/ssi
%config %{_sysconfdir}/naemon/thruk.conf
%attr(0644,%{apacheuser},%{apachegroup}) %config(noreplace) %{_sysconfdir}/naemon/thruk_local.conf
%attr(0644,%{apacheuser},%{apachegroup}) %config(noreplace) %{_sysconfdir}/naemon/cgi.cfg
%attr(0644,%{apacheuser},%{apachegroup}) %config(noreplace) %{_sysconfdir}/naemon/htpasswd
%attr(0755,%{apacheuser},%{apachegroup}) %dir %{_sysconfdir}/naemon/bp
%attr(0755,%{apacheuser},%{apachegroup}) %dir /var/log/thruk/
%config(noreplace) %{_sysconfdir}/naemon/naglint.conf
%config(noreplace) %{_sysconfdir}/naemon/log4perl.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/naemon-thruk
%config(noreplace) %{_sysconfdir}/%{apachedir}/conf.d/thruk.conf
%config(noreplace) %{_sysconfdir}/naemon/plugins
%config(noreplace) %{_sysconfdir}/naemon/themes
%config(noreplace) %{_sysconfdir}/naemon/menu_local.conf
%attr(0755,root, root) %{_datadir}/naemon/script/thruk_auth
%attr(0755,root, root) %{_datadir}/naemon/script/thruk_fastcgi.pl
%attr(0755,%{apacheuser},%{apachegroup}) %dir %{_localstatedir}/cache/naemon/thruk
%{_datadir}/naemon/root
%{_datadir}/naemon/templates
%{_datadir}/naemon/themes
%{_datadir}/naemon/plugins
%{_datadir}/naemon/lib
%{_datadir}/naemon/Changes
%{_datadir}/naemon/LICENSE
%{_datadir}/naemon/menu.conf
%{_datadir}/naemon/dist.ini
%attr(0755,root,root) %{_datadir}/naemon/fcgid_env.sh
%doc %{_mandir}/man3/nagexp.3
%doc %{_mandir}/man3/naglint.3
%doc %{_mandir}/man3/thruk.3
%doc %{_mandir}/man8/thruk.8

%files thruk-libs
%attr(-,root,root) %{_libdir}/naemon/perl5

%changelog
* Tue Nov 26 2013 Sven Nierlein <sven.nierlein@consol.de> 0.0.1-1
- initial naemon meta package