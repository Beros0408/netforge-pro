# NETWORK COPILOT PLATFORM
## NetForge Pro
### PROMPTS DE DÉVELOPPEMENT
**Guide Complet pour les Développeurs**

Version 2.0 - Avril 2026 | Document de Référence Technique

---

## TABLE DES MATIÈRES

1. Introduction et Guide d'Utilisation
2. Architecture Globale et Dépendances
3. PROMPT MODULE 1 - Parser Engine
4. PROMPT MODULE 2 - Rule Engine
5. PROMPT MODULE 3 - AI Engine
6. PROMPT MODULE 4 - Graph Database
7. PROMPT MODULE 5 - Frontend (UI + Canvas)
8. PROMPT MODULE 6 - API Backend
9. PROMPT MODULE 7 - Sécurité Multicouches
10. PROMPT MODULE 8 - Correction Automatique
11. PROMPT MODULE 9 - Reporting DSI/Direction
12. Prompts Transversaux (Infrastructure, CI/CD, Tests)
13. Annexes Techniques

---

## 1. INTRODUCTION ET GUIDE D'UTILISATION

### 1.1 Objectif de ce Document

Ce document contient les prompts détaillés pour le développement de chaque module de la plateforme Network Copilot (NetForge Pro). Chaque prompt est conçu pour être utilisé directement avec un assistant IA de développement (Claude Code, Cursor, GitHub Copilot) ou comme spécification pour un développeur humain.

### 1.2 Comment Utiliser ces Prompts

1. Lire le prompt complet avant de commencer
2. Vérifier les dépendances avec les autres modules
3. Respecter les structures de données définies
4. Implémenter les tests unitaires spécifiés
5. Valider les critères d'acceptation avant de passer au module suivant

### 1.3 Stack Technologique Global

| Composant | Technologie | Version |
|---|---|---|
| Backend API | Python FastAPI | 0.100+ |
| Base de données relationnelle | PostgreSQL | 15+ |
| Base de données temporelle | TimescaleDB | 2.x |
| Base de données graphe | Neo4j | 5.x |
| Cache | Redis Cluster | 7.x |
| Queue | RabbitMQ | 3.12+ |
| Tasks async | Celery | 5.x |
| Frontend | React + TypeScript | 18.x |
| Canvas | React-Flow | 11.x |
| CLI Web | Xterm.js | 5.x |
| Containerisation | Docker + Kubernetes | 1.28+ |

### 1.4 Roadmap de Développement

| Phase | Modules | Durée | Priorité |
|---|---|---|---|
| Phase 1 (MVP) | Parser (Cisco+Fortinet), Rule Engine (L2/L3), Frontend basique, API Backend | 3-4 mois | CRITIQUE |
| Phase 2 | Parser (Huawei+Arista), Graph DB, Canvas avancé, Sécurité L1-L3 | 2-3 mois | HAUTE |
| Phase 3 | AI Engine, Correction semi-auto, Digital Twin | 3-4 mois | MOYENNE |
| Phase 4 | Sécurité L4-L7, Reporting DSI, HA/DR | 2-3 mois | NORMALE |

---

## 2. ARCHITECTURE GLOBALE ET DÉPENDANCES

### 2.1 Diagramme des Dépendances

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (Module 5)                        │
│                  React + Canvas + CLI Web                       │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API BACKEND (Module 6)                       │
│                  FastAPI + Auth + WebSocket                     │
└─────────────────────────────────────────────────────────────────┘
           │             │             │             │
           ▼             ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│    PARSER    │ │    RULE      │ │      AI      │ │   SECURITY   │
│    ENGINE    │ │    ENGINE    │ │    ENGINE    │ │    MODULE    │
│  (Module 1)  │ │  (Module 2)  │ │  (Module 3)  │ │  (Module 7)  │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
           │             │             │             │
           └─────────────┴─────────────┴─────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   GRAPH DATABASE (Module 4)                     │
│                       Neo4j + Cypher                            │
└─────────────────────────────────────────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌──────────────────┐                 ┌──────────────────┐
│    CORRECTION    │                 │    REPORTING     │
│    (Module 8)    │                 │    (Module 9)    │
└──────────────────┘                 └──────────────────┘
```

### 2.2 Ordre de Développement Recommandé

1. Module 6 - API Backend (fondation)
2. Module 1 - Parser Engine (entrée des données)
3. Module 4 - Graph Database (stockage)
4. Module 2 - Rule Engine (analyse)
5. Module 5 - Frontend (interface)
6. Module 7 - Sécurité (transversal)
7. Module 3 - AI Engine (intelligence)
8. Module 8 - Correction (action)
9. Module 9 - Reporting (sortie)

---

## 3. PROMPT MODULE 1 - PARSER ENGINE

> **CONTEXTE**: Tu es un développeur Python expert en automatisation réseau. Tu dois développer le module Parser Engine de la plateforme Network Copilot.

### 3.1 Dépendances

| Type | Description |
|---|---|
| Ce module N'A PAS de dépendances | C'est le point d'entrée des données |
| Modules qui DÉPENDENT de ce module | Rule Engine, Graph Database, AI Engine |
| Base de données | PostgreSQL (stockage configs), Redis (cache parsing) |

### 3.2 Objectif

Créer un moteur de parsing capable de :

1. Importer des configurations depuis fichiers ou connexion SSH live
2. Parser les syntaxes CLI de 4 constructeurs : Cisco, Fortinet, Huawei, Arista
3. Extraire tous les éléments réseau (interfaces, VLAN, routing, ACL, VPN, etc.)
4. Normaliser les données dans un format JSON unifié
5. Détecter automatiquement le constructeur et la version OS

### 3.3 Structure du Projet

```
parser_engine/
├── __init__.py
├── main.py                 # Point d'entrée FastAPI
├── config.py               # Configuration (Pydantic Settings)
├── models/
│   ├── __init__.py
│   ├── base.py             # Modèles Pydantic de base
│   ├── device.py           # Modèle Device normalisé
│   ├── interface.py        # Modèle Interface
│   ├── vlan.py             # Modèle VLAN
│   ├── routing.py          # Modèles OSPF, BGP, Static
│   ├── security.py         # Modèles ACL, NAT, Firewall
│   └── vpn.py              # Modèles IPsec, GRE, DMVPN
├── parsers/
│   ├── __init__.py
│   ├── base_parser.py      # Classe abstraite BaseParser
│   ├── cisco/
│   │   ├── __init__.py
│   │   ├── ios_parser.py
│   │   ├── nxos_parser.py
│   │   └── templates/      # Templates TextFSM
│   ├── fortinet/
│   ├── huawei/
│   └── arista/
├── connectors/
│   ├── ssh_connector.py    # Connexion SSH (Netmiko/Scrapli)
│   ├── api_connector.py    # Connexion API REST/NETCONF
│   └── file_connector.py   # Import fichiers
├── services/
│   └── parsing_service.py  # Service principal
├── api/
│   └── routes.py           # Endpoints API
└── tests/
```

### 3.4 Modèles de Données Principaux

**Device Info**

```python
class DeviceInfo(BaseModel):
    hostname: str
    vendor: VendorType          # cisco, fortinet, huawei, arista
    os_type: OSType             # ios, ios-xe, nxos, fortios, vrp, eos
    os_version: str
    model: str
    serial_number: Optional[str]
    management_ip: Optional[str]
    location: Optional[str]
    zone: Optional[str]
```

**Interface**

```python
class Interface(BaseModel):
    name: str                   # GigabitEthernet0/1
    normalized_name: str        # gi0/1
    type: InterfaceType         # physical, loopback, vlan_svi, port_channel
    description: Optional[str]
    enabled: bool
    # L1
    speed: Optional[str]        # 1000, 10000, auto
    duplex: Optional[str]
    mtu: int = 1500
    # L2
    mode: InterfaceMode         # access, trunk, routed
    access_vlan: Optional[int]
    trunk_allowed_vlans: List[int]
    # L3
    ipv4_addresses: List[str]
    vrf: Optional[str]
    # Connexion distante (CDP/LLDP)
    neighbor_device: Optional[str]
    neighbor_port: Optional[str]
```

### 3.5 API Endpoints

| Méthode | Endpoint | Description |
|---|---|---|
| POST | /api/v1/parser/parse/file | Parse une configuration depuis un fichier uploadé |
| POST | /api/v1/parser/parse/ssh | Parse une configuration via connexion SSH live |
| POST | /api/v1/parser/parse/batch | Parse plusieurs configurations en batch |
| POST | /api/v1/parser/detect/vendor | Détecte automatiquement le constructeur et l'OS |
| GET | /api/v1/parser/templates | Liste les templates de parsing disponibles |

### 3.6 Exemple Input/Output

**Input: Configuration Cisco IOS**

```
hostname CORE-SW-01
!
interface GigabitEthernet0/1
 description Uplink to DIST-SW-01
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30
!
router ospf 1
 router-id 10.0.0.1
 network 10.0.0.0 0.0.255.255 area 0
```

**Output: JSON Normalisé**

```json
{
  "info": {
    "hostname": "CORE-SW-01",
    "vendor": "cisco",
    "os_type": "ios"
  },
  "interfaces": [
    {
      "name": "GigabitEthernet0/1",
      "normalized_name": "gi0/1",
      "description": "Uplink to DIST-SW-01",
      "mode": "trunk",
      "trunk_allowed_vlans": [10, 20, 30]
    }
  ],
  "routing": {
    "ospf_processes": [
      {
        "process_id": 1,
        "router_id": "10.0.0.1",
        "areas": [{"area_id": "0", "networks": ["10.0.0.0/16"]}]
      }
    ]
  }
}
```

### 3.7 Critères d'Acceptation

```
☐ Tous les constructeurs supportés (Cisco, Fortinet, Huawei, Arista)
☐ Détection automatique du vendor fonctionne
☐ Interfaces correctement parsées (L1, L2, L3)
☐ VLAN et STP parsés
☐ OSPF parsé (process, areas, networks)
☐ BGP parsé (AS, neighbors, policies)
☐ ACL parsées avec règles et hit-counts
☐ VPN IPsec parsé
☐ Connexion SSH fonctionnelle
☐ Tests unitaires > 80% coverage
```

### 3.8 Métriques de Performance

| Métrique | Objectif |
|---|---|
| Temps de parsing (config 1000 lignes) | < 500ms |
| Temps de parsing (config 10000 lignes) | < 2s |
| Parsing batch (100 configs) | < 30s |
| Taux de succès parsing | > 95% |

### 3.9 Technologies à Utiliser

- **Python 3.11+** : Langage principal
- **TextFSM / TTP / Genie** : Parsing de configurations CLI
- **Netmiko / Scrapli** : Connexions SSH multi-constructeurs
- **NAPALM** : Abstraction multi-vendor
- **Pydantic** : Validation et sérialisation

---

## 4. PROMPT MODULE 2 - RULE ENGINE

> **CONTEXTE**: Tu es un développeur Python expert en analyse réseau. Tu dois développer le module Rule Engine qui analyse les configurations parsées pour détecter automatiquement les erreurs.

### 4.1 Dépendances

| Type | Description |
|---|---|
| DÉPEND DE | Module 1 (Parser Engine) - reçoit les ParsedDevice |
| DÉPEND DE | Module 4 (Graph Database) - requêtes de topologie |
| Modules qui DÉPENDENT | AI Engine, Correction, Reporting |

### 4.2 Objectif

Créer un moteur de règles capable de :

1. Détecter les anomalies L2 (VLAN, STP, LACP, VXLAN, EVPN)
2. Détecter les anomalies L3 (routage, BGP, OSPF, VRF)
3. Détecter les problèmes WAN (MPLS, IPsec, DMVPN)
4. Analyser la sécurité (ACL, NAT, firewall)
5. Générer des rapports avec sévérité et recommandations

### 4.3 Règles L2 à Implémenter

| ID Règle | Sévérité | Description |
|---|---|---|
| L2_VLAN_001 - VLAN Mismatch on Trunk | HIGH | VLANs autorisés différents entre les deux extrémités d'un trunk |
| L2_STP_001 - Unexpected Root Bridge | CRITICAL | Le root bridge STP n'est pas l'équipement prévu |
| L2_STP_002 - Potential Loop | CRITICAL | Liens redondants sans STP/LACP |
| L2_LACP_001 - LACP Mode Mismatch | HIGH | Modes LACP différents sur les membres d'un port-channel |
| L2_VXLAN_001 - VNI Mismatch | HIGH | Mapping VNI/VLAN incohérent leaf/spine |
| L2_EVPN_001 - MAC Duplication | CRITICAL | Même MAC annoncée depuis plusieurs sources |

### 4.4 Règles L3 à Implémenter

| ID Règle | Sévérité | Description |
|---|---|---|
| L3_OSPF_001 - OSPF Area Mismatch | HIGH | Interfaces OSPF dans des areas différentes |
| L3_OSPF_002 - MTU Mismatch | HIGH | MTU différente entre voisins OSPF |
| L3_BGP_001 - BGP Neighbor Down | CRITICAL | Voisin BGP configuré mais session non établie |
| L3_BGP_002 - Route Leaking | HIGH | Fuite de routes entre VRF non prévue |
| L3_ROUTING_001 - Asymmetric Routing | MEDIUM | Chemin aller différent du retour |
| L3_ROUTING_002 - Routing Loop | CRITICAL | Routes créant des cycles |

### 4.5 Règles Sécurité à Implémenter

| ID Règle | Sévérité | Description |
|---|---|---|
| SEC_ACL_001 - Shadow ACL Rule | MEDIUM | Règle ACL jamais matchée (hit_count = 0) |
| SEC_ACL_002 - Contradictory Rules | HIGH | Règles ACL contradictoires |
| SEC_FW_001 - Any-Any Permit | CRITICAL | Règle firewall autorisant tout trafic |
| SEC_NAT_001 - NAT Pool Exhaustion | HIGH | Pool NAT épuisé ou presque |

### 4.6 Format de Sortie des Problèmes

```json
{
  "id": "prob-001",
  "rule_id": "L2_VLAN_001",
  "category": "l2_vlan",
  "severity": "high",
  "device_id": "dev-001",
  "device_hostname": "CORE-SW-01",
  "interface": "GigabitEthernet0/1",
  "title": "VLAN Mismatch on Trunk",
  "description": "VLANs autorisés différents entre CORE-SW-01 et DIST-SW-01",
  "impact": "Le trafic des VLANs 30 et 40 ne pourra pas traverser ce trunk",
  "recommendation": "Harmoniser les VLANs autorisés sur les deux extrémités",
  "cli_fix": "interface GigabitEthernet0/1\n switchport trunk allowed vlan add 40",
  "cli_fix_vendor": "cisco",
  "evidence": {
    "device_a_vlans": [10, 20, 30],
    "device_b_vlans": [10, 20, 40]
  }
}
```

### 4.7 Critères d'Acceptation

```
☐ 50+ règles L2 implémentées
☐ 30+ règles L3 implémentées
☐ 20+ règles sécurité implémentées
☐ Analyse cross-device fonctionnelle
☐ Règles YAML personnalisables
☐ Calcul des scores (santé, sécurité)
☐ API complète avec filtres
☐ Tests > 85% coverage
```

---

## 5. PROMPT MODULE 3 - AI ENGINE

> **OBJECTIF**: Créer un assistant IA capable de répondre aux questions, expliquer les problèmes, générer des corrections CLI et traduire des configurations entre constructeurs.

**Fonctionnalités Principales**

- Chat conversationnel avec contexte réseau
- Explication des problèmes détectés
- Génération de corrections CLI multi-vendor
- Traduction de configuration (Cisco ↔ Huawei ↔ Fortinet ↔ Arista)
- RAG avec documentation constructeurs

**Technologies**

- **LLM** : Claude / GPT-4 / modèle fine-tuné
- **RAG** : ChromaDB / Pinecone pour embeddings
- **WebSocket** pour streaming des réponses

---

## 6. PROMPT MODULE 4 - GRAPH DATABASE

> **OBJECTIF**: Modéliser l'infrastructure réseau sous forme de graphe Neo4j pour permettre des analyses de topologie complexes.

**Éléments Modélisés**

- **Nodes** : Device, Interface, VLAN, VRF, Zone, Subnet
- **Relations** : CONNECTED_TO, HAS_INTERFACE, MEMBER_OF_VLAN, ROUTES_TO, BGP_PEER, OSPF_NEIGHBOR

**Requêtes Clés**

- Path finding entre devices
- Impact analysis
- Détection de boucles
- Dépendances VLAN

---

## 7. PROMPT MODULE 5 - FRONTEND

> **OBJECTIF**: Créer une interface utilisateur complète avec canvas interactif pour visualiser la topologie, les zones et les ports.

**Composants Principaux**

- `NetworkCanvas` : Canvas React-Flow interactif
- `DeviceNode` : Node device avec état et métriques
- `PortList` : Liste des ports avec LED état
- `ZoneOverlay` : Zones colorées (DMZ, LAN, WAN)
- `TerminalEmulator` : CLI Xterm.js intégrée

**Modes d'Affichage**

| Mode | Description |
|---|---|
| Physique | Rack elevation, câblage, PDU |
| Logique L2 | Spanning-tree, VLAN, trunk |
| Logique L3 | Routage, OSPF, BGP, VRF |
| Sécurité | ACL, firewall, VPN |
| Flux | NetFlow, top talkers |

---

## 8. PROMPT MODULE 6 - API BACKEND

> **OBJECTIF**: Créer l'API REST/GraphQL centrale orchestrant tous les modules.

**Endpoints Principaux**

- `/auth/*` - Authentification (OAuth2, JWT, MFA)
- `/devices/*` - CRUD devices
- `/configs/*` - Gestion configurations
- `/analysis/*` - Lancement analyses
- `/problems/*` - Gestion problèmes
- `/users/*` - Gestion utilisateurs (RBAC)

---

## 9. PROMPT MODULE 7 - SÉCURITÉ MULTICOUCHES

> **OBJECTIF**: Analyser la sécurité L1-L7 et calculer les scores.

**Matrice de Sécurité OSI**

| Couche | Menaces Détectées | Contrôles |
|---|---|---|
| L1 | Accès non autorisé, écoutes | Port security, 802.1X |
| L2 | VLAN hopping, MAC flooding | BPDU Guard, Storm Control |
| L3 | IP spoofing, route injection | uRPF, ACLs, BGP MD5 |
| L4 | SYN flood, session hijacking | TCP Intercept, Zone-based FW |
| L5-L7 | MITM, XSS, malware | TLS inspection, WAF, IPS |

---

## 10-11. MODULES CORRECTION ET REPORTING

### Module 8 - Correction Automatique

- Mode conseil (lecture seule)
- Mode semi-automatique (validation humaine)
- Mode automatique (avec rollback)
- **Technologies** : NAPALM, Nornir, Git

### Module 9 - Reporting DSI

- Dashboard KPIs temps réel
- Rapports PDF automatisés
- Executive Summary
- Métriques ROI

---

## 12. PROMPTS TRANSVERSAUX

### 12.1 Infrastructure Docker/Kubernetes

Services à containeriser :

```
- api-backend      (FastAPI)
- parser-engine    (Python workers)
- rule-engine      (Python workers)
- ai-engine        (Python + GPU)
- frontend         (Node/Nginx)
- neo4j, postgresql, redis, rabbitmq
```

Exigences :

- Health checks sur tous les services
- Secrets management (Vault)
- Horizontal Pod Autoscaling
- Network policies
- Ingress avec TLS

### 12.2 Pipeline CI/CD

| Stage | Actions |
|---|---|
| Build | Build images Docker |
| Test | Tests unitaires et intégration |
| Security | Scan vulnérabilités (Trivy) |
| Quality | Linting, coverage > 80% |
| Deploy Staging | Déploiement auto |
| Deploy Prod | Déploiement manuel |

### 12.3 Stratégie de Tests

- **Tests Unitaires** (pytest) - > 80% coverage
- **Tests Intégration** - API, DB
- **Tests E2E** (Playwright) - Parcours utilisateur
- **Tests Performance** (Locust) - Charge
- **Tests Sécurité** - OWASP ZAP

---

## 13. ANNEXES TECHNIQUES

### 13.1 Variables d'Environnement

```bash
# API Backend
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256

# Database
POSTGRES_HOST=localhost
POSTGRES_DB=netforge
POSTGRES_USER=netforge
POSTGRES_PASSWORD=secret

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secret

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Engine
ANTHROPIC_API_KEY=sk-ant-...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
```

### 13.2 Commandes de Développement

```bash
# Installation
make install        # Install all dependencies
make dev            # Start development environment

# Tests
make test           # Run all tests
make coverage       # Generate coverage report

# Docker
make docker-build   # Build all images
make docker-up      # Start all services

# Database
make db-migrate     # Run migrations
make db-seed        # Seed test data
```

---

*Document généré le 3 Avril 2026*
*Network Copilot Platform - Prompts de Développement v2.0*
