#!/usr/bin/env bash
# Install BeEF from https://github.com/beefproject/beef (SATANA auto-install).
# Usage: sudo ./scripts/install-beef.sh
# Env: BEEF_INSTALL_DIR (default /opt/beef), BEEF_REPO_URL

set -euo pipefail

BEEF_DIR="${BEEF_INSTALL_DIR:-/opt/beef}"
BEEF_REPO="${BEEF_REPO_URL:-https://github.com/beefproject/beef.git}"

apt_install_beef_deps() {
	export DEBIAN_FRONTEND=noninteractive
	apt-get update -qq
	apt-get install -y --no-install-recommends \
		git curl wget ruby-full build-essential \
		sqlite3 libsqlite3-dev zlib1g-dev ruby-dev ruby-bundler
}

clone_and_bundle() {
	mkdir -p "$(dirname "${BEEF_DIR}")"

	if [[ -f "${BEEF_DIR}/beef" ]] && [[ -f "${BEEF_DIR}/Gemfile" ]]; then
		echo "[*] BeEF found at ${BEEF_DIR}, updating gems..."
		(cd "${BEEF_DIR}" && bundle install)
		chmod +x "${BEEF_DIR}/beef" 2>/dev/null || true
		return 0
	fi

	if [[ -d "${BEEF_DIR}/.git" ]]; then
		echo "[*] BeEF git repo at ${BEEF_DIR}, running bundle install..."
		(cd "${BEEF_DIR}" && bundle install)
		chmod +x "${BEEF_DIR}/beef" 2>/dev/null || true
		return 0
	fi

	echo "[*] Cloning BeEF into ${BEEF_DIR} ..."
	rm -rf "${BEEF_DIR}"
	git clone --depth 1 "${BEEF_REPO}" "${BEEF_DIR}"
	(cd "${BEEF_DIR}" && bundle install)
	chmod +x "${BEEF_DIR}/beef" 2>/dev/null || true
}

install_beef_command() {
	if [[ ! -f "${BEEF_DIR}/beef" ]]; then
		echo "[warn] ${BEEF_DIR}/beef not found after bundle install" >&2
		return 1
	fi

	cat > /usr/local/bin/beef <<EOF
#!/usr/bin/env bash
cd "${BEEF_DIR}" || exit 1
exec ./beef "\$@"
EOF
	chmod 755 /usr/local/bin/beef

	if [[ ! -e /usr/bin/beef ]] || [[ -L /usr/bin/beef ]]; then
		ln -sf /usr/local/bin/beef /usr/bin/beef 2>/dev/null || cp -f /usr/local/bin/beef /usr/bin/beef
		chmod 755 /usr/bin/beef 2>/dev/null || true
	fi

	echo "[ok] BeEF launcher: /usr/local/bin/beef -> ${BEEF_DIR}"
}

main() {
	if [[ "${EUID}" -ne 0 ]]; then
		echo "Run as root: sudo $0" >&2
		exit 1
	fi

	if ! command -v git >/dev/null 2>&1 || ! command -v bundle >/dev/null 2>&1; then
		if command -v apt-get >/dev/null 2>&1; then
			apt_install_beef_deps
		else
			echo "[warn] apt-get not found; install git, ruby, bundler manually." >&2
			exit 1
		fi
	elif command -v apt-get >/dev/null 2>&1; then
		apt_install_beef_deps || true
	fi

	clone_and_bundle
	install_beef_command
	echo "[ok] BeEF installation finished."
}

main "$@"
