#!/usr/bin/env bash
cat /etc/os-release | head -5
echo "---"
for p in sslstrip beef-xss hostapd-wpe asleap; do
	if apt-cache show "$p" >/dev/null 2>&1; then
		echo "OK: $p"
	else
		echo "MISSING: $p"
	fi
done
echo "---"
for p in sslstrip beef-xss hostapd-wpe asleap; do
	apt-cache search "^${p}$" 2>/dev/null | head -1
done
