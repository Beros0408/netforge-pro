# Cisco Catalyst 9200 Series

## Identification
```yaml
vendor: cisco
vendor_display: Cisco Systems
family: catalyst_9200
os: IOS-XE
type: switch
layer: L2/L3
icon_category: switch_rack_1u
color_hex: "#1BA0D7"
snmp_pattern: "Cisco IOS.*Catalyst.*9200"
ssh_banner_pattern: "cisco C9200"
```

---

## Modèles et Nombre de Ports

| Modèle | Ports Accès | Vitesse Accès | Ports Uplink | PoE | mGig | Stacking |
|---|---|---|---|---|---|---|
| C9200-24T | 24 | 1G data | Modulaire | Non | Non | StackWise-160 |
| C9200-24P | 24 | 1G | Modulaire | PoE+ 30W | Non | StackWise-160 |
| C9200-24PXG | 24 | 8x10G + 16x1G | Modulaire | PoE+ 30W | 10G (8 ports) | StackWise-160 |
| C9200-48T | 48 | 1G data | Modulaire | Non | Non | StackWise-160 |
| C9200-48P | 48 | 1G | Modulaire | PoE+ 30W | Non | StackWise-160 |
| C9200-48PL | 48 | 1G | Modulaire | PoE+ partiel | Non | StackWise-160 |
| C9200-48PXG | 48 | 8x10G + 40x1G | Modulaire | PoE+ 30W | 10G (8 ports) | StackWise-160 |
| C9200L-24T-4G | 24 | 1G data | 4x1G fixe | Non | Non | StackWise-80 |
| C9200L-24P-4G | 24 | 1G | 4x1G fixe | PoE+ 30W | Non | StackWise-80 |
| C9200L-48T-4G | 48 | 1G data | 4x1G fixe | Non | Non | StackWise-80 |
| C9200L-48P-4G | 48 | 1G | 4x1G fixe | PoE+ 30W | Non | StackWise-80 |
| C9200L-24T-4X | 24 | 1G data | 4x10G fixe | Non | Non | StackWise-80 |
| C9200L-24P-4X | 24 | 1G | 4x10G fixe | PoE+ 30W | Non | StackWise-80 |
| C9200L-48T-4X | 48 | 1G data | 4x10G fixe | Non | Non | StackWise-80 |
| C9200L-48P-4X | 48 | 1G | 4x10G fixe | PoE+ 30W | Non | StackWise-80 |
| C9200CX-12T-2X2G | 12 | 1G data | 2x10G+2x1G fixe | Non | Non | Non |
| C9200CX-12P-2X2G | 12 | 1G | 2x10G+2x1G fixe | PoE+ 30W | Non | Non |
| C9200CX-8P-2X2G | 8 | 1G | 2x10G+2x1G fixe | PoE+ 30W | Non | Non |
| C9200CX-8UXG-2X | 8 | 4x10G+4x1G | 2x10G fixe | UPOE 60W | 10G (4 ports) | Non |

---

## Modules Uplink (Modèles C9200 modulaires uniquement)

| Référence | Ports | Vitesse | Connecteur | Type |
|---|---|---|---|---|
| C9200-NM-4G | 4 | 1G | SFP | Cuivre/Fibre |
| C9200-NM-4X | 4 | 1G/10G | SFP+ | Cuivre/Fibre |
| C9200-NM-2Y | 2 | 25G | SFP28 | Fibre |
| C9200-NM-2Q | 2 | 40G | QSFP+ | Fibre |
| C9200-NM-BLANK | - | - | - | Pas de module |

---

## Types de Câbles Supportés

| Type | Connecteur | Vitesse Max | Médium | Couleur Affichage | Style Affichage |
|---|---|---|---|---|---|
| RJ45 Cuivre | RJ-45 | 10/100/1000 | Cat5E UTP | #8B4513 (Marron) | Pointillé `- - -` |
| SFP Cuivre | RJ-45 | 1G | Cat5E UTP | #8B4513 (Marron) | Pointillé `- - -` |
| SFP Fibre Multimode | LC | 1G | OM3/OM4 | #22C55E (Vert clair) | Trait plein |
| SFP Fibre Monomode | LC | 1G | OS2 | #16A34A (Vert foncé) | Trait plein |
| SFP+ Fibre MM | LC | 10G | OM3/OM4 | #22C55E (Vert clair) | Trait épais |
| SFP+ Fibre SM | LC | 10G | OS2 | #16A34A (Vert foncé) | Trait épais |
| SFP28 | LC | 25G | OS2 | #15803D (Vert vif) | Trait épais |
| QSFP+ | MPO | 40G | OM4/OS2 | #166534 (Vert intense) | Trait très épais |
| StackWise | Cuivre propriétaire | 160Gbps/80Gbps | Câble Cisco | #F59E0B (Orange) | Trait double |

---

## Modules SFP Compatibles

| Référence Cisco | Type | Vitesse | Distance Max | Médium | Connecteur |
|---|---|---|---|---|---|
| GLC-T= | Cuivre | 1G | 100m | RJ-45 | RJ-45 |
| GLC-SX-MMD= | Fibre MM | 1G | 550m | OM2+ | LC |
| GLC-LH-SMD= | Fibre SM | 1G | 10km | OS1/OS2 | LC |
| GLC-ZX-SMD= | Fibre SM | 1G | 70km | OS2 | LC |
| SFP-10G-SR= | Fibre MM | 10G | 300m | OM3/OM4 | LC |
| SFP-10G-LR= | Fibre SM | 10G | 10km | OS2 | LC |
| SFP-10G-LRM= | Fibre MM | 10G | 220m | OM1/OM2 | LC |
| SFP-10G-ER= | Fibre SM | 10G | 40km | OS2 | LC |
| SFP-25G-SR-S= | Fibre MM | 25G | 100m | OM4 | LC |
| QSFP-40G-SR4= | Fibre MM | 40G | 150m | OM3/OM4 | MPO |
| QSFP-40G-LR4= | Fibre SM | 40G | 10km | OS2 | LC |

---

## Détection Automatique par NetForge Pro

```yaml
detection:
  snmp:
    oid_sysdescr: "1.3.6.1.2.1.1.1.0"
    pattern: "Cisco IOS.*Version.*catalyst.*9200"
    confidence: 50%
  ssh_banner:
    pattern: ["cisco C9200", "Catalyst 9200", "C9200-"]
    confidence: 30%
  mac_oui:
    prefixes: ["00:00:0C", "00:1A:2B", "00:17:DF", "68:EF:BD"]
    confidence: 20%
  model_extraction:
    snmp_oid: "1.3.6.1.2.1.47.1.1.1.1.13"
    ssh_command: "show version | include cisco C9200"
    regex: "cisco (C9200[A-Z0-9\-]+)"
  port_count:
    snmp_oid: "1.3.6.1.2.1.2.1.0"
    description: "ifNumber - nombre total d'interfaces"
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
    C9200-24T:
      access_ports: 24
      uplink_ports: 4
      layout: "2 rangées de 12 + module droit"
    C9200-24P:
      access_ports: 24
      uplink_ports: 4
      poe_indicator: true
      layout: "2 rangées de 12 + module droit"
    C9200-48T:
      access_ports: 48
      uplink_ports: 4
      layout: "2 rangées de 24 + module droit"
    C9200-48P:
      access_ports: 48
      uplink_ports: 4
      poe_indicator: true
      layout: "2 rangées de 24 + module droit"
    C9200CX-12P-2X2G:
      access_ports: 12
      uplink_ports: 4
      form_factor: compact
      layout: "1 rangée de 12 + 4 SFP"

  port_led_colors:
    up: "#22C55E"
    down: "#EF4444"
    err_disabled: "#F97316"
    admin_down: "#6B7280"
    poe_active: "#3B82F6"
```

---

## Performance

| Modèle | Switching | Forwarding | MAC Table | VLAN | VRF | Routes IPv4 |
|---|---|---|---|---|---|---|
| C9200-24T | 128 Gbps | 95 Mpps | 32,000 | 4094 | Non (Essentials) | 14,000 |
| C9200-24P | 128 Gbps | 95 Mpps | 32,000 | 4094 | Non | 14,000 |
| C9200-48T | 176 Gbps | 131 Mpps | 32,000 | 4094 | Non | 14,000 |
| C9200-48P | 176 Gbps | 131 Mpps | 32,000 | 4094 | Non | 14,000 |
| C9200-48PXG | 400 Gbps | 298 Mpps | 32,000 | 4094 | Oui (Advantage) | 14,000 |
| C9200L-48P-4X | 176 Gbps | 131 Mpps | 16,000 | 4094 | Non | 11,000 |
| C9200CX-12P | 68 Gbps | 51 Mpps | 32,000 | 4094 | Non | 14,000 |

---

## Dimensions Physiques

| Modèle | H x L x P (pouces) | Poids | Format |
|---|---|---|---|
| C9200-24T | 1.73 x 17.5 x 13.8 | 5.0 kg | 1U Rack |
| C9200-24P | 1.73 x 17.5 x 13.8 | 5.5 kg | 1U Rack |
| C9200-48T | 1.73 x 17.5 x 13.8 | 5.0 kg | 1U Rack |
| C9200-48P | 1.73 x 17.5 x 13.8 | 5.5 kg | 1U Rack |
| C9200L-24T-4G | 1.73 x 17.5 x 11.3 | 4.35 kg | 1U Rack |
| C9200L-48P-4X | 1.73 x 17.5 x 11.3 | 4.80 kg | 1U Rack |
| C9200CX-12P-2X2G | 1.73 x 10.6 x 9.6 | 2.99 kg | Compact |

---

## Alimentation PoE

| Modèle | Alim Primaire | PoE Dispo (1 alim) | PoE Dispo (2 alim) |
|---|---|---|---|
| C9200-24P | PWR-C6-600WAC | 370W | 740W |
| C9200-48P | PWR-C6-1KWAC | 740W | 1440W |
| C9200-48PXG | PWR-C6-1KWAC | 740W | 1440W |
| C9200CX-12P | 315W AC interne | 240W | N/A |

---

## Fiabilité (MTBF)

| Modèle | MTBF (heures) | MTBF (années) |
|---|---|---|
| C9200-24T | 587,800 | ~67 ans |
| C9200-24P | 422,310 | ~48 ans |
| C9200-48T | 571,440 | ~65 ans |
| C9200-48P | 375,570 | ~43 ans |
| C9200CX-12T | 960,180 | ~110 ans |

---

## Protocols et Standards Supportés

```yaml
layer2:
  - 802.1Q VLAN (4094 VLANs)
  - 802.1w RSTP
  - 802.1s MSTP
  - 802.3ad LACP (EtherChannel)
  - 802.1AE MACsec 128-bit (9200) / 256-bit (9200CX)
  - 802.1X authentification
  - CDP / LLDP
  - STP BPDU Guard / Root Guard
  - Storm Control
  - Port Security

layer3:
  - Static Routing
  - OSPF (Essentials: 1000 routes / Advantage: complet)
  - EIGRP (Advantage uniquement)
  - BGP (9200CX uniquement, IOS-XE 17.13+)
  - VRF (Advantage uniquement)
  - VXLAN (Advantage uniquement)
  - PIM multicast

management:
  - CLI (SSH/Telnet/Console)
  - SNMP v1/v2c/v3
  - NETCONF / RESTCONF / YANG
  - Streaming Telemetry
  - Cisco Catalyst Center (ex-DNA Center)
  - Meraki Dashboard
  - WebUI intégré
  - Plug and Play (PnP)
```

---

## Informations pour l'Ingénieur Réseau

```yaml
use_case:
  role: "Switch d'accès enterprise (campus/branch)"
  position_reseau: "Couche Accès (Access Layer)"
  ideal_pour:
    - Déploiements Wi-Fi 6/6E (PoE+ jusqu'à 30W)
    - IoT et endpoints avec 802.1X
    - SD-Access avec Cisco ISE
    - Branch office standardisée

points_attention:
  - "C9200 modulaire = uplinks remplaçables sur site"
  - "C9200L = uplinks fixés à la commande (non remplaçable)"
  - "C9200CX = format compact, fanless, alimentation par PoE possible (802.3bt)"
  - "Mixed stacking impossible entre C9200 et C9200L"
  - "VRF et VXLAN nécessitent licence Network Advantage"
  - "BGP uniquement sur C9200CX avec IOS-XE 17.13+"

compatibilite_sfp:
  referentiel: "https://tmgmatrix.cisco.com"
  note: "Vérifier compatibilité SFP avant commande"
```
