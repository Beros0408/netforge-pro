# Cisco Catalyst 9300 Series

## Identification
```yaml
vendor: cisco
vendor_display: Cisco Systems
family: catalyst_9300
os: IOS-XE
type: switch
layer: L2/L3
icon_category: switch_rack_1u
color_hex: "#1BA0D7"
snmp_pattern: "Cisco IOS.*Catalyst.*9300"
ssh_banner_pattern: "cisco C9300"
```

---

## Modèles et Nombre de Ports

| Modèle | Ports Accès | Vitesse Accès | Uplinks | PoE | mGig | Stacking | ASIC |
|---|---|---|---|---|---|---|---|
| C9300-24T | 24 | 1G data | Modulaire | Non | Non | StackWise-480 | UADP 2.0 |
| C9300-24P | 24 | 1G | Modulaire | PoE+ 30W | Non | StackWise-480 | UADP 2.0 |
| C9300-24U | 24 | 1G | Modulaire | UPOE 60W | Non | StackWise-480 | UADP 2.0 |
| C9300-24UX | 24 | 8x mGig + 16x1G | Modulaire | UPOE 60W | 10G (8 ports) | StackWise-480 | UADP 2.0 |
| C9300-48T | 48 | 1G data | Modulaire | Non | Non | StackWise-480 | UADP 2.0 |
| C9300-48P | 48 | 1G | Modulaire | PoE+ 30W | Non | StackWise-480 | UADP 2.0 |
| C9300-48U | 48 | 1G | Modulaire | UPOE 60W | Non | StackWise-480 | UADP 2.0 |
| C9300-48UN | 48 | 5G mGig | Modulaire | UPOE 60W | 5G (48 ports) | StackWise-480 | UADP 2.0 |
| C9300-48UXM | 48 | 48x mGig | Modulaire | UPOE 60W | 10G (48 ports) | StackWise-480 | UADP 2.0 |
| C9300X-48HX | 48 | 10G mGig (90W) | Modulaire | UPOE+ 90W | 10G (48 ports) | StackWise-1T | UADP 2.0sec |
| C9300X-48TX | 48 | 10G mGig data | Modulaire | Non | 10G (48 ports) | StackWise-1T | UADP 2.0sec |
| C9300L-24T-4G | 24 | 1G data | 4x1G fixe | Non | Non | StackWise-320 | UADP 2.0 |
| C9300L-24P-4G | 24 | 1G | 4x1G fixe | PoE+ 30W | Non | StackWise-320 | UADP 2.0 |
| C9300L-48T-4G | 48 | 1G data | 4x1G fixe | Non | Non | StackWise-320 | UADP 2.0 |
| C9300L-48P-4G | 48 | 1G | 4x1G fixe | PoE+ 30W | Non | StackWise-320 | UADP 2.0 |
| C9300L-48T-4X | 48 | 1G data | 4x10G fixe | Non | Non | StackWise-320 | UADP 2.0 |
| C9300L-48P-4X | 48 | 1G | 4x10G fixe | PoE+ 30W | Non | StackWise-320 | UADP 2.0 |

---

## Modules Uplink (Modèles C9300/C9300X modulaires)

| Référence | Ports | Vitesse | Connecteur | Compatible |
|---|---|---|---|---|
| C9300-NM-4G | 4 | 1G | SFP | C9300 |
| C9300-NM-4M | 4 | 1G/2.5G/5G/10G | SFP (mGig) | C9300 |
| C9300-NM-8X | 8 | 1G/10G | SFP+ | C9300 |
| C9300-NM-2Q | 2 | 40G | QSFP+ | C9300 |
| C9300-NM-2Y | 2 | 1G/10G/25G | SFP28 | C9300 |
| C9300X-NM-8M | 8 | 1G/10G mGig | RJ-45 | C9300X |
| C9300X-NM-8Y | 8 | 1G/10G/25G | SFP28 | C9300X |
| C9300X-NM-2C | 2 | 40G/100G | QSFP28 | C9300X |
| C9300X-NM-4C | 4 | 40G/100G | QSFP28 | C9300X |

---

## Types de Câbles Supportés

| Type | Connecteur | Vitesse Max | Médium | Couleur Affichage | Style Affichage |
|---|---|---|---|---|---|
| RJ45 Cuivre | RJ-45 | 10/100/1000 | Cat5E UTP | #8B4513 (Marron) | Pointillé `- - -` |
| RJ45 Cuivre mGig | RJ-45 | 2.5G/5G/10G | Cat6A UTP | #A16207 (Marron clair) | Pointillé épais |
| SFP Cuivre | RJ-45 | 1G | Cat5E UTP | #8B4513 (Marron) | Pointillé `- - -` |
| SFP Fibre MM | LC | 1G | OM3/OM4 | #22C55E (Vert clair) | Trait plein |
| SFP Fibre SM | LC | 1G | OS2 | #16A34A (Vert foncé) | Trait plein |
| SFP+ Fibre MM | LC | 10G | OM3/OM4 | #22C55E (Vert clair) | Trait épais |
| SFP+ Fibre SM | LC | 10G | OS2 | #16A34A (Vert foncé) | Trait épais |
| SFP28 | LC | 25G | OS2 | #15803D (Vert vif) | Trait épais |
| QSFP+ | MPO | 40G | OM4/OS2 | #166534 (Vert intense) | Trait très épais |
| QSFP28 | MPO/LC | 100G | OS2 | #14532D (Vert foncé) | Trait très épais |
| StackWise-480 | Cuivre propriétaire | 480 Gbps | Câble Cisco | #F59E0B (Orange) | Trait double |
| StackWise-1T | Cuivre propriétaire | 1 Tbps | Câble Cisco | #D97706 (Orange vif) | Trait double épais |
| StackPower | Propriétaire | Électrique | Câble Cisco | #DC2626 (Rouge) | Trait rouge |

---

## Modules SFP Compatibles

| Référence Cisco | Type | Vitesse | Distance Max | Médium | Connecteur |
|---|---|---|---|---|---|
| GLC-T= | Cuivre | 1G | 100m | RJ-45 | RJ-45 |
| GLC-SX-MMD= | Fibre MM | 1G | 550m | OM2+ | LC |
| GLC-LH-SMD= | Fibre SM | 1G | 10km | OS1/OS2 | LC |
| SFP-10G-SR= | Fibre MM | 10G | 300m | OM3/OM4 | LC |
| SFP-10G-LR= | Fibre SM | 10G | 10km | OS2 | LC |
| SFP-25G-SR-S= | Fibre MM | 25G | 100m | OM4 | LC |
| SFP-25G-LR-S= | Fibre SM | 25G | 10km | OS2 | LC |
| QSFP-40G-SR4= | Fibre MM | 40G | 150m | OM3/OM4 | MPO |
| QSFP-40G-LR4= | Fibre SM | 40G | 10km | OS2 | LC |
| QSFP-100G-SR4-S= | Fibre MM | 100G | 100m | OM4 | MPO |
| QSFP-100G-LR4-S= | Fibre SM | 100G | 10km | OS2 | LC |

---

## Détection Automatique par NetForge Pro

```yaml
detection:
  snmp:
    oid_sysdescr: "1.3.6.1.2.1.1.1.0"
    pattern: "Cisco IOS.*Version.*[Cc]atalyst.*9300"
    confidence: 50%
  ssh_banner:
    pattern: ["cisco C9300", "Catalyst 9300", "C9300-", "C9300X-"]
    confidence: 30%
  mac_oui:
    prefixes: ["00:00:0C", "00:1A:2B", "A0:EC:F9", "34:DB:FD"]
    confidence: 20%
  model_extraction:
    ssh_command: "show version | include cisco C9300"
    regex: "cisco (C9300[X]?[A-Z0-9\-]+)"
  port_count:
    snmp_oid: "1.3.6.1.2.1.2.1.0"
  stack_detection:
    ssh_command: "show switch"
    note: "Détecter si switch stacké (plusieurs membres)"
```

---

## Représentation Visuelle dans NetForge Pro

```yaml
visual:
  icon_type: switch_rack_1u
  color_primary: "#1BA0D7"
  color_secondary: "#005073"
  rack_height: 1U

  port_layout:
    C9300-24T:
      access_ports: 24
      uplink_ports: 8
      layout: "2 rangées de 12 + module droit 8 ports"
    C9300-24P:
      access_ports: 24
      uplink_ports: 8
      poe_indicator: true
      layout: "2 rangées de 12 + module droit 8 ports"
    C9300-48T:
      access_ports: 48
      uplink_ports: 8
      layout: "2 rangées de 24 + module droit 8 ports"
    C9300-48P:
      access_ports: 48
      uplink_ports: 8
      poe_indicator: true
      layout: "2 rangées de 24 + module droit 8 ports"
    C9300X-48HX:
      access_ports: 48
      uplink_ports: 4
      poe_indicator: true
      poe_type: "UPOE+ 90W"
      layout: "2 rangées de 24 mGig + module droit"
      badge: "UPOE+"

  stack_visual:
    enabled: true
    max_members: 8
    display: "Afficher les membres du stack comme un bloc unique"
    label: "Stack {N} membres — {total_ports} ports total"

  port_led_colors:
    up: "#22C55E"
    down: "#EF4444"
    err_disabled: "#F97316"
    admin_down: "#6B7280"
    poe_active: "#3B82F6"
    upoe_active: "#8B5CF6"
    mgig_active: "#06B6D4"
```

---

## Performance

| Modèle | Switching | Forwarding | MAC Table | Routes IPv4 | VLAN | DRAM | Flash |
|---|---|---|---|---|---|---|---|
| C9300-24T | 208 Gbps | 155 Mpps | 32,000 | 32,000 | 4094 | 8 GB | 16 GB |
| C9300-48T | 256 Gbps | 190 Mpps | 32,000 | 32,000 | 4094 | 8 GB | 16 GB |
| C9300-48P | 256 Gbps | 190 Mpps | 32,000 | 32,000 | 4094 | 8 GB | 16 GB |
| C9300-48UXM | 848 Gbps | 631 Mpps | 32,000 | 32,000 | 4094 | 8 GB | 16 GB |
| C9300X-48HX | 1760 Gbps | 1309 Mpps | 32,000 | 39,000 | 4094 | 16 GB | 16 GB |
| C9300X-48TX | 1760 Gbps | 1309 Mpps | 32,000 | 39,000 | 4094 | 16 GB | 16 GB |

---

## Dimensions Physiques

| Modèle | H x L x P (pouces) | Format | MTBF (heures) |
|---|---|---|---|
| C9300-24T | 1.73 x 17.5 x 16.1 | 1U Rack | 314,790 |
| C9300-48T | 1.73 x 17.5 x 16.1 | 1U Rack | 305,870 |
| C9300X-48HX | 1.73 x 17.5 x 19.0 | 1U Rack | 185,420 |
| C9300X-48TX | 1.73 x 17.5 x 19.0 | 1U Rack | 206,480 |

---

## Stacking

| Type | Bande Passante | Membres Max | Ports Accès Max | PoE Ports Max |
|---|---|---|---|---|
| StackWise-1T (C9300X) | 1 Tbps | 8 | 384 | 384 UPOE+ 90W |
| StackWise-480 (C9300) | 480 Gbps | 8 | 384 | 384 UPOE |
| StackWise-320 (C9300L) | 320 Gbps | 8 | 384 | 384 PoE+ |

```yaml
stacking_note:
  - "C9300X peut stack avec C9300 (bandwidth réduit à 480G)"
  - "C9300L ne peut PAS stack avec C9300 ou C9300X"
  - "StackPower partage l'alimentation entre membres du stack"
  - "Mixed stacking nécessite même niveau de licence"
```

---

## Alimentation PoE

| Modèle | Alim Défaut | PoE Max (1 alim) | PoE Max (2 alim) | Type PoE |
|---|---|---|---|---|
| C9300-24P | PWR-C1-715WAC | 437W | 875W | PoE+ 30W |
| C9300-48P | PWR-C1-715WAC | 437W | 875W | PoE+ 30W |
| C9300-24U | PWR-C1-715WAC | 437W | 875W | UPOE 60W |
| C9300-48U | PWR-C1-1100WAC | 875W | 1750W | UPOE 60W |
| C9300X-48HX | PWR-C1-1100WAC-P | 2490W | 3290W | UPOE+ 90W |

---

## Protocoles et Standards Supportés

```yaml
layer2:
  - 802.1Q VLAN (4094 VLANs)
  - 802.1w RSTP / 802.1s MSTP
  - 802.3ad LACP (EtherChannel cross-stack)
  - 802.1AE MACsec 256-bit
  - 802.1X / 802.1X-Rev
  - CDP / LLDP
  - STP BPDU Guard / Root Guard / PortFast
  - Dynamic ARP Inspection (DAI)
  - DHCP Snooping / IP Source Guard
  - 802.1ba AVB
  - PTP IEEE 1588v2

layer3:
  - Static Routing
  - OSPF (complet)
  - EIGRP
  - IS-IS
  - BGP
  - VRF / VRF-lite
  - VXLAN / LISP
  - PIM multicast (Sparse/SSM)
  - IPv6 dual-stack hardware
  - uRPF
  - NAT/PAT statique et dynamique

security:
  - IPsec 100G hardware (C9300X uniquement)
  - Encrypted Traffic Analytics (ETA)
  - Cisco TrustSec (SGT)
  - MACsec 256-bit
  - Secure Boot hardware
  - Cisco ASAc firewall (virtuel)

management:
  - CLI SSH/Console
  - SNMP v1/v2c/v3 (liste exhaustive de MIBs)
  - NETCONF / RESTCONF / YANG
  - Python scripting (on-box)
  - Streaming Telemetry model-driven
  - Container hosting (applications tierces)
  - Cisco Catalyst Center (ex-DNA Center)
  - Meraki Dashboard
  - Plug and Play (PnP)
  - ThousandEyes (avec licence Advantage)
```

---

## Informations pour l'Ingénieur Réseau

```yaml
use_case:
  role: "Switch d'accès enterprise premium (campus/branch)"
  position_reseau: "Couche Accès ou Distribution"
  ideal_pour:
    - Wi-Fi 6/6E haute densité (UPOE/UPOE+)
    - IoT et OT avec isolation (VXLAN/SGT)
    - SD-Access enterprise
    - Déploiements mGig pour AP haute performance
    - Data center edge avec C9300X (100G IPsec)

vs_9200:
  - "9300 = accès premium / 9200 = accès standard"
  - "9300 supporte UPOE (60W) et UPOE+ (90W)"
  - "9300X = hardware IPsec 100G (unique sur access)"
  - "9300 a plus de mémoire (8GB/16GB vs 4GB)"
  - "9300 supporte plus de routes IPv4 (32K vs 14K)"
  - "9300 stacking plus performant (480G/1T vs 160G/80G)"

points_attention:
  - "C9300X-NM-4C (4x100G) = connectivité spine très haute densité"
  - "StackWise-1T nécessite câbles STACK-T1-* (différent du 9200)"
  - "Mixed stack 9300X+9300 possible mais bandwidth limité à 480G"
  - "IPsec hardware C9300X nécessite commande clé HSEC séparée"
  - "AppGig port (2x10G) pour hosting applications sur C9300X"
  - "Cat5E UTP suffisant pour mGig jusqu'à 2.5G/5G; Cat6A pour 10G"

compatibilite_sfp:
  referentiel: "https://tmgmatrix.cisco.com"
  note: "SFP 9300 compatibles avec 9200 — vérifier avant déploiement"
```
