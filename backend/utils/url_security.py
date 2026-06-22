import ipaddress
import socket
from urllib.parse import urlparse


def is_public_http_url(url: str) -> bool:
    """Return True only for http(s) URLs resolving to public Internet addresses.

    This is a lightweight SSRF guard for endpoints that fetch user-provided URLs.
    It rejects localhost, private networks, link-local/cloud metadata ranges,
    multicast/reserved addresses, and malformed hosts. Hostnames are resolved at
    validation time; callers should also avoid automatic redirects unless every
    redirect target is revalidated.
    """
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    host = parsed.hostname.strip().rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
        except socket.gaierror:
            return False
        addresses = []
        for info in infos:
            try:
                addresses.append(ipaddress.ip_address(info[4][0]))
            except ValueError:
                return False
    if not addresses:
        return False
    return all(is_public_ip(address) for address in addresses)


def is_public_ip(address: ipaddress._BaseAddress) -> bool:
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def is_allowed_host(url: str, allowed_hosts: tuple[str, ...]) -> bool:
    parsed = urlparse(str(url or "").strip())
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and bool(host) and any(host == item or host.endswith(f".{item}") for item in allowed_hosts)
