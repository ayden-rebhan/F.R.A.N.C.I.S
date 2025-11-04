import socket
import time
from typing import List, Dict

SSDP_ADDR = ("239.255.255.250", 1900)
MSEARCH = "M-SEARCH * HTTP/1.1\r\nHOST:239.255.255.250:1900\r\nMAN:\"ssdp:discover\"\r\nMX:1\r\nST:ssdp:all\r\n\r\n"


def discover_devices(timeout: float = 2.0) -> List[Dict[str, str]]:
    """Perform a simple SSDP M-SEARCH and collect responses."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(timeout)

    try:
        sock.sendto(MSEARCH.encode('utf-8'), SSDP_ADDR)
    except Exception:
        sock.close()
        return []

    start = time.time()
    devices = []
    seen = set()
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            text = data.decode('utf-8', errors='ignore')
            if addr[0] in seen:
                continue
            seen.add(addr[0])
            device = {'address': addr[0], 'response': text}
            devices.append(device)
        except socket.timeout:
            break
        except Exception:
            break
        if time.time() - start > timeout:
            break

    sock.close()
    return devices
