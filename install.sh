#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v rpm-ostree >/dev/null 2>&1; then
    echo "error: this installer must be run on Bazzite/rpm-ostree." >&2
    exit 1
fi

if command -v mokutil >/dev/null 2>&1 && mokutil --sb-state 2>/dev/null | grep -qi 'enabled'; then
    cat >&2 <<'EOF'
error: Secure Boot is enabled.

Locally built akmods cannot use Universal Blue's private signing key. Installing
unsigned modules would leave this adapter unavailable after reboot. Disable
Secure Boot first, or add a private local-MOK package/signing workflow before
installing these RPMs.
EOF
    exit 1
fi

fedora_version="$(rpm -E '%fedora')"
result_dir="${project_dir}/results/fedora-${fedora_version}"

mapfile -t common_rpms < <(find "$result_dir" -maxdepth 1 -type f \
    -name 'aic8800d80-kmod-common-*.rpm' -print | sort)
mapfile -t akmod_rpms < <(find "$result_dir" -maxdepth 1 -type f \
    -name 'akmod-aic8800d80-*.rpm' -print | sort)

if (( ${#common_rpms[@]} != 1 || ${#akmod_rpms[@]} != 1 )); then
    echo "error: expected exactly one common RPM and one akmod RPM in:" >&2
    echo "  $result_dir" >&2
    echo "Run ./build.sh first and remove obsolete RPMs if necessary." >&2
    exit 1
fi

printf 'Staging these packages in a new Bazzite deployment:\n  %s\n  %s\n' \
    "${common_rpms[0]}" "${akmod_rpms[0]}"

# The upstream kernel-specific Bazzite RPM owns the same firmware and udev
# files. Remove its layering request before replacing it with the akmod. The
# following install operation is chained onto the same pending deployment.
if rpm -q aic8800d80 >/dev/null 2>&1; then
    echo 'Removing the old kernel-specific aic8800d80 RPM from the pending deployment.'
    sudo rpm-ostree uninstall aic8800d80
fi

sudo rpm-ostree install "${common_rpms[0]}" "${akmod_rpms[0]}"

cat <<'EOF'

Installation was staged successfully. Reboot to enter the new deployment:

  systemctl reboot

The akmod package will be retained and rebuilt automatically when later
Bazzite updates introduce a new kernel.
EOF
