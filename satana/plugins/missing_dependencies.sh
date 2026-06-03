#!/usr/bin/env bash

#Global shellcheck disabled warnings
#shellcheck disable=SC2034

plugin_name="Missing dependencies auto-installation"
plugin_description="A plugin to autoinstall missing dependencies on Debian-based and Arch-based systems"
plugin_author="v1s1t0r"

plugin_enabled=1

plugin_minimum_ag_affected_version="10.0"
plugin_maximum_ag_affected_version=""
plugin_distros_supported=("Kali" "Parrot" "BlackArch" "Debian" "Ubuntu" "Mint" "Raspbian" "Kali arm" "Parrot arm")

#Populate commands_to_packages_correspondence for apt-based distros
#shellcheck disable=SC2154
function missing_dependencies_fill_apt_correspondence() {

	commands_to_packages_correspondence["ifconfig"]="net-tools"
	commands_to_packages_correspondence["iwconfig"]="wireless-tools"
	commands_to_packages_correspondence["iw"]="iw"
	commands_to_packages_correspondence["awk"]="gawk"
	commands_to_packages_correspondence["airmon-ng"]="aircrack-ng"
	commands_to_packages_correspondence["airodump-ng"]="aircrack-ng"
	commands_to_packages_correspondence["aircrack-ng"]="aircrack-ng"
	commands_to_packages_correspondence["xterm"]="xterm"
	commands_to_packages_correspondence["tmux"]="tmux"
	commands_to_packages_correspondence["ip"]="iproute2"
	commands_to_packages_correspondence["lspci"]="pciutils"
	commands_to_packages_correspondence["ps"]="procps"
	commands_to_packages_correspondence["wpaclean"]="aircrack-ng"
	commands_to_packages_correspondence["crunch"]="crunch"
	commands_to_packages_correspondence["aireplay-ng"]="aircrack-ng"
	commands_to_packages_correspondence["mdk3"]="mdk3"
	commands_to_packages_correspondence["mdk4"]="mdk4"
	commands_to_packages_correspondence["hashcat"]="hashcat"
	commands_to_packages_correspondence["hostapd"]="hostapd"
	commands_to_packages_correspondence["dhcpd"]="isc-dhcp-server"
	commands_to_packages_correspondence["nft"]="nftables"
	commands_to_packages_correspondence["iptables"]="iptables"
	commands_to_packages_correspondence["ettercap"]="ettercap-text-only"
	commands_to_packages_correspondence["etterlog"]="ettercap-text-only"
	commands_to_packages_correspondence["sslstrip"]="sslstrip"
	commands_to_packages_correspondence["lighttpd"]="lighttpd"
	commands_to_packages_correspondence["dnsspoof"]="dsniff"
	commands_to_packages_correspondence["wash"]="reaver"
	commands_to_packages_correspondence["reaver"]="reaver"
	commands_to_packages_correspondence["bully"]="bully"
	commands_to_packages_correspondence["pixiewps"]="pixiewps"
	commands_to_packages_correspondence["bettercap"]="bettercap"
	commands_to_packages_correspondence["beef-xss"]="beef-xss"
	commands_to_packages_correspondence["packetforge-ng"]="aircrack-ng"
	commands_to_packages_correspondence["hostapd-wpe"]="hostapd-wpe"
	commands_to_packages_correspondence["asleap"]="asleap"
	commands_to_packages_correspondence["john"]="john"
	commands_to_packages_correspondence["openssl"]="openssl"
	commands_to_packages_correspondence["xdpyinfo"]="x11-utils"
	commands_to_packages_correspondence["ethtool"]="ethtool"
	commands_to_packages_correspondence["lsusb"]="usbutils"
	commands_to_packages_correspondence["rfkill"]="rfkill"
	commands_to_packages_correspondence["wget"]="wget"
	commands_to_packages_correspondence["ccze"]="ccze"
	commands_to_packages_correspondence["xset"]="x11-xserver-utils"
	commands_to_packages_correspondence["curl"]="curl"
}

#Custom function. Create the correspondence between commands and packages for each supported distro
#shellcheck disable=SC2154
function commands_to_packages() {

	local missing_commands_string_clean
	missing_commands_string_clean="${1#${1%%[![:space:]]*}}"

	declare -gA commands_to_packages_correspondence

	case "${distro}" in
		"Kali"|"Parrot"|"Kali arm"|"Parrot arm"|"Debian"|"Ubuntu"|"Mint"|"Raspbian")
			missing_dependencies_fill_apt_correspondence
		;;
		"BlackArch")
			commands_to_packages_correspondence["ifconfig"]="net-tools"
			commands_to_packages_correspondence["iwconfig"]="wireless_tools"
			commands_to_packages_correspondence["iw"]="iw"
			commands_to_packages_correspondence["awk"]="gawk"
			commands_to_packages_correspondence["airmon-ng"]="aircrack-ng"
			commands_to_packages_correspondence["airodump-ng"]="aircrack-ng"
			commands_to_packages_correspondence["aircrack-ng"]="aircrack-ng"
			commands_to_packages_correspondence["xterm"]="xterm"
			commands_to_packages_correspondence["tmux"]="tmux"
			commands_to_packages_correspondence["ip"]="iproute2"
			commands_to_packages_correspondence["lspci"]="pciutils"
			commands_to_packages_correspondence["ps"]="procps-ng"
			commands_to_packages_correspondence["wpaclean"]="aircrack-ng"
			commands_to_packages_correspondence["crunch"]="crunch"
			commands_to_packages_correspondence["aireplay-ng"]="aircrack-ng"
			commands_to_packages_correspondence["mdk3"]="mdk3"
			commands_to_packages_correspondence["mdk4"]="mdk4"
			commands_to_packages_correspondence["hashcat"]="hashcat"
			commands_to_packages_correspondence["hostapd"]="hostapd"
			commands_to_packages_correspondence["dhcpd"]="dhcp"
			commands_to_packages_correspondence["nft"]="nftables"
			commands_to_packages_correspondence["iptables"]="iptables"
			commands_to_packages_correspondence["ettercap"]="ettercap"
			commands_to_packages_correspondence["etterlog"]="ettercap"
			commands_to_packages_correspondence["sslstrip"]="sslstrip"
			commands_to_packages_correspondence["lighttpd"]="lighttpd"
			commands_to_packages_correspondence["dnsspoof"]="dsniff"
			commands_to_packages_correspondence["wash"]="reaver"
			commands_to_packages_correspondence["reaver"]="reaver"
			commands_to_packages_correspondence["bully"]="bully"
			commands_to_packages_correspondence["pixiewps"]="pixiewps"
			commands_to_packages_correspondence["bettercap"]="bettercap"
			commands_to_packages_correspondence["beef"]="beef"
			commands_to_packages_correspondence["packetforge-ng"]="aircrack-ng"
			commands_to_packages_correspondence["hostapd-wpe"]="hostapd-wpe"
			commands_to_packages_correspondence["asleap"]="asleap"
			commands_to_packages_correspondence["john"]="john"
			commands_to_packages_correspondence["openssl"]="openssl"
			commands_to_packages_correspondence["xdpyinfo"]="xorg-xdpyinfo"
			commands_to_packages_correspondence["ethtool"]="ethtool"
			commands_to_packages_correspondence["lsusb"]="usbutils"
			commands_to_packages_correspondence["rfkill"]="rfkill"
			commands_to_packages_correspondence["wget"]="wget"
			commands_to_packages_correspondence["ccze"]="ccze"
			commands_to_packages_correspondence["xset"]="xorg-xset"
			commands_to_packages_correspondence["curl"]="curl"
		;;
	esac

	local missing_packages_string=""
	declare -A unique_packages=()
	IFS=' ' read -r -a missing_commands_array <<< "${missing_commands_string_clean}"
	for item in "${missing_commands_array[@]}"; do
		local pkg="${commands_to_packages_correspondence[${item}]}"
		if [[ -n "${pkg}" ]] && [[ -z "${unique_packages[${pkg}]}" ]]; then
			unique_packages["${pkg}"]=1
			missing_packages_string+=" ${pkg}"
		fi
	done

	missing_packages_string_clean="${missing_packages_string#${missing_packages_string%%[![:space:]]*}}"
	IFS=' ' read -r -a missing_packages_array <<< "${missing_packages_string_clean}"
}

#Install BeEF from GitHub when beef-xss package is missing or fake
#shellcheck disable=SC2154
function missing_dependencies_install_beef_from_source() {

	local beef_install_script="${scriptfolder}scripts/install-beef.sh"

	if [[ ! -f "${beef_install_script}" ]]; then
		return 0
	fi

	if hash "beef" 2> /dev/null; then
		detect_fake_beef
		if [[ ${fake_beef_found} -eq 0 ]]; then
			return 0
		fi
	fi

	if hash "beef-xss" 2> /dev/null; then
		return 0
	fi

	if [[ -f "/opt/beef/beef" ]]; then
		return 0
	fi

	echo
	language_strings "${language}" "missing_dependencies_3" "blue"
	bash "${beef_install_script}" > /dev/null 2>&1 || bash "${beef_install_script}" || true
}

#Re-scan installed tools after package installation
#shellcheck disable=SC2154
function missing_dependencies_refresh_tool_status() {

	essential_toolsok=1
	for item in "${essential_tools_names[@]}"; do
		if ! hash "${item}" 2> /dev/null; then
			essential_toolsok=0
		fi
	done

	optional_toolsok=1
	for item in "${!optional_tools[@]}"; do
		if ! hash "${item}" 2> /dev/null; then
			optional_tools[${item}]=0
			optional_toolsok=0
		else
			if [ "${item}" = "beef" ]; then
				detect_fake_beef
				if [ ${fake_beef_found} -eq 1 ]; then
					optional_tools[${item}]=0
					optional_toolsok=0
				else
					optional_tools[${item}]=1
				fi
			else
				optional_tools[${item}]=1
			fi
		fi
	done

	update_toolsok=1
	if "${SATANA_AUTO_UPDATE:-true}"; then
		for item in "${update_tools[@]}"; do
			if ! hash "${item}" 2> /dev/null; then
				update_toolsok=0
			fi
		done
	fi

	if [ ${essential_toolsok} -eq 1 ]; then
		compatible=1
	else
		compatible=0
	fi
}

#Custom function. Create text messages to be used in missing dependencies plugin
#shellcheck disable=SC2154
function missing_dependencies_text() {

	arr["RUSSIAN","missing_dependencies_1"]="${blue_color}Даже при включённой опции ${normal_color}SATANA_SILENT_CHECKS${blue_color}, SATANA с помощью плагина auto install missing dependencies (автоматическая установка отсутствующих зависимостей) обнаружил, что вам не хватает некоторых зависимостей. ${green_color}Вы хотите продолжить автоматическую установку? ${normal_color}${visual_choice}"

	arr["RUSSIAN","missing_dependencies_2"]="${blue_color}Благодаря плагину auto install missing dependencies (автоматическая установка отсутствующих зависимостей) SATANA может попытаться установить необходимые недостающие пакеты. ${green_color}Вы хотите продолжить автоматическую установку? ${normal_color}${visual_choice}"

	arr["RUSSIAN","missing_dependencies_3"]="Попытка установить пакеты отсутствующих зависимостей. Подождите немного..."

	arr["RUSSIAN","missing_dependencies_4"]="Зависимости установлены правильно. Скрипт может продолжать..."

	arr["RUSSIAN","missing_dependencies_5"]="Произошла ошибка при попытке установить зависимости. Это может быть связано с несколькими причинами. Убедитесь, что подключение к Интернету работает. Во всяком случае, вы установили все инструменты необходимые для базовой работы. Вам будут недоступны только некоторые функции"

	arr["RUSSIAN","missing_dependencies_6"]="Произошла ошибка при попытке установить зависимости. Это может быть связано с несколькими причинами. Убедитесь, что подключение к Интернету работает. Скрипт не может продолжить работу из-за отсутствия некоторых необходимых инструментов"

	arr["RUSSIAN","missing_dependencies_7"]="${blue_color}Обнаружены отсутствующие компоненты. Запускается автоматическая установка...${normal_color}"
}

#Posthook for check_compatibity function to install missing dependencies
#shellcheck disable=SC2154
function missing_dependencies_posthook_check_compatibility() {

	if [[ ${essential_toolsok} -ne 1 ]] || [[ ${optional_toolsok} -ne 1 ]] || [[ ${update_toolsok} -ne 1 ]]; then

		if "${SATANA_AUTO_INSTALL_MISSING:-true}"; then
			yesno="y"
			echo
			missing_dependencies_text
			language_strings "${language}" "missing_dependencies_7" "blue"
		elif "${SATANA_SILENT_CHECKS:-true}"; then
			ask_yesno "missing_dependencies_1" "yes"
		else
			ask_yesno "missing_dependencies_2" "yes"
		fi

		if [ "${yesno}" = "y" ]; then

			missing_dependencies_text

			local missing_tools=()

			for item in "${!possible_package_names[@]}"; do
				if ! hash "${item}" 2> /dev/null || [[ "${item}" = "beef" ]]; then
					if [ "${item}" = "beef" ]; then
						case "${distro}" in
							"Kali"|"Parrot"|"Kali arm"|"Parrot arm"|"Debian"|"Ubuntu"|"Mint"|"Raspbian")
								if ! hash "beef-xss" 2> /dev/null; then
									missing_tools+=("beef-xss")
								fi
							;;
							"BlackArch")
								if ! hash "${item}" 2> /dev/null; then
									missing_tools+=("${item}")
								fi
							;;
						esac
					else
						missing_tools+=("${item}")
					fi
				fi
			done

			for item in "${internal_tools[@]}"; do
				if ! hash "${item}" 2> /dev/null; then
					missing_tools+=("${item}")
				fi
			done

			if "${SATANA_AUTO_UPDATE:-true}"; then
				for item in "${update_tools[@]}"; do
					if ! hash "${item}" 2> /dev/null; then
						missing_tools+=("${item}")
					fi
				done
			fi

			local missing_commands_string=""
			for item in "${missing_tools[@]}"; do
				missing_commands_string+=" ${item}"
			done

			commands_to_packages "${missing_commands_string}"

			if [ ${#missing_packages_array[@]} -eq 0 ]; then
				missing_dependencies_install_beef_from_source
				missing_dependencies_refresh_tool_status
				return
			fi

			echo
			language_strings "${language}" "missing_dependencies_3" "blue"
			echo

			local resultok=0
			local pkg
			case "${distro}" in
				"Kali"|"Parrot"|"Kali arm"|"Parrot arm"|"Debian"|"Ubuntu"|"Mint"|"Raspbian")
					if apt-get update > /dev/null 2>&1; then
						for pkg in "${missing_packages_array[@]}"; do
							if DEBIAN_FRONTEND=noninteractive apt-get install -y "${pkg}" > /dev/null 2>&1; then
								resultok=1
							elif DEBIAN_FRONTEND=noninteractive apt install -y "${pkg}" > /dev/null 2>&1; then
								resultok=1
							fi
						done
					elif apt update > /dev/null 2>&1; then
						for pkg in "${missing_packages_array[@]}"; do
							if DEBIAN_FRONTEND=noninteractive apt install -y "${pkg}" > /dev/null 2>&1; then
								resultok=1
							fi
						done
					fi
				;;
				"BlackArch")
					if pacman -Sy > /dev/null 2>&1; then
						for pkg in "${missing_packages_array[@]}"; do
							if pacman --noconfirm -S "${pkg}" > /dev/null 2>&1; then
								resultok=1
							fi
						done
					fi
				;;
			esac

			missing_dependencies_install_beef_from_source

			missing_dependencies_refresh_tool_status

			if [ ${resultok} -eq 1 ] && [ ${essential_toolsok} -eq 1 ]; then
				language_strings "${language}" "missing_dependencies_4" "yellow"
			else
				if [ ${compatible} -eq 1 ]; then
					language_strings "${language}" "missing_dependencies_5" "yellow"
				else
					language_strings "${language}" "missing_dependencies_6" "red"
					language_strings "${language}" 115 "read"
				fi
			fi
		else
			if [ "${compatible}" -ne 1 ]; then
				exit_code=1
				exit_script_option
			fi
		fi
	fi
}

#Override read_yesno function to be able to print the question correctly
#shellcheck disable=SC2154
function missing_dependencies_override_read_yesno() {

	debug_print

	echo
	missing_dependencies_text

	language_strings "${language}" "${1}" "green"
	read -rp "> " yesno
}
