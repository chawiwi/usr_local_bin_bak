from typing import Union
from isc_dhcp_leases import IscDhcpLeases
from .sf import get_key_from_sn
from .consts import DHCPD_LEASES_PATH
from re import search, sub


def normalize_mac(mac: str,sep: str = ":") -> str:
    mac = sub(r"[^a-fA-F0-9]", "", mac).lower()[:12]
    return sep.join([mac[i : i + 2] for i in range(0, len(mac), 2)])


def find_mac_two_rm(
    sn: str, location: str, threshold: int, use_cache=False
) -> Union[str, None]:
    try:
        location_num = int(search(r"\d+", location)[0])
    except:
        return None
    if location_num > threshold:
        key = get_key_from_sn("RACK_MOUNT1_MAC1", sn, use_cache=use_cache)
        if key:
            return key
    return get_key_from_sn("RACK_MOUNT_MAC1", sn, use_cache=use_cache)


ip_cache = {}


def get_rm_ip_from_sn(
    sn: str, model: str, location: str, use_cache=False
) -> Union[str, None]:
    if model == "C2398":
        rm_mac = find_mac_two_rm(sn, location, 20)
    elif model == "C2298":
        rm_mac = find_mac_two_rm(sn, location, 21)
    elif model == "C229D":
        rm_mac = find_mac_two_rm(sn, location, 21)
    else:
        rm_mac = get_key_from_sn("RACK_MOUNT_MAC1", sn, use_cache=use_cache)

    if rm_mac is None:
        return None

    rm_mac = normalize_mac(rm_mac)

    if ip_cache.get(rm_mac):
        return ip_cache[rm_mac]

    ip = get_leased_ip(rm_mac)
    ip_cache[rm_mac] = ip
    return ip


def get_leased_ip(mac: str) -> Union[str, None]:
    leases = IscDhcpLeases(DHCPD_LEASES_PATH)
    cur = leases.get_current()
    lease = cur.get(mac)
    if lease is None:
        return None
    return lease.ip
