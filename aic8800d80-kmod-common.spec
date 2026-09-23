%global commit 27af5add83088af64b013ec99db1ddf824112e6e
%global commitdate 20260917
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global modname aic8800d80

Name:           %{modname}-kmod-common
Version:        1.0.0.git%{commitdate}.%{shortcommit}
Release:        1%{?dist}
Summary:        Firmware and configuration for AIC8800 USB adapters
License:        GPL-2.0-only
URL:            https://github.com/shenmintao/aic8800d80
Source0:        %{url}/archive/%{commit}/%{modname}-%{commit}.tar.gz
BuildArch:      noarch

# akmod-aic8800d80 provides this virtual package. Keep both packages installed
# so firmware/configuration and automatically rebuilt modules stay in sync.
Requires:       %{modname}-kmod >= %{version}
Requires:       usb_modeswitch
Requires:       /usr/bin/eject

%description
Firmware, udev mode-switch rules, and usb_modeswitch configuration used by the
AIC8800 kernel modules. Bluetooth transport remains handled by the kernel's
standard btusb module.

%prep
%autosetup -n %{modname}-%{commit}

%build
# Architecture-independent files only.

%check
test -s aic.rules
test -s usb_modeswitch/1111_1111
test -d fw/aic8800D80

%install
install -Dpm0644 aic.rules \
    %{buildroot}/usr/lib/udev/rules.d/90-aic8800-mode-switch.rules

install -Dpm0644 usb_modeswitch/1111_1111 \
    %{buildroot}/etc/usb_modeswitch.d/1111:1111

install -d -m 0755 %{buildroot}/usr/lib/firmware
cp -a fw/aic8800* %{buildroot}/usr/lib/firmware/

%files
%doc README.md
/usr/lib/udev/rules.d/90-aic8800-mode-switch.rules
%config(noreplace) /etc/usb_modeswitch.d/1111:1111
/usr/lib/firmware/aic8800*

%changelog
* Thu Sep 17 2026 Felipe CWB - 1.0.0.git20260917.27af5ad-1
- Initial firmware and configuration package for Bazzite.
