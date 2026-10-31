#!/bin/sh
# Dev aid (VM only): the mobile hotspot over the PC's only Wi-Fi card.
# Three mac80211_hwsim radios: wlan0 is the PC's Wi-Fi (NetworkManager) and
# joins "Upstream", an access point in namespace "upstream" (hostapd, dnsmasq
# for DHCP, a web server at 192.168.77.1:8080 that answers UPSTREAM-OK);
# Ethernet is disconnected, so Wi-Fi is the PC's only connection. The third
# radio is a phone in namespace "phone" that joins the hotspot.
#   samecard.sh setup             radios, upstream, wlan0 joins it, Ethernet off
#   samecard.sh join SSID KEY     the phone joins the hotspot
#   samecard.sh test              the phone reaches the upstream web server
#   samecard.sh ethernet          Ethernet back on
set -eu
W=/tmp/samecard
phy_of() { basename "$(readlink -f "/sys/class/net/$1/phy80211")"; }
case "${1:-}" in
setup)
    mkdir -p $W
    lsmod | grep -q mac80211_hwsim || modprobe mac80211_hwsim radios=3
    sleep 2
    for ns in upstream phone; do ip netns list | grep -qw $ns || ip netns add $ns; done
    nmcli device set wlan1 managed no || true
    nmcli device set wlan2 managed no || true
    iw phy "$(phy_of wlan1)" set netns name upstream
    iw phy "$(phy_of wlan2)" set netns name phone
    ip netns exec upstream ip link set lo up
    ip netns exec phone ip link set lo up
    ip netns exec upstream ip addr add 192.168.77.1/24 dev wlan1
    cat > $W/upstream.conf <<EOF
interface=wlan1
driver=nl80211
ssid=Upstream
hw_mode=g
channel=6
wpa=2
wpa_passphrase=upstream123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOF
    ip netns exec upstream hostapd -B -P $W/hostapd.pid $W/upstream.conf
    sleep 2
    ip netns exec upstream dnsmasq --conf-file=/dev/null --interface=wlan1 --bind-interfaces \
        --dhcp-range=192.168.77.50,192.168.77.150,12h --dhcp-option=3,192.168.77.1 \
        --dhcp-option=6,192.168.77.1 --pid-file=$W/dnsmasq.pid --leasefile-ro --port=0
    mkdir -p $W/www && echo UPSTREAM-OK > $W/www/index.html
    ip netns exec upstream sh -c "cd $W/www && nohup python3 -m http.server 8080 --bind 192.168.77.1 >$W/http.log 2>&1 &"
    for dev in $(nmcli -t -f DEVICE,TYPE device status | awk -F: '$2=="ethernet"{print $1}'); do
        nmcli device disconnect "$dev" || true
    done
    nmcli device wifi rescan ifname wlan0 || true
    sleep 4
    nmcli device wifi connect Upstream password upstream123 ifname wlan0
    sleep 3
    nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device status
    ip -4 route
    iw dev wlan0 link
    ;;
join)
    mkdir -p $W/phone
    cat > $W/phone/wpa.conf <<EOF
ctrl_interface=$W/phone/ctrl
network={
    ssid="$2"
    psk="$3"
    key_mgmt=WPA-PSK
}
EOF
    ip netns exec phone ip link set wlan2 up
    ip netns exec phone wpa_supplicant -B -i wlan2 -c $W/phone/wpa.conf -P $W/phone/wpa.pid
    sleep 8
    ip netns exec phone iw dev wlan2 link || true
    if command -v dhcpcd >/dev/null; then
        ip netns exec phone dhcpcd -4 --nohook resolv.conf -h veltos-phone -t 30 wlan2 || true
        nmcli general reload dns-full || true
    else
        ip netns exec phone busybox udhcpc -i wlan2 -x hostname:veltos-phone -n -q -t 10 \
            -s /usr/share/udhcpc/default.script || true
    fi
    ip netns exec phone ip -4 addr show wlan2
    ;;
test)
    ip netns exec phone ip -4 route
    ip netns exec phone ping -c 3 -W 3 192.168.77.1 || true
    ip netns exec phone python3 -c "import urllib.request; print(urllib.request.urlopen('http://192.168.77.1:8080/', timeout=10).read().decode().strip())" || echo HTTP-FAIL
    ;;
ethernet)
    for dev in $(nmcli -t -f DEVICE,TYPE device status | awk -F: '$2=="ethernet"{print $1}'); do
        nmcli device connect "$dev" || true
    done
    ;;
*)
    echo "usage: samecard.sh setup|join SSID KEY|test|ethernet" >&2
    exit 2
    ;;
esac
