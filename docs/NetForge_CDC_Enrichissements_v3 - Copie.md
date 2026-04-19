# NETWORK COPILOT PLATFORM
## NetForge Pro
### ENRICHISSEMENTS CAHIER DES CHARGES
**Version 3.0**

MODULE 10: Discovery Engine | MODULE 5: CLI Engine | CLI Unifie | Nomenclature Interfaces

*Avril 2026*

---

## MODULE 10 - DISCOVERY ENGINE
### Sonde Reseau Intelligente

### 10.1 Objectif

Creer une sonde reseau intelligente capable de :

1. Scanner automatiquement le reseau local
2. Decouvrir les equipements actifs
3. Identifier le constructeur et l'OS (fingerprinting)
4. Cartographier la topologie via LLDP/CDP
5. Adapter automatiquement le CLI et le parsing

### 10.2 Techniques de Decouverte

| Technique | Description | Outil | Priorite |
|---|---|---|---|
| Ping Sweep | Detection hosts actifs via ICMP | nmap, scapy | Basique |
| Port Scan | Detection services (22, 23, 443, 161) | nmap | Basique |
| SNMP | Recuperation sysDescr, sysName | PySNMP | Principal |
| SSH Banner | Detection via banniere SSH | Paramiko | Complementaire |
| LLDP/CDP | Decouverte topologie et voisins | Netmiko | Topologie |
| MAC OUI | Identification vendor via MAC | Base IEEE | Complementaire |

### 10.3 Device Fingerprinting

**Algorithme Multi-Sources** : Combine SNMP (50%), SSH Banner (30%), MAC OUI (20%) pour identifier le vendor avec un score de confiance.

| Vendor | Pattern SNMP | MAC OUI |
|---|---|---|
| Cisco IOS | Cisco IOS Software | 00:00:0C |
| Cisco NX-OS | Cisco Nexus Operating System | 00:1A:2B |
| Huawei VRP | Huawei.*VRP | 00:E0:FC |
| Fortinet | FortiGate | 00:09:0F |
| Arista EOS | Arista.*EOS | 00:1C:73 |

### 10.4 Workflow Discovery

```
1. INPUT: Plage IP (192.168.1.0/24) + Credentials
          |
          v
2. SCAN RESEAU --> Detection hosts actifs + ports ouverts
          |
          v
3. SNMP DISCOVERY --> sysDescr, sysName, ifDescr
          |
          v
4. FINGERPRINTING --> Identification vendor/OS (confidence score)
          |
          v
5. SSH CONNECTION --> Collecte config + LLDP/CDP neighbors
          |
          v
6. GRAPH DATABASE --> Creation nodes + relations
          |
          v
7. CLI PROFILE --> Chargement profil constructeur adapte
```

### 10.5 Auto-Learning Network

Fonctionnalite avancee :

- Demarre d'un device "seed"
- Recupere ses voisins LLDP/CDP
- Decouvre recursivement (max N hops)
- Cartographie automatique du reseau

### 10.6 API Endpoints

| Methode | Endpoint | Description |
|---|---|---|
| POST | /api/v1/discovery/scan | Lance un scan reseau |
| GET | /api/v1/discovery/scan/{id} | Statut du scan |
| GET | /api/v1/discovery/devices | Liste devices decouverts |
| POST | /api/v1/discovery/auto-discover | Auto-learning depuis seed |

---

## ENRICHISSEMENT MODULE 5 - CLI ENGINE

### 5.X.1 Architecture Hybride (3 Modes)

| Mode | Description | Usage |
|---|---|---|
| SSH Proxy | Connexion SSH reelle via Netmiko | Production (recommande) |
| Simulator | CLI simule sur modele JSON/SoT | Formation, dry-run |
| AI-Assisted | Auto-completion + suggestions IA | Assistance intelligente |

### 5.X.2 Profils CLI par Constructeur

Structure des profils YAML :

```
cli_profiles/
+-- cisco_ios.yaml
+-- cisco_nxos.yaml
+-- huawei_vrp.yaml
+-- fortinet_fortios.yaml
+-- arista_eos.yaml
```

### 5.X.3 State Machine CLI

Gestion des transitions entre modes :

```
User Exec (>)
     |
     v enable
Privileged Exec (#)
     |
     v configure terminal
Global Config (config)#
     |
     +---> interface Gi0/1 ---> Interface Config (config-if)#
     |
     +---> router ospf 1   ---> Router Config (config-router)#
```

### 5.X.4 Differences Cles entre Constructeurs

| Concept | Cisco | Huawei | Fortinet |
|---|---|---|---|
| Negation | no | undo | unset |
| Affichage | show | display | get |
| Sortie config | exit / end | quit / return | end / abort |
| VLAN SVI | Vlan10 | Vlanif10 | N/A |
| LAG | Port-channel1 | Eth-Trunk1 | agg1 |

---

## CLI UNIFIE - KILLER FEATURE

> **CONCEPT** : L'utilisateur tape UNE commande universelle, le systeme traduit automatiquement vers chaque constructeur.

### Exemple

```
netforge> create vlan 10 name USERS

===================================================================
CISCO IOS:            | HUAWEI VRP:          | FORTINET:
----------------------|----------------------|-----------------------
vlan 10               | vlan 10              | config system interface
 name USERS           |  description USERS   |  edit "USERS"
                      |                      |   set vlanid 10
                      |                      |  next
                      |                      | end
===================================================================
```

### Commandes Unifiees Principales

| Commande Unifiee | Description |
|---|---|
| `create vlan {id} name {name}` | Cree un VLAN |
| `set interface {iface} ip {ip}/{prefix}` | Configure IP interface |
| `create lag {id} members {ports}` | Cree un LAG |
| `set interface {iface} mode {access/trunk}` | Configure mode switchport |
| `create static-route {prefix} nexthop {ip}` | Ajoute route statique |
| `enable ospf {process} area {area} interface {iface}` | Active OSPF |

---

## NOMENCLATURE INTERFACES

*Document de reference : NetForge_Nomenclature_Interfaces.pdf*

| Element | Cisco | Huawei | Arista |
|---|---|---|---|
| 1 Gbps | GigabitEthernet0/1 | GE0/0/1 | Ethernet1 |
| 10 Gbps | TenGigabitEthernet1/0/1 | 10GE1/0/1 | Ethernet1 |
| VLAN SVI | Vlan10 | Vlanif10 | Vlan10 |
| LAG | Port-channel1 | Eth-Trunk1 | Port-Channel1 |
| Format | slot/module/port | slot/subcard/port (3 niveaux) | port simple |

---

## MISE A JOUR ROADMAP

| Phase | Modules | Duree |
|---|---|---|
| Phase 1 (MVP) | Parser (Cisco+Fortinet), Rule Engine, API Backend, Frontend basique | 3-4 mois |
| Phase 2 | Discovery Engine (basique), Parser (Huawei+Arista), Graph DB, CLI SSH Proxy | 2-3 mois |
| Phase 3 | CLI Simule, AI Engine, Auto-completion, Correction semi-auto | 3-4 mois |
| Phase 4 | CLI Unifie, Discovery Auto-learning, Securite L4-L7, Reporting DSI | 2-3 mois |

---

## RECAPITULATIF DES AJOUTS

| Module | Statut | Description |
|---|---|---|
| Module 10 - Discovery Engine | NOUVEAU | Sonde reseau, fingerprinting, auto-discovery |
| Module 5 - CLI Engine | ENRICHI | 3 modes, profils YAML, state machine |
| CLI Unifie | NOUVEAU | Killer feature - commandes universelles |
| Nomenclature | NOUVEAU | Tables d'equivalence + module Python |

---

*Network Copilot Platform - NetForge Pro*
*Enrichissements CDC v3.0 - Avril 2026*
