%define nginx_user 		admin
%define nginx_group 		%{nginx_user}
%define nginx_home 		/export/servers/nginx
%define nginx_temp_path 	/dev/shm/nginx_temp
%define nginx_sbin_path         %{nginx_home}/sbin
%define nginx_sbin_file_path 	%{nginx_sbin_path}/nginx
%define nginx_conf_path 	%{nginx_home}/conf
%define nginx_log_path 		%{nginx_home}/logs
%define nginx_var_path 		%{nginx_home}/var
%define nginx_run_path 		%{nginx_home}/run
%define nginx_temp_proxy_path 	%{nginx_temp_path}/proxy
%define nginx_temp_client_path 	%{nginx_temp_path}/client_body
%define nginx_temp_fastcgi_path %{nginx_temp_path}/fastcgi
%define nginx_temp_uwsgi_path 	%{nginx_temp_path}/uwsgi
%define nginx_temp_scgi_path 	%{nginx_temp_path}/scgi
Name:		nginx
Version:	1.7.2.1
Release:	1%{?dist}
Summary:	nginx, small and high performance http and reverse proxy server

Group:		System Environment/Daemons
License:	GPL
URL:		http://nginx.org
Source0:	nginx-1.7.2.tar.gz
Source1:	nginx
Source2:	logrotate.sh
Source3:	nginx.conf
Source4:	pickingplan_taskassign.location.conf
Source5:	lua.tar.gz
Source6:	pcre-8.31.zip
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u} -n)

BuildRequires:	gcc,openssl-devel,pcre-devel,zlib-devel,libtool,gcc-c++
Requires:	pcre,zlib,openssl
Requires:       perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%description
Nginx [engine x] is an HTTP(S) server, HTTP(S) reverse proxy and IMAP/POP3
proxy server written by Igor Sysoev.

%prep
%setup -q

%build
cd %{_builddir}/%{name}-%{version}/bundle/LuaJIT-2.1-20140707
make clean
make -j32
make install
ln -sf luajit-2.1.0-alpha /usr/local/bin/luajit

export DESTDIR=%{buildroot}
cd %{_builddir}/%{name}-%{version}
mkdir -p %{buildroot}%{nginx_conf_path}
./configure --prefix=%{nginx_home} \
            --sbin-path=%{nginx_sbin_file_path} \
	    --conf-path=%{nginx_conf_path}/nginx.conf \
	    --error-log-path=%{nginx_log_path}/error.log \
	    --http-log-path=%{nginx_log_path}/access.log \
	    --pid-path=%{nginx_run_path}/nginx.pid \
	    --lock-path=%{nginx_var_path}/nginx.lock \
	    --http-client-body-temp-path=%{nginx_temp_client_path} \
	    --http-proxy-temp-path=%{nginx_temp_proxy_path} \
	    --http-fastcgi-temp-path=%{nginx_temp_fastcgi_path} \
	    --http-uwsgi-temp-path=%{nginx_temp_uwsgi_path} \
	    --http-scgi-temp-path=%{nginx_temp_scgi_path} \
	    --user=%{nginx_user} \
	    --group=%{nginx_group} \
	    --with-cpu-opt=pentium4F \
	    --without-select_module \
	    --without-poll_module \
	    --with-http_realip_module \
	    --with-http_sub_module \
	    --with-http_gzip_static_module \
	    --without-http_ssi_module \
	    --without-http_userid_module \
	    --without-http_geo_module \
	    --without-http_map_module \
	    --without-mail_pop3_module \
	    --without-mail_imap_module \
	    --without-mail_smtp_module \
	    --with-http_stub_status_module \
	    --with-luajit \
	    --with-http_spdy_module \
	    --with-pcre=/usr/local/src/pcre-8.31
make %{?_smp_mflags}


%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}
mkdir -p %{buildroot}/dev/shm/nginx_temp
mkdir -p %{buildroot}%{nginx_conf_path}/domains
mkdir -p %{buildroot}%{nginx_run_path}
mkdir -p %{buildroot}%{nginx_var_path}
mkdir -p %{buildroot}%{nginx_var_path}/lua

%{__install} -p -D -m 0755 $RPM_SOURCE_DIR/logrotate.sh %{buildroot}%{nginx_sbin_path}
%{__install} -p -D -m 0644 $RPM_SOURCE_DIR/nginx.conf %{buildroot}%{nginx_conf_path}
%{__install} -p -D -m 0644 $RPM_SOURCE_DIR/pickingplan_taskassign.location.conf %{buildroot}%{nginx_conf_path}/domains
%{__install} -p -D -m 0755 $RPM_SOURCE_DIR/nginx %{buildroot}/etc/rc.d/init.d/nginx
%{__tar} zxvf $RPM_SOURCE_DIR/lua.tar.gz -C %{buildroot}%{nginx_var_path}/lua

%clean
rm -rf %{buildroot}

%pre
if [ $1 == 1 ];then
    egrep "^admin" /etc/group >& /dev/null
    if [ $? -ne 0 ];then
        groupadd -g 600 admin
    fi
    egrep "^admin" /etc/passwd >& /dev/null  
    if [ $? -ne 0 ];then
        useradd -u 600 -g 600 admin
    fi
fi

%post
if [ $1 == 1 ];then
    /sbin/chkconfig --add %{name}
    /sbin/chkconfig %{name} on
echo '# Add  #下面主要是内核参数的优化，包括tcp的快速释放和重利用等。   
net.core.somaxconn = 32768
net.core.wmem_default = 8388608
net.core.rmem_default = 8388608
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_synack_retries = 1
net.ipv4.tcp_syn_retries = 0
net.ipv4.tcp_tw_recycle = 1
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_mem = 94500000 915000000 927000000
net.ipv4.tcp_max_orphans = 3276800
net.ipv4.ip_local_port_range = 1024  65535
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_keepalive_time = 100
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_max_tw_buckets = 20000' >> /etc/sysctl.conf
    sysctl -p > /dev/null 2>&1
fi

if [ $1 == 1 ];then
    /sbin/service %{name} restart > /dev/null 2>&1
fi

%preun
if [ $1 == 0 ];then
    /sbin/service %{name} stop > /dev/null 2>&1
    /sbin/chkconfig --del %{name}
fi

%postun
if [ $1 == 0 ];then
    rm -rf %{nginx_home}
    sed -i '/# Add  #下面主要是内核参数的优化/,$d' /etc/sysctl.conf
fi

%files
%defattr(-,root,root,-)
%doc
/export
/dev
/etc
/usr/local


%changelog
* Wed Feb 3 2016 Created by lihui
-RPMBUILD OpenResty
