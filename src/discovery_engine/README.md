# NetForge Pro - Module 10: Discovery Engine

## Vue d'ensemble

Le **Discovery Engine** est une sonde réseau intelligente capable de découvrir automatiquement les équipements réseau dans une infrastructure. Il combine plusieurs techniques de découverte pour identifier les devices, leurs vendors et établir la topologie réseau.

## Fonctionnalités

### 🔍 Découverte réseau
- **Ping Sweep**: Détection des hosts actifs via ICMP
- **Port Scanning**: Scan des ports 22, 23, 161, 443
- **SNMP Discovery**: Récupération des informations via SNMP (sysDescr, sysName, etc.)

### 🕵️ Fingerprinting multi-sources
- **Algorithme pondéré**: Combine SNMP (50%), SSH (30%), MAC OUI (20%)
- **Identification vendor**: Cisco, Huawei, Arista, Fortinet, Juniper, etc.
- **Classification device**: Router, Switch, Firewall, etc.

### 🗺️ Topologie réseau
- **LLDP/CDP Discovery**: Découverte des voisins via protocoles Layer 2
- **Auto-learning**: Découverte récursive depuis un device "seed"
- **Cartographie réseau**: Construction automatique de la topologie

## Architecture

```
src/discovery_engine/
├── config.py              # Configuration (timeouts, ports, poids)
├── models/
│   └── discovery.py       # Modèles Pydantic (DiscoveredDevice, FingerprintResult, etc.)
├── services/
│   ├── scanner.py         # Ping sweep + port scanning
│   ├── snmp_discovery.py  # Requêtes SNMP
│   ├── fingerprinter.py   # Algorithme de fingerprinting
│   └── topology.py        # Découverte LLDP/CDP
├── api/
│   └── routes.py          # Endpoints REST API
└── tests/
    └── test_discovery.py  # Tests unitaires
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/discovery/scan` | Lancer un scan réseau |
| `GET` | `/api/v1/discovery/scan/{id}` | Statut du scan |
| `GET` | `/api/v1/discovery/scan/{id}/devices` | Résultats du scan |
| `POST` | `/api/v1/discovery/auto-discover` | Auto-learning depuis seed |

## Exemple d'utilisation

### Scan réseau basique
```python
from discovery_engine import NetworkScanner
from ipaddress import IPv4Network

scanner = NetworkScanner()
network = IPv4Network("192.168.1.0/24")
devices = await scanner.scan_network(network)
```

### Fingerprinting device
```python
from discovery_engine import DeviceFingerprinter
from discovery_engine.models.discovery import SNMPInfo

fingerprinter = DeviceFingerprinter()
snmp_info = SNMPInfo(sysDescr="Cisco IOS Software, Version 15.4(3)M3")
result = await fingerprinter.fingerprint_device(ip, snmp_info=snmp_info)
print(f"Vendor: {result.vendor}, Confidence: {result.confidence_score}")
```

### Auto-discovery
```python
from discovery_engine import TopologyDiscovery

topology = TopologyDiscovery()
credentials = {"username": "admin", "password": "secret"}
devices = await topology.auto_discover(seed_ip, credentials, max_hops=3)
```

## Configuration

Le module utilise des variables d'environnement pour la configuration :

```python
# Délais et limites
SCAN_TIMEOUT_SECONDS = 5
MAX_CONCURRENT_SCANS = 50
SNMP_TIMEOUT = 2.0

# Ports par défaut
DEFAULT_PORTS = [22, 23, 161, 443]

# Poids fingerprinting
SNMP_FINGERPRINT_WEIGHT = 0.5
SSH_FINGERPRINT_WEIGHT = 0.3
MAC_FINGERPRINT_WEIGHT = 0.2
```

## Dépendances

- `scapy`: Ping sweep et manipulation paquets
- `pysnmp`: Requêtes SNMP
- `paramiko`: Connexions SSH
- `netmiko`: Connexions réseau (LLDP/CDP)

## Tests

Le module inclut une suite complète de tests :

```bash
# Exécuter tous les tests
pytest src/discovery_engine/tests/ -v

# Avec couverture
pytest src/discovery_engine/tests/ --cov=src/discovery_engine
```

**Résultats**: 14 tests passent, 1 skip (SNMP conditionnel)

## Intégration

Le Discovery Engine s'intègre avec :
- **Parser Engine**: Fournit les devices découverts pour parsing
- **API Backend**: Exposition via endpoints REST
- **Graph Database**: Stockage des topologies découvertes

## Workflow typique

1. **Scan réseau** → Découverte des IPs actives
2. **SNMP/SSH** → Collecte des informations système
3. **Fingerprinting** → Identification vendor/OS
4. **Topologie** → Découverte des voisins LLDP/CDP
5. **Parsing** → Analyse des configurations récupérées

## Sécurité

- Timeouts configurables pour éviter les blocages
- Limites de débit pour éviter la surcharge réseau
- Gestion graceful des erreurs de connexion
- Support des credentials sécurisés

## Performance

- **Async/Await**: Toutes les opérations sont asynchrones
- **Thread pools**: Utilisation de ThreadPoolExecutor pour les I/O
- **Batching**: Traitement par lots pour l'auto-discovery
- **Caching**: Cache Redis pour éviter les rescans

---

**Status**: ✅ **COMPLET** - Module 10 implémenté et testé