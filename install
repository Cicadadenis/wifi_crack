#!/usr/bin/env bash
# SATANA (satana) installer — dependencies + global `satana` command
# Usage: sudo ./install.sh [--prefix /opt/satana] [--minimal]

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${SATANA_INSTALL_DIR:-/opt/satana}"
BIN_NAME="satana"
BIN_PATH="/usr/local/bin/${BIN_NAME}"
WEB_BIN_NAME="satana-web"
WEB_BIN_PATH="/usr/local/bin/${WEB_BIN_NAME}"
MINIMAL=0

usage() {
	cat <<'EOF'
Usage: sudo ./install.sh [options]

  --prefix PATH   Install directory (default: /opt/satana)
  --minimal       Essential + internal tools only (smaller install)
  -h, --help      Show this help

After install, run from anywhere:
  sudo satana
  satana-web
EOF
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		--prefix)
			[[ $# -ge 2 ]] || { echo "Missing value for --prefix" >&2; exit 1; }
			INSTALL_DIR="$2"
			shift 2
			;;
		--minimal)
			MINIMAL=1
			shift
			;;
		-h|--help)
			usage
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			usage >&2
			exit 1
			;;
	esac
done

if [[ "${EUID}" -ne 0 ]]; then
	echo "Run as root: sudo ./install.sh" >&2
	exit 1
fi

if [[ ! -f "${SCRIPT_DIR}/satana.sh" ]]; then
	echo "satana.sh not found in ${SCRIPT_DIR}" >&2
	exit 1
fi

detect_distro() {
	if [[ -f /etc/os-release ]]; then
		# shellcheck source=/dev/null
		. /etc/os-release
		case "${ID:-}" in
			kali|parrotos|debian|ubuntu|linuxmint|raspbian) echo "apt" ;;
			arch|manjaro|endeavouros|garuda|blackarch) echo "pacman" ;;
			*) echo "unknown" ;;
		esac
		return
	fi
	echo "unknown"
}

strip_utf8_bom() {
	local f
	for f in "${INSTALL_DIR}/satana.sh" \
		"${INSTALL_DIR}/language_strings.sh" \
		"${INSTALL_DIR}/plugins/"*.sh; do
		[[ -f "${f}" ]] || continue
		if head -c 3 "${f}" | grep -q $'^\xef\xbb\xbf'; then
			sed -i '1s/^\xEF\xBB\xBF//' "${f}"
			echo "  Removed UTF-8 BOM: ${f}"
		fi
	done
}

# Install one apt package; skip unavailable names without aborting the rest.
apt_install_one() {
	local pkg="$1"

	if ! apt-cache show "${pkg}" >/dev/null 2>&1; then
		echo "  [warn] Package not available: ${pkg}"
		return 1
	fi

	if apt-get install -y --no-install-recommends "${pkg}" >/dev/null 2>&1; then
		echo "  [ok] ${pkg}"
		return 0
	fi

	echo "  [warn] Failed to install: ${pkg}"
	return 1
}

apt_install_list() {
	local label="$1"
	shift
	local -a pkgs=("$@")
	local pkg

	echo "[*] ${label}"
	for pkg in "${pkgs[@]}"; do
		apt_install_one "${pkg}" || true
	done
}

# Debian / Ubuntu / Kali — package names from plugins/missing_dependencies.sh
apt_install() {
	export DEBIAN_FRONTEND=noninteractive
	apt-get update -qq

	local -a essential=(
		iw gawk aircrack-ng xterm iproute2 pciutils procps
		nftables curl wget openssl ethtool usbutils rfkill
		x11-utils x11-xserver-utils python3-flask python3-flask-socketio
		python3-psutil
	)

	local -a optional=(
		crunch mdk4 hashcat hostapd isc-dhcp-server iptables
		ettercap-text-only lighttpd dsniff reaver bully pixiewps
		bettercap john ccze tmux net-tools wireless-tools
		hashcat-utils hcxtools
	)

	local -a extra=(
		sslstrip beef-xss hostapd-wpe asleap
	)

	echo "[*] Installing essential packages..."
	apt-get install -y --no-install-recommends "${essential[@]}"

	if [[ "${MINIMAL}" -eq 0 ]]; then
		apt_install_list "Installing optional attack / menu packages..." "${optional[@]}"
		apt_install_list "Installing extra packages (Kali-only on some distros)..." "${extra[@]}"
		install_beef_from_source
	fi
}

install_beef_from_source() {
	local beef_script="${SCRIPT_DIR}/scripts/install-beef.sh"

	if [[ ! -x "${beef_script}" ]]; then
		chmod +x "${beef_script}" 2>/dev/null || true
	fi
	if [[ ! -f "${beef_script}" ]]; then
		echo "  [warn] BeEF install script not found: ${beef_script}"
		return 0
	fi

	if [[ -f /opt/beef/beef ]]; then
		echo "  [ok] BeEF already installed at /opt/beef"
		return 0
	fi

	echo "[*] Installing BeEF from source (git + bundle)..."
	if bash "${beef_script}"; then
		echo "  [ok] BeEF installed to /opt/beef"
	else
		echo "  [warn] BeEF source install failed; try: sudo ${beef_script}"
	fi
}

pacman_install_one() {
	local pkg="$1"

	if pacman -Sy --noconfirm --needed "${pkg}" >/dev/null 2>&1; then
		echo "  [ok] ${pkg}"
		return 0
	fi

	echo "  [warn] Failed to install: ${pkg}"
	return 1
}

pacman_install() {
	local -a essential=(
		iw gawk aircrack-ng xterm iproute2 pciutils
		nftables curl wget openssl ethtool usbutils rfkill
		xorg-xdpyinfo xorg-xset python-flask python-flask-socketio
		python-psutil
	)
	local -a optional=(
		crunch mdk4 hashcat hostapd dhcp
		ettercap dsniff reaver bully pixiewps
		bettercap john ccze tmux net-tools wireless_tools
		sslstrip beef hostapd-wpe asleap
	)
	local pkg

	echo "[*] Installing essential packages..."
	for pkg in "${essential[@]}"; do
		pacman_install_one "${pkg}" || true
	done

	if [[ "${MINIMAL}" -eq 0 ]]; then
		echo "[*] Installing optional attack / menu packages..."
		for pkg in "${optional[@]}"; do
			pacman_install_one "${pkg}" || true
		done
	fi
}

install_files() {
	echo "[*] Installing SATANA to ${INSTALL_DIR} ..."
	mkdir -p "${INSTALL_DIR}"

	if command -v rsync >/dev/null 2>&1; then
		rsync -a --delete \
			--exclude='.git/' \
			--exclude='*.log' \
			--exclude='satana-debug.log' \
			"${SCRIPT_DIR}/" "${INSTALL_DIR}/"
	else
		rm -rf "${INSTALL_DIR:?}"/*
		cp -a "${SCRIPT_DIR}/." "${INSTALL_DIR}/"
		rm -f "${INSTALL_DIR}/satana-debug.log" 2>/dev/null || true
	fi

	chmod +x "${INSTALL_DIR}/satana.sh" "${INSTALL_DIR}/install.sh" "${INSTALL_DIR}/satana-web" "${INSTALL_DIR}/satana.py"
	chmod +x "${INSTALL_DIR}/plugins/"*.sh 2>/dev/null || true
	chmod +x "${INSTALL_DIR}/scripts/install-beef.sh" 2>/dev/null || true

	strip_utf8_bom
}

install_launcher() {
	echo "[*] Creating command: ${BIN_PATH}"
	cat > "${BIN_PATH}" <<LAUNCHER
#!/usr/bin/env bash
# SATANA launcher — installed by install.sh
SATANA_HOME="${INSTALL_DIR}"

if [[ ! -f "\${SATANA_HOME}/satana.sh" ]]; then
	echo "SATANA not found in \${SATANA_HOME}. Re-run: sudo ./install.sh" >&2
	exit 1
fi

cd "\${SATANA_HOME}" || exit 1

if [[ \${EUID} -ne 0 ]]; then
	exec sudo -E bash "\${SATANA_HOME}/satana.sh" "\$@"
fi

exec bash "\${SATANA_HOME}/satana.sh" "\$@"
LAUNCHER
	chmod 755 "${BIN_PATH}"

	echo "[*] Creating command: ${WEB_BIN_PATH}"
	cat > "${WEB_BIN_PATH}" <<LAUNCHER
#!/usr/bin/env bash
# SATANA Web launcher — installed by install.sh
SATANA_HOME="${INSTALL_DIR}"

if [[ ! -f "\${SATANA_HOME}/satana/web/app.py" ]]; then
	echo "SATANA Web UI not found in \${SATANA_HOME}. Re-run: sudo ./install.sh" >&2
	exit 1
fi

cd "\${SATANA_HOME}" || exit 1
exec python3 satana.py web "\$@"
LAUNCHER
	chmod 755 "${WEB_BIN_PATH}"
}

main() {
	echo "=============================================="
	echo " SATANA installer"
	echo " Source: ${SCRIPT_DIR}"
	echo " Target: ${INSTALL_DIR}"
	echo "=============================================="

	case "$(detect_distro)" in
		apt) apt_install ;;
		pacman) pacman_install ;;
		*)
			echo "[warn] Unknown distro. Skipping package manager; install tools manually." >&2
			echo "       Supported: Debian, Ubuntu, Kali, Parrot, Arch, BlackArch." >&2
			;;
	esac

	install_files
	install_launcher

	echo ""
	echo "Done."
	echo "  Install dir: ${INSTALL_DIR}"
	echo "  Command:     sudo ${BIN_NAME}"
	echo "  Web UI:      ${WEB_BIN_NAME}"
	echo ""
	echo "Re-install after updates: sudo ./install.sh"
}

main "$@"
