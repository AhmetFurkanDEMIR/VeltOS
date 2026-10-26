#!/bin/sh
# Dev aid (VM only): a simulated phone for testing VeltOS' mobile hotspot.
# Two mac80211_hwsim radios: wlan0 stays with NetworkManager (the PC's
# Wi-Fi, which shares the connection), the second radio moves into the
# network namespace "phone", where wpa_supplicant and dhcpcd join the
# hotspot like a phone would.
#   hotspotsim.sh radios          load the radios, move the second one
#   hotspotsim.sh join SSID KEY   join the hotspot from "phone"
#   hotspotsim.sh leave           disconnect the phone
#   hotspotsim.sh test            ping and HTTP through the hotspot
set -eu
case "${1:-}" in
radios)
    lsmod | grep -q mac80211_hwsim || modprobe mac80211_hwsim radios=2
    sleep 2
    ip netns list | grep -q phone || ip netns add phone
    phy=$(for p in /sys/class/ieee80211/*; do
              n=$(basename "$p")
              ls "$p/device/net" 2>/dev/null | grep -qx wlan1 && echo "$n"
          done)
    [ -n "$phy" ] && iw_phy="$phy" || iw_phy=""
    if [ -n "$iw_phy" ]; then
        # No `iw` in the image: move the phy with busybox-free sysfs is not
        # possible, so use `ip link set netns` on the interface (works for
        # mac80211_hwsim since the radio has no other users).
        nmcli device set wlan1 managed no || true
        ip link set wlan1 netns phone || true
    fi
    ip netns exec phone ip link set lo up
    ip netns exec phone ip link
    nmcli device
    ;;
join)
    mkdir -p /tmp/phone
    cat > /tmp/phone/wpa.conf <<EOF
ctrl_interface=/tmp/phone/ctrl
network={
    ssid="$2"
    psk="$3"
    key_mgmt=WPA-PSK
}
EOF
    ip netns exec phone ip link set wlan1 up
    ip netns exec phone wpa_supplicant -B -i wlan1 -c /tmp/phone/wpa.conf -P /tmp/phone/wpa.pid
    sleep 6
    mkdir -p /etc/netns/phone
    echo "nameserver 10.42.0.1" > /etc/netns/phone/resolv.conf
    ip netns exec phone dhcpcd -4 --nohook resolv.conf -h veltos-phone -t 30 wlan1 || true
    # dhcpcd's hook still rewrites the PC's own /etc/resolv.conf (and the
    # hotspot's dnsmasq then asks itself): let NetworkManager write it again.
    nmcli general reload dns-full
    sleep 2
    ip netns exec phone ip -4 addr show wlan1
    ;;
leave)
    ip netns exec phone dhcpcd -k wlan1 2>/dev/null || true
    pkill -x dhcpcd || true
    [ -f /tmp/phone/wpa.pid ] && kill "$(cat /tmp/phone/wpa.pid)" || true
    # A stale control socket makes the next wpa_supplicant -B fail silently.
    rm -rf /tmp/phone/wpa.pid /tmp/phone/ctrl
    ip netns exec phone ip link set wlan1 down || true
    ;;
test)
    ip netns exec phone ip route
    ip netns exec phone ping -c 3 -W 3 10.0.2.2 || true
    ip netns exec phone busybox wget -q -T 10 -O /dev/null http://deb.debian.org/debian/ && echo HTTP-OK || echo HTTP-FAIL
    ;;
*)
    echo "usage: hotspotsim.sh radios|join SSID KEY|leave|test" >&2
    exit 2
    ;;
esac
