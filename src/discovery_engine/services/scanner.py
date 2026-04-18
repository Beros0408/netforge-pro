"""
Network scanner service for ping sweep and port scanning.
"""
import asyncio
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Network, IPv4Address
from typing import List, Optional, Set

import scapy.all as scapy

from ..config import settings
from ..models.discovery import PortInfo, PortStatus, DiscoveredDevice


class NetworkScanner:
    """
    Service for network scanning operations including ping sweep and port scanning.
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_scans)

    async def ping_sweep(self, network: IPv4Network) -> List[IPv4Address]:
        """
        Perform ping sweep on network range to find alive hosts.

        Args:
            network: IPv4Network range to scan

        Returns:
            List of IP addresses that responded to ping
        """
        alive_hosts = []

        # Create ping packets for all hosts in network
        ping_tasks = []
        for ip in network.hosts():
            ping_tasks.append(self._ping_host(str(ip)))

        # Execute ping sweep concurrently
        results = await asyncio.gather(*ping_tasks, return_exceptions=True)

        # Collect alive hosts
        for ip, result in zip(network.hosts(), results):
            if result is True:  # Host is alive
                alive_hosts.append(ip)

        return alive_hosts

    async def _ping_host(self, ip: str) -> bool:
        """
        Ping a single host.

        Args:
            ip: IP address to ping

        Returns:
            True if host responds, False otherwise
        """
        def ping():
            # Create ICMP echo request
            packet = scapy.IP(dst=ip)/scapy.ICMP()
            # Send packet and wait for response
            response = scapy.sr1(packet, timeout=settings.scan_timeout_seconds, verbose=0)
            return response is not None

        # Run ping in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self.executor, ping)
            return result
        except Exception:
            return False

    async def port_scan(self, ip: IPv4Address, ports: Optional[List[int]] = None) -> List[PortInfo]:
        """
        Scan ports on a target IP address.

        Args:
            ip: Target IP address
            ports: List of ports to scan (default: config default_ports)

        Returns:
            List of PortInfo objects with scan results
        """
        if ports is None:
            ports = settings.default_ports

        port_scan_tasks = []
        for port in ports:
            port_scan_tasks.append(self._scan_port(str(ip), port))

        # Execute port scans concurrently
        results = await asyncio.gather(*port_scan_tasks, return_exceptions=True)

        port_infos = []
        for port, result in zip(ports, results):
            if isinstance(result, Exception):
                # Port scan failed
                port_info = PortInfo(
                    port=port,
                    status=PortStatus.UNKNOWN
                )
            else:
                port_info = result
            port_infos.append(port_info)

        return port_infos

    async def _scan_port(self, ip: str, port: int) -> PortInfo:
        """
        Scan a single port on target IP.

        Args:
            ip: Target IP address
            port: Port number to scan

        Returns:
            PortInfo with scan results
        """
        def scan():
            try:
                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(settings.port_scan_timeout)

                # Attempt connection
                result = sock.connect_ex((ip, port))

                if result == 0:
                    # Port is open
                    status = PortStatus.OPEN
                    # Try to get service banner for known ports
                    banner = None
                    if port in [22, 23]:  # SSH or Telnet
                        try:
                            banner = self._get_service_banner(sock, port)
                        except:
                            pass
                else:
                    status = PortStatus.CLOSED

                sock.close()
                return PortInfo(port=port, status=status, banner=banner)

            except Exception:
                return PortInfo(port=port, status=PortStatus.UNKNOWN)

        # Run port scan in thread pool
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self.executor, scan)
            return result
        except Exception:
            return PortInfo(port=port, status=PortStatus.UNKNOWN)

    def _get_service_banner(self, sock: socket.socket, port: int) -> Optional[str]:
        """
        Attempt to get service banner from open port.

        Args:
            sock: Connected socket
            port: Port number

        Returns:
            Service banner if available
        """
        try:
            if port == 22:  # SSH
                # SSH banner is sent immediately upon connection
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                return banner
            elif port == 23:  # Telnet
                # Telnet might require sending something to get a response
                sock.send(b'\r\n')
                banner = sock.recv(1024).decode('utf-8', errors='ignore').strip()
                return banner
        except Exception:
            pass
        return None

    async def scan_network(self, network: IPv4Network, ports: Optional[List[int]] = None) -> List[DiscoveredDevice]:
        """
        Perform complete network scan: ping sweep + port scanning.

        Args:
            network: Network range to scan
            ports: Ports to scan on alive hosts

        Returns:
            List of discovered devices with basic information
        """
        # Step 1: Ping sweep to find alive hosts
        alive_hosts = await self.ping_sweep(network)

        # Step 2: Port scan alive hosts
        scan_tasks = []
        for ip in alive_hosts:
            scan_tasks.append(self._scan_host(ip, ports))

        # Execute host scans concurrently
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)

        devices = []
        for ip, result in zip(alive_hosts, results):
            if isinstance(result, Exception):
                # Host scan failed, create minimal device info
                device = DiscoveredDevice(
                    ip_address=ip,
                    is_alive=True,
                    discovery_method="network_scan"
                )
            else:
                device = result
            devices.append(device)

        return devices

    async def _scan_host(self, ip: IPv4Address, ports: Optional[List[int]] = None) -> DiscoveredDevice:
        """
        Scan a single host completely.

        Args:
            ip: Host IP address
            ports: Ports to scan

        Returns:
            DiscoveredDevice with scan results
        """
        # Port scan
        open_ports = await self.port_scan(ip, ports)

        # Create device info
        device = DiscoveredDevice(
            ip_address=ip,
            is_alive=True,
            open_ports=open_ports,
            discovery_method="network_scan"
        )

        return device

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)