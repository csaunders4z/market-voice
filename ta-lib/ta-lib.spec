Summary: Technical Analysis Library
Name: ta-lib
Version: 0.4.0
Release: 1
License: BSD
Group: Development/Libraries

%description
TA-Lib provides common functions for the technical analysis of stock/future/commodity market data.

%build
./autogen.sh
CFLAGS="-g0 -O2 -pipe" ./configure --prefix=/usr
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install

%post -p /sbin/ldconfig
%postun -p /sbin/ldconfig

%files
%defattr(-,root,root)
/usr
