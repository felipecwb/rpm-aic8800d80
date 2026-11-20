%global commit 1a2ce4e38e678a0c0d7f6071be415ab74f488240
%global commitdate 20261120
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global modname aic8800d80

# Build an akmod source package. At install/update time akmods rebuilds the
# modules for the kernel in the new rpm-ostree deployment.
%global buildforkernels akmod
%global debug_package %{nil}

# kmodtool copies this list to the generated akmod package as runtime
# requirements, so the rpm-ostree transaction has the complete build toolchain.
%global AkmodsBuildRequires %{_bindir}/kmodtool, gcc, clang, llvm, lld, make, elfutils-libelf-devel

Name:           %{modname}-kmod
Version:        1.0.0.git%{commitdate}.%{shortcommit}
Release:        1%{?dist}
Summary:        Kernel modules for AIC8800 USB Wi-Fi and Bluetooth adapters
License:        GPL-2.0-only
URL:            https://github.com/shenmintao/aic8800d80
Source0:        %{url}/archive/%{commit}/%{modname}-%{commit}.tar.gz

BuildRequires:  %{AkmodsBuildRequires}

# Generate akmod-aic8800d80, kmod-aic8800d80, the kernel-specific package
# metadata, and the akmod_install macro.
%{expand:%(kmodtool --target %{_target_cpu} --kmodname %{modname} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Out-of-tree kernel modules for AIC8800 USB Wi-Fi/Bluetooth adapters. The
package builds aic8800_fdrv, aic_load_fw, and the device-scoped
368b:8d81 Bluetooth ACL bulk-TX ZLP companion module.

%prep
%{?kmodtool_check}

# Keep the expanded kmodtool output in build logs for troubleshooting.
kmodtool --target %{_target_cpu} --kmodname %{modname} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null

%autosetup -n %{modname}-%{commit}

for kernel_version in %{?kernel_versions}; do
    cp -a drivers/aic8800 "_kmod_build_${kernel_version%%___*}"
done

%build
for kernel_version in %{?kernel_versions}; do
    make -C "_kmod_build_${kernel_version%%___*}" \
        KVER="${kernel_version%%___*}" \
        KDIR="${kernel_version##*___}"
done

%check
for kernel_version in %{?kernel_versions}; do
    test -s "_kmod_build_${kernel_version%%___*}/aic8800_fdrv/aic8800_fdrv.ko"
    test -s "_kmod_build_${kernel_version%%___*}/aic_load_fw/aic_load_fw.ko"
    test -s "_kmod_build_${kernel_version%%___*}/aic_zlp_quirk/aic_zlp_quirk.ko"
done

%install
for kernel_version in %{?kernel_versions}; do
    destination="%{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}"
    install -d -m 0755 "$destination"

    install -p -m 0755 \
        "_kmod_build_${kernel_version%%___*}/aic8800_fdrv/aic8800_fdrv.ko" \
        "$destination/"
    install -p -m 0755 \
        "_kmod_build_${kernel_version%%___*}/aic_load_fw/aic_load_fw.ko" \
        "$destination/"
    install -p -m 0755 \
        "_kmod_build_${kernel_version%%___*}/aic_zlp_quirk/aic_zlp_quirk.ko" \
        "$destination/"
done

# Embed this spec and its sources in /usr/src/akmods. This is what makes the
# installed package rebuild itself for later kernels.
%{?akmod_install}

%changelog
* Fri Nov 20 2026 Felipe CWB - 1.0.0.git20261120.1a2ce4e-1
- Update to upstream main for Linux 7.3 firmware-open fallback.
