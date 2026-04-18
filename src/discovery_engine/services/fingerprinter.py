"""
Device fingerprinting service using multi-source analysis.
"""
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
from ipaddress import IPv4Address
from typing import Dict, Optional, Tuple

import paramiko

from ..config import settings
from ..models.discovery import (
    VendorType, DeviceType, FingerprintResult, SNMPInfo, SSHInfo, MACInfo
)


class DeviceFingerprinter:
    """
    Service for fingerprinting network devices using multiple sources.
    Combines SNMP, SSH banner, and MAC OUI analysis with weighted scoring.
    """

    # Vendor patterns for different sources
    VENDOR_PATTERNS = {
        # SNMP sysDescr patterns
        'snmp': {
            VendorType.CISCO: [
                r'Cisco IOS Software',
                r'Cisco Nexus Operating System',
                r'Cisco Adaptive Security Appliance',
                r'Cisco Internetwork Operating System',
            ],
            VendorType.HUAWEI: [
                r'Huawei.*VRP',
                r'Huawei Versatile Routing Platform',
            ],
            VendorType.ARISTA: [
                r'Arista.*EOS',
                r'Arista Networks EOS',
            ],
            VendorType.FORTINET: [
                r'FortiGate',
                r'Fortinet',
            ],
            VendorType.JUNIPER: [
                r'Juniper Networks',
                r'JUNOS Software Release',
            ],
            VendorType.EXTREME: [
                r'ExtremeXOS',
                r'Extreme Networks',
            ],
            VendorType.BROCADE: [
                r'Brocade',
                r'Foundry Networks',
            ],
            VendorType.HP: [
                r'Hewlett-Packard',
                r'HP.*Switch',
                r'ProCurve',
            ],
            VendorType.DELL: [
                r'Dell.*Switch',
                r'Dell PowerConnect',
            ],
        },

        # SSH banner patterns
        'ssh': {
            VendorType.CISCO: [
                r'Cisco-',
                r'User Access Verification',
            ],
            VendorType.HUAWEI: [
                r'Huawei',
                r'VRP',
            ],
            VendorType.ARISTA: [
                r'Arista',
            ],
            VendorType.FORTINET: [
                r'FortiGate',
            ],
            VendorType.JUNIPER: [
                r'Juniper',
            ],
        },

        # MAC OUI to vendor mapping
        'mac': {
            VendorType.CISCO: ['00:00:0C', '00:1A:2B', '00:50:56'],
            VendorType.HUAWEI: ['00:E0:FC', '00:1A:8C'],
            VendorType.ARISTA: ['00:1C:73'],
            VendorType.FORTINET: ['00:09:0F'],
            VendorType.JUNIPER: ['00:05:85', '00:10:DB'],
            VendorType.EXTREME: ['00:04:96'],
            VendorType.BROCADE: ['00:05:33', '00:1B:ED'],
            VendorType.HP: ['00:01:E7', '00:0F:61', '00:11:0A'],
            VendorType.DELL: ['00:14:22', '00:21:9B'],
        }
    }

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_scans)

    async def fingerprint_device(
        self,
        ip: IPv4Address,
        snmp_info: Optional[SNMPInfo] = None,
        ssh_info: Optional[SSHInfo] = None,
        mac_info: Optional[MACInfo] = None
    ) -> FingerprintResult:
        """
        Fingerprint a device using available information sources.

        Args:
            ip: Device IP address
            snmp_info: SNMP information if available
            ssh_info: SSH information if available
            mac_info: MAC address information if available

        Returns:
            FingerprintResult with vendor identification and confidence score
        """
        # Analyze each source
        snmp_result = await self._analyze_snmp(snmp_info) if snmp_info else (VendorType.UNKNOWN, 0.0)
        ssh_result = await self._analyze_ssh(ssh_info) if ssh_info else (VendorType.UNKNOWN, 0.0)
        mac_result = self._analyze_mac(mac_info) if mac_info else (VendorType.UNKNOWN, 0.0)

        # Combine results with weights
        vendor_scores = {}
        fingerprint_sources = {}

        # SNMP analysis
        vendor, confidence = snmp_result
        if vendor != VendorType.UNKNOWN:
            vendor_scores[vendor] = vendor_scores.get(vendor, 0) + confidence * settings.snmp_fingerprint_weight
            fingerprint_sources['snmp'] = confidence

        # SSH analysis
        vendor, confidence = ssh_result
        if vendor != VendorType.UNKNOWN:
            vendor_scores[vendor] = vendor_scores.get(vendor, 0) + confidence * settings.ssh_fingerprint_weight
            fingerprint_sources['ssh'] = confidence

        # MAC analysis
        vendor, confidence = mac_result
        if vendor != VendorType.UNKNOWN:
            vendor_scores[vendor] = vendor_scores.get(vendor, 0) + confidence * settings.mac_fingerprint_weight
            fingerprint_sources['mac'] = confidence

        # Determine best vendor match
        if vendor_scores:
            best_vendor = max(vendor_scores.items(), key=lambda x: x[1])
            final_vendor = best_vendor[0]
            confidence_score = min(best_vendor[1], 1.0)  # Cap at 1.0
        else:
            final_vendor = VendorType.UNKNOWN
            confidence_score = 0.0

        # Extract additional information
        device_type = self._determine_device_type(final_vendor, snmp_info, ssh_info)
        os_version = self._extract_os_version(final_vendor, snmp_info, ssh_info)
        model = self._extract_model(final_vendor, snmp_info, ssh_info)

        return FingerprintResult(
            vendor=final_vendor,
            device_type=device_type,
            os_version=os_version,
            model=model,
            confidence_score=confidence_score,
            fingerprint_sources=fingerprint_sources
        )

    async def _analyze_snmp(self, snmp_info: SNMPInfo) -> Tuple[VendorType, float]:
        """
        Analyze SNMP information for vendor identification.

        Args:
            snmp_info: SNMP information

        Returns:
            Tuple of (vendor, confidence_score)
        """
        if not snmp_info or not snmp_info.sysDescr:
            return VendorType.UNKNOWN, 0.0

        sys_descr = snmp_info.sysDescr.lower()

        for vendor, patterns in self.VENDOR_PATTERNS['snmp'].items():
            for pattern in patterns:
                if re.search(pattern.lower(), sys_descr, re.IGNORECASE):
                    # Extract version information if available
                    confidence = 0.9  # High confidence for SNMP match
                    return vendor, confidence

        return VendorType.UNKNOWN, 0.0

    async def _analyze_ssh(self, ssh_info: SSHInfo) -> Tuple[VendorType, float]:
        """
        Analyze SSH banner for vendor identification.

        Args:
            ssh_info: SSH information

        Returns:
            Tuple of (vendor, confidence_score)
        """
        if not ssh_info or not ssh_info.banner:
            return VendorType.UNKNOWN, 0.0

        banner = ssh_info.banner.lower()

        for vendor, patterns in self.VENDOR_PATTERNS['ssh'].items():
            for pattern in patterns:
                if re.search(pattern.lower(), banner, re.IGNORECASE):
                    confidence = 0.8  # Good confidence for SSH banner match
                    return vendor, confidence

        return VendorType.UNKNOWN, 0.0

    def _analyze_mac(self, mac_info: MACInfo) -> Tuple[VendorType, float]:
        """
        Analyze MAC address OUI for vendor identification.

        Args:
            mac_info: MAC address information

        Returns:
            Tuple of (vendor, confidence_score)
        """
        if not mac_info or not mac_info.oui:
            return VendorType.UNKNOWN, 0.0

        oui = mac_info.oui.upper()

        for vendor, ouis in self.VENDOR_PATTERNS['mac'].items():
            if oui in ouis:
                confidence = 0.7  # Moderate confidence for MAC OUI match
                return vendor, confidence

        return VendorType.UNKNOWN, 0.0

    def _determine_device_type(
        self,
        vendor: VendorType,
        snmp_info: Optional[SNMPInfo],
        ssh_info: Optional[SSHInfo]
    ) -> DeviceType:
        """
        Determine device type based on vendor and available information.

        Args:
            vendor: Identified vendor
            snmp_info: SNMP information
            ssh_info: SSH information

        Returns:
            DeviceType classification
        """
        # Default classifications by vendor
        vendor_defaults = {
            VendorType.CISCO: DeviceType.ROUTER,  # Cisco can be router or switch
            VendorType.HUAWEI: DeviceType.ROUTER,
            VendorType.ARISTA: DeviceType.SWITCH,
            VendorType.FORTINET: DeviceType.FIREWALL,
            VendorType.JUNIPER: DeviceType.ROUTER,
            VendorType.EXTREME: DeviceType.SWITCH,
            VendorType.BROCADE: DeviceType.SWITCH,
            VendorType.HP: DeviceType.SWITCH,
            VendorType.DELL: DeviceType.SWITCH,
        }

        # Analyze sysDescr for more specific classification
        if snmp_info and snmp_info.sysDescr:
            descr = snmp_info.sysDescr.lower()

            # Router indicators
            if any(keyword in descr for keyword in ['router', 'routing', 'ios', 'vrp']):
                return DeviceType.ROUTER

            # Switch indicators
            if any(keyword in descr for keyword in ['switch', 'switching', 'lan', 'eos']):
                return DeviceType.SWITCH

            # Firewall indicators
            if any(keyword in descr for keyword in ['firewall', 'asa', 'fortigate']):
                return DeviceType.FIREWALL

        return vendor_defaults.get(vendor, DeviceType.UNKNOWN)

    def _extract_os_version(
        self,
        vendor: VendorType,
        snmp_info: Optional[SNMPInfo],
        ssh_info: Optional[SSHInfo]
    ) -> Optional[str]:
        """
        Extract OS version from available information.

        Args:
            vendor: Identified vendor
            snmp_info: SNMP information
            ssh_info: SSH information

        Returns:
            OS version string if found
        """
        # Try SNMP sysDescr first
        if snmp_info and snmp_info.sysDescr:
            descr = snmp_info.sysDescr

            # Vendor-specific version extraction patterns
            patterns = {
                VendorType.CISCO: [
                    r'Version (\d+\.\d+\([^)]+\)[^,]*)',
                    r'IOS.*Version (\d+\.\d+[^,]*)',
                ],
                VendorType.HUAWEI: [
                    r'Version (\d+\.\d+[^,]*)',
                    r'VRP.*(\d+\.\d+)',
                ],
                VendorType.ARISTA: [
                    r'EOS version (\d+\.\d+\.[^ ]+)',
                ],
                VendorType.FORTINET: [
                    r'FortiGate.*v(\d+\.\d+\.\d+)',
                ],
            }

            vendor_patterns = patterns.get(vendor, [])
            for pattern in vendor_patterns:
                match = re.search(pattern, descr, re.IGNORECASE)
                if match:
                    return match.group(1)

        # Try SSH banner as fallback
        if ssh_info and ssh_info.banner:
            # Simple version extraction from banner
            version_match = re.search(r'(\d+\.\d+(?:\.\d+)?)', ssh_info.banner)
            if version_match:
                return version_match.group(1)

        return None

    def _extract_model(
        self,
        vendor: VendorType,
        snmp_info: Optional[SNMPInfo],
        ssh_info: Optional[SSHInfo]
    ) -> Optional[str]:
        """
        Extract device model from available information.

        Args:
            vendor: Identified vendor
            snmp_info: SNMP information
            ssh_info: SSH information

        Returns:
            Device model string if found
        """
        # Try SNMP sysDescr first
        if snmp_info and snmp_info.sysDescr:
            descr = snmp_info.sysDescr

            # Vendor-specific model extraction patterns
            patterns = {
                VendorType.CISCO: [
                    r'(CISCO\d+|WS-C\d+|Nexus\d+|ASA\d+)',
                    r'(\d+\.\d+\.\d+\.\d+)',
                ],
                VendorType.HUAWEI: [
                    r'(NE\d+|CE\d+|S\d+)',
                ],
                VendorType.ARISTA: [
                    r'(DCS-\d+|CCS-\d+)',
                ],
                VendorType.FORTINET: [
                    r'(FortiGate-\d+|FG-\d+)',
                ],
            }

            vendor_patterns = patterns.get(vendor, [])
            for pattern in vendor_patterns:
                match = re.search(pattern, descr, re.IGNORECASE)
                if match:
                    return match.group(1)

        return None

    def __del__(self):
        """Cleanup executor on destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)