#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v podman >/dev/null 2>&1; then
    echo "error: podman is required (it is included with Bazzite)." >&2
    exit 1
fi

fedora_version="${FEDORA_VERSION:-}"
if [[ -z "$fedora_version" ]] && command -v rpm >/dev/null 2>&1; then
    fedora_version="$(rpm -E '%fedora' 2>/dev/null || true)"
fi
if [[ ! "$fedora_version" =~ ^[0-9]+$ ]]; then
    echo "error: could not detect Bazzite's Fedora version." >&2
    echo "Run this as, for example: FEDORA_VERSION=42 ./build.sh" >&2
    exit 1
fi

image="${BUILD_IMAGE:-registry.fedoraproject.org/fedora:${fedora_version}}"
result_dir="${project_dir}/results/fedora-${fedora_version}"

rm -rf "${project_dir}/rpmbuild" "$result_dir"
mkdir -p "${project_dir}/rpmbuild" "$result_dir"

printf 'Building with %s for Fedora %s\n' "$image" "$fedora_version"

podman run --rm \
    --security-opt label=disable \
    -v "${project_dir}:/work" \
    -w /work \
    "$image" \
    bash -euo pipefail -c '
        dnf -y -q install \
            rpm-build rpmdevtools kmodtool \
            gcc clang llvm lld make elfutils-libelf-devel

        topdir=/work/rpmbuild
        mkdir -p "$topdir"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}
        cp /work/aic8800d80-kmod.spec /work/aic8800d80-kmod-common.spec \
            "$topdir/SPECS/"

        spectool --get-files --sources --directory "$topdir/SOURCES" \
            /work/aic8800d80-kmod.spec

        rpmbuild --define "_topdir $topdir" -ba \
            "$topdir/SPECS/aic8800d80-kmod-common.spec"
        rpmbuild --define "_topdir $topdir" -ba \
            "$topdir/SPECS/aic8800d80-kmod.spec"
    '

find "${project_dir}/rpmbuild/RPMS" -type f \
    \( -name 'akmod-aic8800d80-*.rpm' -o -name 'aic8800d80-kmod-common-*.rpm' \) \
    -exec cp -v {} "$result_dir/" \;

printf '\nInstallable packages ready in %s:\n' "$result_dir"
find "$result_dir" -maxdepth 1 -type f -name '*.rpm' -printf '  %f\n' | sort
