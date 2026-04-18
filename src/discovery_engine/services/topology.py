"""
Network topology discovery service using LLDP and CDP protocols.
"""
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Address
from typing import List, Optional, Dict, Any

from netmiko import ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException

from ..config import settings
from ..models.discovery import NeighborInfo, VendorType, DiscoveredDevice


class TopologyDiscovery:
    """
    Service for discovering network topology using LLDP and CDP protocols.
    """

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_scans)

    async def discover_neighbors(
        self,
        device: DiscoveredDevice,
        credentials: Optional[Dict[str, Any]] = None
    ) -> List[NeighborInfo]:
        """
        Discover network neighbors using LLDP/CDP from a device.

        Args:
            device: Discovered device to query
            credentials: SSH credentials for device access

        Returns:
            List of neighbor information
        """
        if not credentials:
            return []

        # Try different connection methods based on device type
        neighbors = []

        # Try SSH connection
        ssh_neighbors = await self._discover_via_ssh(device.ip_address, credentials)
        if ssh_neighbors:
            neighbors.extend(ssh_neighbors)

        return neighbors

    async def _discover_via_ssh(self, ip: IPv4Address, credentials: Dict[str, Any]) -> List[NeighborInfo]:
        """
        Discover neighbors via SSH connection to device.

        Args:
            ip: Device IP address
            credentials: SSH credentials

        Returns:
            List of neighbor information
        """
        def ssh_discovery():
            try:
                # Prepare connection parameters
                device_params = {
                    'device_type': self._determine_device_type(ip, credentials),
                    'host': str(ip),
                    'username': credentials.get('username'),
                    'password': credentials.get('password'),
                    'timeout': settings.ssh_timeout,
                }

                # Add optional parameters
                if 'port' in credentials:
                    device_params['port'] = credentials['port']
                if 'secret' in credentials:
                    device_params['secret'] = credentials['secret']

                # Connect to device
                with ConnectHandler(**device_params) as conn:
                    # Try LLDP first
                    lldp_neighbors = self._get_lldp_neighbors(conn)
                    if lldp_neighbors:
                        return lldp_neighbors

                    # Try CDP as fallback
                    cdp_neighbors = self._get_cdp_neighbors(conn)
                    if cdp_neighbors:
                        return cdp_neighbors

                return []

            except (NetMikoTimeoutException, NetMikoAuthenticationException, Exception):
                return []

        # Run SSH discovery in thread pool
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self.executor, ssh_discovery)
            return result
        except Exception:
            return []

    def _determine_device_type(self, ip: IPv4Address, credentials: Dict[str, Any]) -> str:
        """
        Determine Netmiko device type based on credentials or IP.

        Args:
            ip: Device IP address
            credentials: Connection credentials

        Returns:
            Netmiko device type string
        """
        # Check if device_type is explicitly provided
        if 'device_type' in credentials:
            return credentials['device_type']

        # Default to Cisco IOS (most common)
        return 'cisco_ios'

    def _get_lldp_neighbors(self, conn) -> List[NeighborInfo]:
        """
        Get LLDP neighbors from device.

        Args:
            conn: Netmiko connection object

        Returns:
            List of NeighborInfo objects
        """
        try:
            # Try common LLDP commands
            commands = [
                'show lldp neighbors',
                'show lldp neighbors detail',
                'show lldp neighbor',
            ]

            for cmd in commands:
                try:
                    output = conn.send_command(cmd)
                    if output and 'LLDP' in output.upper():
                        return self._parse_lldp_output(output)
                except:
                    continue

        except Exception:
            pass

        return []

    def _get_cdp_neighbors(self, conn) -> List[NeighborInfo]:
        """
        Get CDP neighbors from device.

        Args:
            conn: Netmiko connection object

        Returns:
            List of NeighborInfo objects
        """
        try:
            # Try CDP commands
            commands = [
                'show cdp neighbors',
                'show cdp neighbors detail',
            ]

            for cmd in commands:
                try:
                    output = conn.send_command(cmd)
                    if output and ('CDP' in output.upper() or 'Neighbor' in output):
                        return self._parse_cdp_output(output)
                except:
                    continue

        except Exception:
            pass

        return []

    def _parse_lldp_output(self, output: str) -> List[NeighborInfo]:
        """
        Parse LLDP command output.

        Args:
            output: LLDP command output

        Returns:
            List of NeighborInfo objects
        """
        neighbors = []

        # Split output into lines
        lines = output.split('\n')

        # Skip header lines
        data_lines = []
        in_table = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for table headers
            if 'Local Intf' in line or 'Interface' in line:
                in_table = True
                continue

            if in_table and line and not line.startswith('-'):
                data_lines.append(line)

        # Parse each neighbor line
        for line in data_lines[:10]:  # Limit to first 10 neighbors
            neighbor = self._parse_lldp_neighbor_line(line)
            if neighbor:
                neighbors.append(neighbor)

        return neighbors

    def _parse_cdp_output(self, output: str) -> List[NeighborInfo]:
        """
        Parse CDP command output.

        Args:
            output: CDP command output

        Returns:
            List of NeighborInfo objects
        """
        neighbors = []

        # Split output into lines
        lines = output.split('\n')

        # Skip header lines
        data_lines = []
        in_table = False
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for table headers
            if 'Device ID' in line or 'Local Intrfce' in line:
                in_table = True
                continue

            if in_table and line and not line.startswith('-'):
                data_lines.append(line)

        # Parse each neighbor line
        for line in data_lines[:10]:  # Limit to first 10 neighbors
            neighbor = self._parse_cdp_neighbor_line(line)
            if neighbor:
                neighbors.append(neighbor)

        return neighbors

    def _parse_lldp_neighbor_line(self, line: str) -> Optional[NeighborInfo]:
        """
        Parse a single LLDP neighbor line.

        Args:
            line: Neighbor line from LLDP output

        Returns:
            NeighborInfo object or None
        """
        try:
            # Common LLDP output formats
            # Format: Local Intf    Neighbor Device    Neighbor Intf    Capabilities
            parts = re.split(r'\s{2,}', line.strip())

            if len(parts) >= 4:
                local_intf = parts[0].strip()
                remote_device = parts[1].strip()
                remote_intf = parts[2].strip()
                capabilities = parts[3].strip() if len(parts) > 3 else ""

                # Extract capabilities
                caps_list = []
                if 'R' in capabilities:
                    caps_list.append('Router')
                if 'S' in capabilities:
                    caps_list.append('Switch')
                if 'B' in capabilities:
                    caps_list.append('Bridge')

                return NeighborInfo(
                    local_interface=local_intf,
                    remote_device=remote_device,
                    remote_interface=remote_intf,
                    protocol='LLDP',
                    capabilities=caps_list
                )

        except Exception:
            pass

        return None

    def _parse_cdp_neighbor_line(self, line: str) -> Optional[NeighborInfo]:
        """
        Parse a single CDP neighbor line.

        Args:
            line: Neighbor line from CDP output

        Returns:
            NeighborInfo object or None
        """
        try:
            # Common CDP output formats
            # Format: Device ID    Local Intrfce    Holdtme    Capability    Platform    Port ID
            parts = re.split(r'\s{2,}', line.strip())

            if len(parts) >= 6:
                remote_device = parts[0].strip()
                local_intf = parts[1].strip()
                capabilities = parts[3].strip()
                platform = parts[4].strip()
                remote_intf = parts[5].strip()

                # Extract capabilities
                caps_list = []
                if 'R' in capabilities:
                    caps_list.append('Router')
                if 'S' in capabilities:
                    caps_list.append('Switch')
                if 'T' in capabilities:
                    caps_list.append('Trans-Bridge')

                # Try to identify vendor from platform
                remote_vendor = self._identify_vendor_from_platform(platform)

                return NeighborInfo(
                    local_interface=local_intf,
                    remote_device=remote_device,
                    remote_interface=remote_intf,
                    remote_vendor=remote_vendor,
                    protocol='CDP',
                    capabilities=caps_list
                )

        except Exception:
            pass

        return None

    def _identify_vendor_from_platform(self, platform: str) -> Optional[VendorType]:
        """
        Identify vendor from platform string in CDP output.

        Args:
            platform: Platform string from CDP

        Returns:
            VendorType if identifiable
        """
        platform_lower = platform.lower()

        if 'cisco' in platform_lower:
            return VendorType.CISCO
        elif 'huawei' in platform_lower:
            return VendorType.HUAWEI
        elif 'arista' in platform_lower:
            return VendorType.ARISTA
        elif 'fortinet' in platform_lower or 'fortigate' in platform_lower:
            return VendorType.FORTINET
        elif 'juniper' in platform_lower:
            return VendorType.JUNIPER
        elif 'extreme' in platform_lower:
            return VendorType.EXTREME
        elif 'brocade' in platform_lower:
            return VendorType.BROCADE
        elif 'hp' in platform_lower or 'procurve' in platform_lower:
            return VendorType.HP
        elif 'dell' in platform_lower:
            return VendorType.DELL

        return None

    async def auto_discover(
        self,
        seed_ip: IPv4Address,
        credentials: Dict[str, Any],
        max_hops: int = 3
    ) -> List[DiscoveredDevice]:
        """
        Perform automatic network discovery starting from a seed device.

        Args:
            seed_ip: IP address of seed device
            credentials: SSH credentials
            max_hops: Maximum discovery hops

        Returns:
            List of discovered devices
        """
        discovered_devices = []
        visited_ips = set()
        to_visit = [(seed_ip, 0)]  # (ip, hop_count)

        while to_visit and len(discovered_devices) < 100:  # Safety limit
            current_ip, hop_count = to_visit.pop(0)

            if current_ip in visited_ips or hop_count > max_hops:
                continue

            visited_ips.add(current_ip)

            # Create device object for current IP
            device = DiscoveredDevice(
                ip_address=current_ip,
                is_alive=True,
                discovery_method="auto_discovery"
            )

            # Discover neighbors
            neighbors = await self.discover_neighbors(device, credentials)
            device.neighbors = neighbors

            discovered_devices.append(device)

            # Add neighbor IPs to visit queue
            if hop_count < max_hops:
                for neighbor in neighbors:
                    # Try to extract IP from neighbor device name
                    neighbor_ip = self._extract_ip_from_neighbor(neighbor.remote_device)
                    if neighbor_ip and neighbor_ip not in visited_ips:
                        to_visit.append((neighbor_ip, hop_count + 1))

        return discovered_devices

    def _extract_ip_from_neighbor(self, remote_device: str) -> Optional[IPv4Address]:
        """
        Extract IP address from neighbor device string.

        Args:
            remote_device: Remote device identifier

        Returns:
            IPv4Address if found
        """
        # Look for IP address patterns
        ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', remote_device)
        if ip_match:
            try:
                return IPv4Address(ip_match.group(0))
            except:
                pass

        return None

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)