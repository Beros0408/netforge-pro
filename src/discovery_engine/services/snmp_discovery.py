"""
SNMP discovery service for retrieving device information via SNMP.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Address
from typing import Optional, List

try:
    from pysnmp.hlapi import (
        getCmd, nextCmd, SnmpEngine, CommunityData, UdpTransportTarget,
        ContextData, ObjectType, ObjectIdentity
    )
    from pysnmp.smi import view
    PYSNMP_AVAILABLE = True
except ImportError:
    # Fallback for different pysnmp versions
    try:
        from pysnmp.hlapi.v1arch import (
            getCmd, nextCmd, SnmpEngine, CommunityData, UdpTransportTarget,
            ContextData, ObjectType, ObjectIdentity
        )
        from pysnmp.smi import view
        PYSNMP_AVAILABLE = True
    except ImportError:
        PYSNMP_AVAILABLE = False

from ..config import settings
from ..models.discovery import SNMPInfo


class SNMPDiscovery:
    """
    Service for SNMP-based device discovery and information retrieval.
    """

    # Common SNMP OIDs
    SYS_DESCR_OID = "1.3.6.1.2.1.1.1.0"      # System description
    SYS_NAME_OID = "1.3.6.1.2.1.1.5.0"       # System name
    SYS_LOCATION_OID = "1.3.6.1.2.1.1.6.0"   # System location
    SYS_CONTACT_OID = "1.3.6.1.2.1.1.4.0"    # System contact
    SYS_UPTIME_OID = "1.3.6.1.2.1.1.3.0"     # System uptime
    IF_NUMBER_OID = "1.3.6.1.2.1.2.1.0"      # Number of interfaces

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_scans)

    async def discover_device(self, ip: IPv4Address, community_strings: Optional[List[str]] = None) -> Optional[SNMPInfo]:
        """
        Discover device information via SNMP.

        Args:
            ip: Device IP address
            community_strings: SNMP community strings to try

        Returns:
            SNMPInfo if successful, None otherwise
        """
        if not PYSNMP_AVAILABLE:
            return None

        if community_strings is None:
            community_strings = settings.snmp_community_strings

        # Try each community string
        for community in community_strings:
            snmp_info = await self._try_snmp_discovery(str(ip), community)
            if snmp_info:
                return snmp_info

        return None

    async def _try_snmp_discovery(self, ip: str, community: str) -> Optional[SNMPInfo]:
        """
        Attempt SNMP discovery with specific community string.

        Args:
            ip: Device IP address
            community: SNMP community string

        Returns:
            SNMPInfo if successful, None otherwise
        """
        def snmp_query():
            try:
                # Create SNMP engine
                snmp_engine = SnmpEngine()

                # Create transport target
                transport = UdpTransportTarget(
                    (ip, 161),
                    timeout=settings.snmp_timeout,
                    retries=settings.snmp_retries
                )

                # Create community data
                community_data = CommunityData(community)

                # Query system information
                oids = [
                    ObjectType(ObjectIdentity(self.SYS_DESCR_OID)),
                    ObjectType(ObjectIdentity(self.SYS_NAME_OID)),
                    ObjectType(ObjectIdentity(self.SYS_LOCATION_OID)),
                    ObjectType(ObjectIdentity(self.SYS_CONTACT_OID)),
                    ObjectType(ObjectIdentity(self.SYS_UPTIME_OID)),
                    ObjectType(ObjectIdentity(self.IF_NUMBER_OID)),
                ]

                # Execute SNMP GET request
                error_indication, error_status, error_index, var_binds = next(
                    getCmd(snmp_engine, community_data, transport, ContextData(), *oids)
                )

                if error_indication:
                    return None

                if error_status:
                    return None

                # Parse results
                snmp_info = SNMPInfo()
                mib_view = view.MibViewController(snmp_engine.getMibBuilder())

                for var_bind in var_binds:
                    oid, value = var_bind
                    oid_str = oid.prettyPrint()

                    try:
                        # Convert OID to name for easier processing
                        oid_name = mib_view.getNodeName(oid)
                    except:
                        oid_name = oid_str

                    # Extract value
                    if hasattr(value, 'prettyPrint'):
                        value_str = value.prettyPrint()
                    else:
                        value_str = str(value)

                    # Map to SNMPInfo fields
                    if self.SYS_DESCR_OID in oid_str or 'sysDescr' in oid_name:
                        snmp_info.sysDescr = value_str
                    elif self.SYS_NAME_OID in oid_str or 'sysName' in oid_name:
                        snmp_info.sysName = value_str
                    elif self.SYS_LOCATION_OID in oid_str or 'sysLocation' in oid_name:
                        snmp_info.sysLocation = value_str
                    elif self.SYS_CONTACT_OID in oid_str or 'sysContact' in oid_name:
                        snmp_info.sysContact = value_str
                    elif self.SYS_UPTIME_OID in oid_str or 'sysUpTime' in oid_name:
                        snmp_info.sysUpTime = value_str
                    elif self.IF_NUMBER_OID in oid_str or 'ifNumber' in oid_name:
                        try:
                            snmp_info.ifNumber = int(value_str)
                        except ValueError:
                            pass

                return snmp_info

            except Exception:
                return None

        # Run SNMP query in thread pool
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self.executor, snmp_query)
            return result
        except Exception:
            return None

    async def get_interface_info(self, ip: IPv4Address, community: str = "public") -> List[dict]:
        """
        Get detailed interface information via SNMP.

        Args:
            ip: Device IP address
            community: SNMP community string

        Returns:
            List of interface information dictionaries
        """
        if not PYSNMP_AVAILABLE:
            return []

        def snmp_walk():
            try:
                snmp_engine = SnmpEngine()
                transport = UdpTransportTarget((str(ip), 161))
                community_data = CommunityData(community)

                # Interface description OID
                if_descr_oid = ObjectType(ObjectIdentity("1.3.6.1.2.1.2.2.1.2"))

                interfaces = []
                for error_indication, error_status, error_index, var_binds in nextCmd(
                    snmp_engine, community_data, transport, ContextData(), if_descr_oid
                ):
                    if error_indication:
                        break
                    elif error_status:
                        break
                    else:
                        for var_bind in var_binds:
                            oid, value = var_bind
                            # Extract interface index from OID
                            oid_parts = oid.asTuple()
                            if len(oid_parts) >= 11:  # IF-MIB::ifDescr.index format
                                if_index = oid_parts[10]  # Last part is interface index
                                interfaces.append({
                                    'index': if_index,
                                    'description': str(value)
                                })

                return interfaces

            except Exception:
                return []

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(self.executor, snmp_walk)
            return result
        except Exception:
            return []

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)