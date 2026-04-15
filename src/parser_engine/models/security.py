"""
Security models — ACLs, firewall policies, NAT rules.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# ACL
# ---------------------------------------------------------------------------

class ACLType(str, Enum):
    """Cisco ACL type."""

    STANDARD = "standard"
    EXTENDED = "extended"
    NAMED_STANDARD = "named_standard"
    NAMED_EXTENDED = "named_extended"
    IPV6 = "ipv6"
    UNKNOWN = "unknown"


class ACLAction(str, Enum):
    """Action applied when an ACE matches."""

    PERMIT = "permit"
    DENY = "deny"


class ACLEntry(BaseModel):
    """
    A single Access Control Entry (ACE).

    Attributes:
        sequence: Optional sequence number (e.g. Cisco named ACL).
        action: permit or deny.
        protocol: Matched protocol (ip, tcp, udp, icmp, …).
        source: Source address or keyword (any, host <ip>, <net> <mask>).
        source_port: Source port or range.
        destination: Destination address or keyword.
        destination_port: Destination port or range.
        log: Whether logging is enabled for this ACE.
        remark: Free-text remark line.
    """

    sequence: Optional[int] = Field(None, ge=1, description="ACE sequence number")
    action: ACLAction = Field(..., description="permit or deny")
    protocol: Optional[str] = Field(None, description="Matched L4 protocol")
    source: Optional[str] = Field(None, description="Source address or keyword")
    source_port: Optional[str] = Field(None, description="Source port / range")
    destination: Optional[str] = Field(None, description="Destination address or keyword")
    destination_port: Optional[str] = Field(None, description="Destination port / range")
    log: bool = Field(default=False, description="Logging enabled")
    remark: Optional[str] = Field(None, description="Remark text")


class ACL(BaseModel):
    """
    An Access Control List composed of one or more ACEs.

    Attributes:
        name: ACL name or numeric identifier.
        acl_type: ACL type classification.
        entries: Ordered list of ACEs.
        interface_in: Interface(s) where this ACL is applied inbound.
        interface_out: Interface(s) where this ACL is applied outbound.
    """

    name: str = Field(..., description="ACL name or number")
    acl_type: ACLType = Field(default=ACLType.UNKNOWN, description="ACL type")
    entries: list[ACLEntry] = Field(default_factory=list, description="ACEs in order")
    interface_in: list[str] = Field(
        default_factory=list, description="Inbound application interfaces"
    )
    interface_out: list[str] = Field(
        default_factory=list, description="Outbound application interfaces"
    )

    @property
    def entry_count(self) -> int:
        """Number of ACEs (excluding remarks)."""
        return sum(1 for e in self.entries if e.remark is None)

    def __str__(self) -> str:
        return f"ACL({self.name}, {self.acl_type.value}, {self.entry_count} entries)"


# ---------------------------------------------------------------------------
# Firewall Policy (FortiOS / Cisco ASA style)
# ---------------------------------------------------------------------------

class FirewallPolicyAction(str, Enum):
    """Action of a firewall policy."""

    ACCEPT = "accept"
    DENY = "deny"
    DROP = "drop"
    REJECT = "reject"


class FirewallPolicy(BaseModel):
    """
    A firewall rule / policy (primarily FortiOS, but usable for ASA as well).

    Attributes:
        policy_id: Numeric policy identifier.
        name: Policy name.
        source_zones: Source security zones / interfaces.
        destination_zones: Destination security zones / interfaces.
        source_addresses: Source address objects.
        destination_addresses: Destination address objects.
        services: Service objects (port/protocol).
        action: Firewall action (accept/deny/drop).
        nat: Whether NAT is applied.
        logging: Whether traffic logging is enabled.
        status: Whether the policy is enabled.
        schedule: Schedule object name.
        comments: Operator comments.
    """

    policy_id: int = Field(..., ge=0, description="Numeric policy ID")
    name: Optional[str] = Field(None, description="Policy name")

    source_zones: list[str] = Field(default_factory=list, description="Source zones")
    destination_zones: list[str] = Field(
        default_factory=list, description="Destination zones"
    )
    source_addresses: list[str] = Field(
        default_factory=list, description="Source address objects"
    )
    destination_addresses: list[str] = Field(
        default_factory=list, description="Destination address objects"
    )
    services: list[str] = Field(
        default_factory=list, description="Service / port-group objects"
    )

    action: FirewallPolicyAction = Field(
        default=FirewallPolicyAction.DENY, description="Policy action"
    )
    nat: bool = Field(default=False, description="NAT enabled")
    logging: bool = Field(default=False, description="Traffic logging enabled")
    status: bool = Field(default=True, description="Policy administratively enabled")
    schedule: Optional[str] = Field(None, description="Schedule object name")
    comments: Optional[str] = Field(None, description="Operator comments")


# ---------------------------------------------------------------------------
# NAT
# ---------------------------------------------------------------------------

class NATType(str, Enum):
    """NAT translation type."""

    STATIC = "static"
    DYNAMIC = "dynamic"
    PAT = "pat"  # Port Address Translation (overload)
    POLICY = "policy"


class NATRule(BaseModel):
    """
    A NAT rule entry.

    Attributes:
        rule_id: Numeric or string identifier.
        nat_type: NAT type (static/dynamic/PAT).
        source_network: Inside local network.
        translated_address: Inside global / translated address or pool.
        interface: Exit interface (for interface-based PAT).
        overload: True when PAT (many-to-one) is active.
        acl_name: ACL that selects traffic to be translated.
        vrf: VRF context.
    """

    rule_id: Optional[str] = Field(None, description="Rule identifier")
    nat_type: NATType = Field(default=NATType.STATIC, description="NAT type")
    source_network: Optional[str] = Field(None, description="Source / inside-local network")
    translated_address: Optional[str] = Field(
        None, description="Translated / inside-global address"
    )
    interface: Optional[str] = Field(None, description="Exit interface for overload NAT")
    overload: bool = Field(default=False, description="PAT overload enabled")
    acl_name: Optional[str] = Field(
        None, description="ACL selecting traffic for dynamic NAT"
    )
    vrf: Optional[str] = Field(None, description="VRF name")
