"""
Rule Engine tests — covers all 13 rules + service + models.
Target: ≥ 30 passing tests, all using mocks (no network required).
"""
from __future__ import annotations

import pytest

from ...parser_engine.models.device import Device, VendorType
from ...parser_engine.models.interface import Interface, InterfaceStatus, InterfaceType, SwitchportMode
from ...parser_engine.models.routing import BGPNeighbor, BGPProcess, OSPFNetwork, OSPFProcess, Route, VRF
from ...parser_engine.models.security import ACL, ACLAction, ACLEntry, ACLType, FirewallPolicy, FirewallPolicyAction
from ...parser_engine.models.vlan import VLAN
from ..models.problem import Category, Problem, Severity
from ..rules.l2_rules import (
    ErrDisabledPortRule,
    LACPInconsistentRule,
    PotentialLoopRule,
    UnexpectedRootBridgeRule,
    VLANMismatchRule,
)
from ..rules.l3_rules import (
    AsymmetricRoutingRule,
    BGPNeighborDownRule,
    OSPFAreaMismatchRule,
    OSPFMTUMismatchRule,
    VRFRouteLeakingRule,
)
from ..rules.security_rules import AnyAnyPermitRule, ContradictoryACLRule, ShadowedACLRule
from ..services.rule_service import RuleService


# ===========================================================================
# Helpers
# ===========================================================================

def _device(hostname: str = "router1", **kwargs) -> Device:
    """Minimal Device factory."""
    return Device(hostname=hostname, vendor=VendorType.CISCO, **kwargs)


def _trunk(name: str, trunk_vlans=None, native_vlan=None, channel_group=None,
           status=InterfaceStatus.UP, mtu=None, speed=None, duplex=None) -> Interface:
    return Interface(
        name=name,
        interface_type=InterfaceType.GIGABIT_ETHERNET,
        switchport_mode=SwitchportMode.TRUNK,
        trunk_vlans=trunk_vlans or [],
        native_vlan=native_vlan,
        channel_group=channel_group,
        status=status,
        mtu=mtu,
        speed=speed,
        duplex=duplex,
    )


def _access(name: str, access_vlan=10, status=InterfaceStatus.UP) -> Interface:
    return Interface(
        name=name,
        interface_type=InterfaceType.GIGABIT_ETHERNET,
        switchport_mode=SwitchportMode.ACCESS,
        access_vlan=access_vlan,
        status=status,
    )


def _routed(name: str, ip: str, prefix: int = 24, mtu=None, status=InterfaceStatus.UP) -> Interface:
    return Interface(
        name=name,
        interface_type=InterfaceType.GIGABIT_ETHERNET,
        switchport_mode=SwitchportMode.ROUTED,
        ip_address=ip,
        prefix_length=prefix,
        mtu=mtu,
        status=status,
    )


# ===========================================================================
# TestProblemModel
# ===========================================================================

class TestProblemModel:
    def test_problem_defaults_populated(self):
        p = Problem(
            rule_id="X_001",
            category=Category.L2,
            severity=Severity.HIGH,
            device_hostname="sw1",
            title="Test",
            description="desc",
            impact="impact",
            recommendation="rec",
        )
        assert p.id  # UUID generated
        assert p.evidence == {}
        assert p.interface is None
        assert p.detected_at is not None

    def test_problem_str(self):
        p = Problem(
            rule_id="L2_VLAN_001",
            category=Category.L2,
            severity=Severity.HIGH,
            device_hostname="sw1",
            interface="Gi0/1",
            title="Test",
            description="d",
            impact="i",
            recommendation="r",
        )
        s = str(p)
        assert "L2_VLAN_001" in s
        assert "sw1" in s
        assert "Gi0/1" in s

    def test_severity_enum_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.LOW.value == "low"

    def test_category_enum_values(self):
        assert Category.L2.value == "l2"
        assert Category.SECURITY.value == "security"


# ===========================================================================
# TestVLANMismatchRule  (L2_VLAN_001)
# ===========================================================================

class TestVLANMismatchRule:
    rule = VLANMismatchRule()

    def test_trunk_with_undefined_vlans_raises_problem(self):
        device = _device(
            interfaces=[_trunk("Gi0/1", trunk_vlans=[10, 20, 30])],
            vlans=[VLAN(vlan_id=10, name="MGMT"), VLAN(vlan_id=20, name="DATA")],
        )
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].rule_id == "L2_VLAN_001"
        assert 30 in problems[0].evidence["missing_vlans"]

    def test_trunk_all_vlans_defined_no_problem(self):
        device = _device(
            interfaces=[_trunk("Gi0/1", trunk_vlans=[10, 20])],
            vlans=[VLAN(vlan_id=10), VLAN(vlan_id=20)],
        )
        assert self.rule.check([device]) == []

    def test_no_trunk_interfaces_no_problem(self):
        device = _device(interfaces=[_access("Gi0/1")])
        assert self.rule.check([device]) == []

    def test_cross_device_native_vlan_mismatch(self):
        d1 = _device("sw1", interfaces=[_trunk("Gi0/1", trunk_vlans=[10, 20], native_vlan=1)])
        d2 = _device("sw2", interfaces=[_trunk("Gi0/1", trunk_vlans=[10], native_vlan=1)])
        problems = self.rule.check([d1, d2])
        rule_ids = [p.rule_id for p in problems]
        assert "L2_VLAN_001" in rule_ids

    def test_no_vlans_on_device_skips_check(self):
        device = _device(interfaces=[_trunk("Gi0/1", trunk_vlans=[10, 20])])
        assert self.rule.check([device]) == []


# ===========================================================================
# TestUnexpectedRootBridgeRule  (L2_STP_001)
# ===========================================================================

class TestUnexpectedRootBridgeRule:
    rule = UnexpectedRootBridgeRule()

    def test_access_switch_with_many_trunks_flagged(self):
        trunks = [_trunk(f"Gi0/{i}", status=InterfaceStatus.UP) for i in range(4)]
        device = _device("access-sw1", interfaces=trunks)
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_core_switch_with_many_trunks_ok(self):
        trunks = [_trunk(f"Gi0/{i}", status=InterfaceStatus.UP) for i in range(4)]
        device = _device("core-sw1", interfaces=trunks)
        assert self.rule.check([device]) == []

    def test_few_trunks_no_problem(self):
        trunks = [_trunk("Gi0/1", status=InterfaceStatus.UP), _trunk("Gi0/2", status=InterfaceStatus.UP)]
        device = _device("access-sw1", interfaces=trunks)
        assert self.rule.check([device]) == []

    def test_down_trunks_not_counted(self):
        trunks = [_trunk(f"Gi0/{i}", status=InterfaceStatus.DOWN) for i in range(5)]
        device = _device("access-sw1", interfaces=trunks)
        assert self.rule.check([device]) == []


# ===========================================================================
# TestPotentialLoopRule  (L2_STP_002)
# ===========================================================================

class TestPotentialLoopRule:
    rule = PotentialLoopRule()

    def test_redundant_trunks_no_lag_flagged(self):
        device = _device(interfaces=[
            _trunk("Gi0/1", trunk_vlans=[10, 20]),
            _trunk("Gi0/2", trunk_vlans=[10, 20]),
        ])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_redundant_trunks_with_lag_ok(self):
        device = _device(interfaces=[
            _trunk("Gi0/1", trunk_vlans=[10, 20], channel_group=1),
            _trunk("Gi0/2", trunk_vlans=[10, 20], channel_group=1),
        ])
        assert self.rule.check([device]) == []

    def test_single_trunk_no_problem(self):
        device = _device(interfaces=[_trunk("Gi0/1", trunk_vlans=[10, 20])])
        assert self.rule.check([device]) == []

    def test_different_vlan_sets_no_loop(self):
        device = _device(interfaces=[
            _trunk("Gi0/1", trunk_vlans=[10]),
            _trunk("Gi0/2", trunk_vlans=[20]),
        ])
        assert self.rule.check([device]) == []


# ===========================================================================
# TestLACPInconsistentRule  (L2_LACP_001)
# ===========================================================================

class TestLACPInconsistentRule:
    rule = LACPInconsistentRule()

    def test_mtu_mismatch_flagged(self):
        device = _device(interfaces=[
            _trunk("Gi0/1", channel_group=1, mtu=9000),
            _trunk("Gi0/2", channel_group=1, mtu=1500),
        ])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].rule_id == "L2_LACP_001"

    def test_consistent_members_ok(self):
        device = _device(interfaces=[
            _trunk("Gi0/1", channel_group=1, mtu=9000, speed=10000),
            _trunk("Gi0/2", channel_group=1, mtu=9000, speed=10000),
        ])
        assert self.rule.check([device]) == []

    def test_no_port_channel_no_problem(self):
        device = _device(interfaces=[_trunk("Gi0/1", mtu=1500), _trunk("Gi0/2", mtu=9000)])
        assert self.rule.check([device]) == []

    def test_speed_mismatch_flagged(self):
        device = _device(interfaces=[
            _trunk("Gi0/1", channel_group=2, speed=1000),
            _trunk("Gi0/2", channel_group=2, speed=10000),
        ])
        assert len(self.rule.check([device])) == 1


# ===========================================================================
# TestErrDisabledPortRule  (L2_PORT_001)
# ===========================================================================

class TestErrDisabledPortRule:
    rule = ErrDisabledPortRule()

    def test_admin_up_oper_down_flagged(self):
        iface = Interface(
            name="Gi0/1",
            interface_type=InterfaceType.GIGABIT_ETHERNET,
            admin_status=True,
            status=InterfaceStatus.DOWN,
        )
        device = _device(interfaces=[iface])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].interface == "Gi0/1"

    def test_admin_down_no_problem(self):
        iface = Interface(
            name="Gi0/1",
            interface_type=InterfaceType.GIGABIT_ETHERNET,
            admin_status=False,
            status=InterfaceStatus.ADMIN_DOWN,
        )
        device = _device(interfaces=[iface])
        assert self.rule.check([device]) == []

    def test_both_up_no_problem(self):
        device = _device(interfaces=[_trunk("Gi0/1", status=InterfaceStatus.UP)])
        assert self.rule.check([device]) == []


# ===========================================================================
# TestOSPFAreaMismatchRule  (L3_OSPF_001)
# ===========================================================================

class TestOSPFAreaMismatchRule:
    rule = OSPFAreaMismatchRule()

    def test_same_net_different_areas_flagged(self):
        d1 = _device("r1", ospf_processes=[
            OSPFProcess(process_id=1, networks=[OSPFNetwork(network="10.0.0.0", area="0")])
        ])
        d2 = _device("r2", ospf_processes=[
            OSPFProcess(process_id=1, networks=[OSPFNetwork(network="10.0.0.0", area="1")])
        ])
        problems = self.rule.check([d1, d2])
        assert len(problems) == 2
        assert all(p.rule_id == "L3_OSPF_001" for p in problems)

    def test_same_area_no_problem(self):
        d1 = _device("r1", ospf_processes=[
            OSPFProcess(process_id=1, networks=[OSPFNetwork(network="10.0.0.0", area="0")])
        ])
        d2 = _device("r2", ospf_processes=[
            OSPFProcess(process_id=1, networks=[OSPFNetwork(network="10.0.0.0", area="0")])
        ])
        assert self.rule.check([d1, d2]) == []

    def test_no_ospf_no_problem(self):
        device = _device()
        assert self.rule.check([device]) == []


# ===========================================================================
# TestOSPFMTUMismatchRule  (L3_OSPF_002)
# ===========================================================================

class TestOSPFMTUMismatchRule:
    rule = OSPFMTUMismatchRule()

    def test_different_mtu_same_area_flagged(self):
        d1 = _device("r1",
            interfaces=[_routed("Gi0/0", "10.0.0.1", mtu=1500)],
            ospf_processes=[OSPFProcess(process_id=1, networks=[
                OSPFNetwork(network="10.0.0.0", wildcard="0.0.0.255", area="0")
            ])],
        )
        d2 = _device("r2",
            interfaces=[_routed("Gi0/0", "10.0.0.2", mtu=9000)],
            ospf_processes=[OSPFProcess(process_id=1, networks=[
                OSPFNetwork(network="10.0.0.0", wildcard="0.0.0.255", area="0")
            ])],
        )
        problems = self.rule.check([d1, d2])
        assert len(problems) >= 1
        assert all(p.rule_id == "L3_OSPF_002" for p in problems)

    def test_same_mtu_no_problem(self):
        d1 = _device("r1",
            interfaces=[_routed("Gi0/0", "10.0.0.1", mtu=1500)],
            ospf_processes=[OSPFProcess(process_id=1, networks=[
                OSPFNetwork(network="10.0.0.0", wildcard="0.0.0.255", area="0")
            ])],
        )
        d2 = _device("r2",
            interfaces=[_routed("Gi0/0", "10.0.0.2", mtu=1500)],
            ospf_processes=[OSPFProcess(process_id=1, networks=[
                OSPFNetwork(network="10.0.0.0", wildcard="0.0.0.255", area="0")
            ])],
        )
        assert self.rule.check([d1, d2]) == []

    def test_no_ospf_no_problem(self):
        assert self.rule.check([_device()]) == []


# ===========================================================================
# TestBGPNeighborDownRule  (L3_BGP_001)
# ===========================================================================

class TestBGPNeighborDownRule:
    rule = BGPNeighborDownRule()

    def test_shutdown_neighbor_flagged(self):
        device = _device(bgp_processes=[
            BGPProcess(local_as=65000, neighbors=[
                BGPNeighbor(address="10.0.0.2", remote_as=65001, shutdown=True)
            ])
        ])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_active_neighbor_no_problem(self):
        device = _device(bgp_processes=[
            BGPProcess(local_as=65000, neighbors=[
                BGPNeighbor(address="10.0.0.2", remote_as=65001, shutdown=False)
            ])
        ])
        assert self.rule.check([device]) == []

    def test_no_bgp_no_problem(self):
        assert self.rule.check([_device()]) == []

    def test_multiple_neighbors_only_down_flagged(self):
        device = _device(bgp_processes=[
            BGPProcess(local_as=65000, neighbors=[
                BGPNeighbor(address="10.0.0.2", remote_as=65001, shutdown=False),
                BGPNeighbor(address="10.0.0.3", remote_as=65002, shutdown=True),
            ])
        ])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].evidence["neighbor_ip"] == "10.0.0.3"


# ===========================================================================
# TestVRFRouteLeakingRule  (L3_BGP_002)
# ===========================================================================

class TestVRFRouteLeakingRule:
    rule = VRFRouteLeakingRule()

    def test_rt_overlap_flagged(self):
        device = _device(vrfs=[
            VRF(name="CUST_A", rd="65000:100", rt_export=["65000:100"], rt_import=[]),
            VRF(name="CUST_B", rd="65000:200", rt_import=["65000:100"], rt_export=[]),
        ])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].rule_id == "L3_BGP_002"

    def test_no_rt_overlap_no_problem(self):
        device = _device(vrfs=[
            VRF(name="CUST_A", rd="65000:100", rt_export=["65000:100"], rt_import=[]),
            VRF(name="CUST_B", rd="65000:200", rt_import=["65000:200"], rt_export=[]),
        ])
        assert self.rule.check([device]) == []

    def test_single_vrf_no_problem(self):
        device = _device(vrfs=[
            VRF(name="DEFAULT", rt_import=["65000:1"], rt_export=["65000:1"])
        ])
        assert self.rule.check([device]) == []


# ===========================================================================
# TestAsymmetricRoutingRule  (L3_ROUTING_001)
# ===========================================================================

class TestAsymmetricRoutingRule:
    rule = AsymmetricRoutingRule()

    def test_unknown_next_hop_flagged(self):
        device = _device(static_routes=[
            Route(network="192.168.10.0", prefix_length=24, next_hop="10.0.0.99")
        ])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].rule_id == "L3_ROUTING_001"
        assert problems[0].severity == Severity.MEDIUM

    def test_known_next_hop_no_problem(self):
        d1 = _device("r1", static_routes=[
            Route(network="192.168.10.0", prefix_length=24, next_hop="10.0.0.2")
        ])
        d2 = _device("r2", interfaces=[_routed("Gi0/0", "10.0.0.2")])
        assert self.rule.check([d1, d2]) == []

    def test_no_static_routes_no_problem(self):
        assert self.rule.check([_device()]) == []


# ===========================================================================
# TestShadowedACLRule  (SEC_ACL_001)
# ===========================================================================

class TestShadowedACLRule:
    rule = ShadowedACLRule()

    def test_entry_after_permit_any_flagged(self):
        acl = ACL(
            name="ACL_TEST",
            acl_type=ACLType.EXTENDED,
            entries=[
                ACLEntry(sequence=10, action=ACLAction.PERMIT, source="any", destination="any", protocol="ip"),
                ACLEntry(sequence=20, action=ACLAction.DENY, source="10.0.0.0 0.0.0.255", destination="any", protocol="tcp"),
            ],
        )
        device = _device(acls=[acl])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].rule_id == "SEC_ACL_001"
        assert problems[0].evidence["shadowed_seq"] == 20

    def test_deny_any_also_shadows(self):
        acl = ACL(
            name="ACL_DENY",
            acl_type=ACLType.EXTENDED,
            entries=[
                ACLEntry(sequence=10, action=ACLAction.DENY, source="any", destination="any", protocol="ip"),
                ACLEntry(sequence=20, action=ACLAction.PERMIT, source="192.168.1.0 0.0.0.255", destination="any", protocol="ip"),
            ],
        )
        device = _device(acls=[acl])
        assert len(self.rule.check([device])) == 1

    def test_no_catch_all_no_problem(self):
        acl = ACL(
            name="ACL_OK",
            acl_type=ACLType.EXTENDED,
            entries=[
                ACLEntry(sequence=10, action=ACLAction.PERMIT, source="10.0.0.0 0.0.0.255", destination="any", protocol="ip"),
                ACLEntry(sequence=20, action=ACLAction.DENY, source="any", destination="any", protocol="ip"),
            ],
        )
        assert self.rule.check([_device(acls=[acl])]) == []

    def test_no_acls_no_problem(self):
        assert self.rule.check([_device()]) == []


# ===========================================================================
# TestAnyAnyPermitRule  (SEC_FW_001)
# ===========================================================================

class TestAnyAnyPermitRule:
    rule = AnyAnyPermitRule()

    def test_any_any_accept_flagged(self):
        policy = FirewallPolicy(
            policy_id=1,
            name="permit-all",
            source_addresses=["all"],
            destination_addresses=["all"],
            action=FirewallPolicyAction.ACCEPT,
            status=True,
        )
        device = _device(firewall_policies=[policy])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].severity == Severity.CRITICAL

    def test_any_any_deny_no_problem(self):
        policy = FirewallPolicy(
            policy_id=1,
            source_addresses=["all"],
            destination_addresses=["all"],
            action=FirewallPolicyAction.DENY,
            status=True,
        )
        assert self.rule.check([_device(firewall_policies=[policy])]) == []

    def test_specific_policy_no_problem(self):
        policy = FirewallPolicy(
            policy_id=1,
            source_addresses=["192.168.1.0/24"],
            destination_addresses=["10.0.0.0/8"],
            action=FirewallPolicyAction.ACCEPT,
            status=True,
        )
        assert self.rule.check([_device(firewall_policies=[policy])]) == []

    def test_disabled_policy_ignored(self):
        policy = FirewallPolicy(
            policy_id=1,
            source_addresses=["all"],
            destination_addresses=["all"],
            action=FirewallPolicyAction.ACCEPT,
            status=False,
        )
        assert self.rule.check([_device(firewall_policies=[policy])]) == []

    def test_empty_addresses_treated_as_any(self):
        policy = FirewallPolicy(
            policy_id=99,
            source_addresses=[],
            destination_addresses=[],
            action=FirewallPolicyAction.ACCEPT,
            status=True,
        )
        problems = self.rule.check([_device(firewall_policies=[policy])])
        assert len(problems) == 1


# ===========================================================================
# TestContradictoryACLRule  (SEC_ACL_002)
# ===========================================================================

class TestContradictoryACLRule:
    rule = ContradictoryACLRule()

    def test_contradictory_entries_flagged(self):
        acl = ACL(
            name="ACL_CONTRA",
            acl_type=ACLType.EXTENDED,
            entries=[
                ACLEntry(sequence=10, action=ACLAction.PERMIT, source="10.0.0.0 0.0.0.255", destination="any", protocol="ip"),
                ACLEntry(sequence=20, action=ACLAction.DENY, source="10.0.0.0 0.0.0.255", destination="any", protocol="ip"),
            ],
        )
        device = _device(acls=[acl])
        problems = self.rule.check([device])
        assert len(problems) == 1
        assert problems[0].rule_id == "SEC_ACL_002"

    def test_different_sources_no_contradiction(self):
        acl = ACL(
            name="ACL_OK",
            acl_type=ACLType.EXTENDED,
            entries=[
                ACLEntry(sequence=10, action=ACLAction.PERMIT, source="10.0.0.0 0.0.0.255", destination="any", protocol="ip"),
                ACLEntry(sequence=20, action=ACLAction.DENY, source="192.168.0.0 0.0.0.255", destination="any", protocol="ip"),
            ],
        )
        assert self.rule.check([_device(acls=[acl])]) == []

    def test_no_acls_no_problem(self):
        assert self.rule.check([_device()]) == []


# ===========================================================================
# TestRuleService
# ===========================================================================

class TestRuleService:
    def test_list_rules_returns_all_13(self):
        svc = RuleService()
        rules = svc.list_rules()
        assert len(rules) == 13
        rule_ids = [r["rule_id"] for r in rules]
        assert "L2_VLAN_001" in rule_ids
        assert "SEC_FW_001" in rule_ids

    def test_get_rule_info_known_rule(self):
        svc = RuleService()
        info = svc.get_rule_info("L2_PORT_001")
        assert info is not None
        assert info["rule_id"] == "L2_PORT_001"
        assert info["category"] == "l2"

    def test_get_rule_info_unknown_returns_none(self):
        svc = RuleService()
        assert svc.get_rule_info("UNKNOWN_999") is None

    def test_analyse_by_rule_id(self):
        svc = RuleService()
        iface = Interface(
            name="Gi0/1",
            interface_type=InterfaceType.GIGABIT_ETHERNET,
            admin_status=True,
            status=InterfaceStatus.DOWN,
        )
        device = _device(interfaces=[iface])
        problems = svc.analyse_by_rule([device], "L2_PORT_001")
        assert len(problems) == 1

    def test_analyse_by_unknown_rule_raises(self):
        svc = RuleService()
        with pytest.raises(ValueError, match="Unknown rule_id"):
            svc.analyse_by_rule([_device()], "FAKE_RULE")

    def test_analyse_by_category_l2_only(self):
        svc = RuleService()
        iface = Interface(
            name="Gi0/1",
            interface_type=InterfaceType.GIGABIT_ETHERNET,
            admin_status=True,
            status=InterfaceStatus.DOWN,
        )
        device = _device(interfaces=[iface])
        from ..models.problem import Category
        problems = svc.analyse_by_category([device], Category.L2)
        assert all(p.category == Category.L2 for p in problems)

    def test_summarise(self):
        svc = RuleService()
        iface = Interface(
            name="Gi0/1",
            interface_type=InterfaceType.GIGABIT_ETHERNET,
            admin_status=True,
            status=InterfaceStatus.DOWN,
        )
        device = _device(interfaces=[iface])
        problems = svc.analyse([device])
        summary = svc.summarise(problems)
        assert "total" in summary
        assert "by_severity" in summary
        assert "by_category" in summary
        assert summary["total"] == len(problems)

    def test_analyse_returns_critical_first(self):
        svc = RuleService()
        device = _device(bgp_processes=[
            BGPProcess(local_as=65000, neighbors=[
                BGPNeighbor(address="10.0.0.2", remote_as=65001, shutdown=True)
            ])
        ])
        iface = Interface(
            name="Gi0/1",
            interface_type=InterfaceType.GIGABIT_ETHERNET,
            admin_status=True,
            status=InterfaceStatus.DOWN,
        )
        device.interfaces.append(iface)
        problems = svc.analyse([device])
        if len(problems) >= 2:
            sev_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
            for i in range(len(problems) - 1):
                assert (
                    sev_order[problems[i].severity.value]
                    >= sev_order[problems[i + 1].severity.value]
                )
