# NetForge Pro - Module 4: Graph Database (Neo4j)

## Vue d'ensemble

Le **Graph Database** module fournit une modélisation graphe complète de l'infrastructure réseau utilisant Neo4j. Il transforme les données parsées des équipements en nœuds et relations, permettant des analyses avancées de topologie, d'impact et de dépendances.

## Architecture

```
src/graph_database/
├── config.py              # Configuration Neo4j
├── models/
│   └── graph_models.py    # Nœuds et Relations Pydantic
├── services/
│   ├── neo4j_service.py   # Connexion + CRUD Neo4j
│   ├── graph_builder.py   # ParsedDevice → Graph
│   └── graph_queries.py   # Requêtes Cypher avancées
├── api/
│   └── routes.py          # Endpoints REST API
└── tests/
    └── test_graph.py      # Tests complets avec mocks
```

## Modèle de données

### Nœuds

| Nœud | Propriétés | Description |
|------|------------|-------------|
| **Device** | hostname, vendor, model, os_version, zone | Équipement réseau |
| **Interface** | name, type, ip, vlan, state, speed | Interface réseau |
| **VLAN** | id, name, svi_ip | Configuration VLAN |
| **VRF** | name, rd, rt_import, rt_export | Instance VRF |
| **Zone** | name, type, security_level | Zone réseau |

### Relations

| Relation | Type | Description |
|----------|------|-------------|
| **CONNECTED_TO** | Interface ↔ Interface | Connexions physiques/logiques |
| **HAS_INTERFACE** | Device → Interface | Composition device |
| **MEMBER_OF_VLAN** | Interface → VLAN | Appartenance VLAN |
| **ROUTES_TO** | Device → Device | Routage entre devices |
| **LOCATED_IN** | Device → Zone | Placement zonal |

## Services

### Neo4jService
- **Connexion async** avec pool de connexions
- **Gestion d'erreurs** robuste
- **CRUD operations** de base
- **Context managers** pour sessions

### GraphBuilder
- **Transformation** ParsedDevice → Nœuds/Relations
- **Batch processing** pour gros volumes
- **Cache intelligent** des nœuds existants
- **Gestion des doublons**

### GraphQueries
- **Requêtes Cypher** optimisées
- **Path finding** entre devices
- **Impact analysis** des pannes
- **Détection de boucles** de routage

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/graph/build` | Construire le graphe depuis devices parsés |
| `POST` | `/api/v1/graph/path` | Trouver chemin entre 2 devices |
| `GET` | `/api/v1/graph/impact/{hostname}` | Analyser impact d'une panne |
| `GET` | `/api/v1/graph/zone/{zone}/devices` | Lister devices d'une zone |
| `GET` | `/api/v1/graph/device/{host}/interface/{int}/vlans` | VLANs d'un trunk |
| `GET` | `/api/v1/graph/loops` | Détecter boucles de routage |
| `GET` | `/api/v1/graph/stats` | Statistiques réseau |
| `GET` | `/api/v1/graph/device/{host}/topology` | Topologie d'un device |
| `GET` | `/api/v1/graph/isolated` | Devices isolés |
| `DELETE` | `/api/v1/graph/clear` | Vider la base (⚠️) |

## Requêtes Cypher clés

### 1. Chemin entre devices
```cypher
MATCH path = shortestPath(
  (start:Device {hostname: $start})-[*1..10]->(end:Device {hostname: $end})
)
RETURN path
```

### 2. Détection de boucles
```cypher
MATCH path = (d:Device)-[r:ROUTES_TO*]->(d:Device)
WHERE length(path) > 2
RETURN [node IN nodes(path) | node.hostname] as devices, length(path) as loop_length
```

### 3. Impact analysis
```cypher
MATCH (target:Device {hostname: $hostname})<-[:CONNECTED_TO|ROUTES_TO]-(d:Device)
RETURN collect(DISTINCT d.hostname) as directly_connected
```

### 4. Devices par zone
```cypher
MATCH (d:Device)-[:LOCATED_IN]->(z:Zone {name: $zone})
RETURN d.hostname, d.vendor, d.model
```

### 5. VLANs d'un trunk
```cypher
MATCH (d:Device {hostname: $host})-[:HAS_INTERFACE]->(i:Interface {name: $int})
-[r:MEMBER_OF_VLAN {mode: 'trunk'}]->(v:VLAN)
RETURN v.vlan_id, v.name, r.native
```

## Configuration

```python
# Configuration Neo4j
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

# Pool de connexions
NEO4J_MAX_CONNECTION_POOL_SIZE = 50
NEO4J_CONNECTION_TIMEOUT = 30.0

# Traitement par lots
GRAPH_BATCH_SIZE = 100
GRAPH_BUILD_TIMEOUT = 300.0
```

## Utilisation

### Construction du graphe
```python
from graph_database import GraphBuilder, Neo4jService
from parser_engine.models.device import Device

# Initialiser services
neo4j = Neo4jService(settings)
await neo4j.connect()

builder = GraphBuilder(neo4j, settings)

# Construire depuis devices parsés
devices = [parsed_device1, parsed_device2]
stats = await builder.build_devices_batch(devices, zone_name="production")
```

### Requêtes d'analyse
```python
from graph_database import GraphQueries

queries = GraphQueries(neo4j, settings)

# Analyser impact
impact = await queries.analyze_impact("router1")
print(f"Impact score: {impact['total_impact_score']}")

# Trouver chemin
paths = await queries.find_path("router1", "server1")
if paths:
    print(f"Chemin trouvé: {len(paths[0])} sauts")
```

### API REST
```bash
# Construire le graphe
curl -X POST http://localhost:8000/api/v1/graph/build \
  -H "Content-Type: application/json" \
  -d '{"devices": [...], "zone_name": "production"}'

# Analyser impact
curl http://localhost:8000/api/v1/graph/impact/router1

# Statistiques réseau
curl http://localhost:8000/api/v1/graph/stats
```

## Tests

Le module inclut une suite complète de tests avec mocks Neo4j :

```bash
# Tests du module
pytest src/graph_database/tests/ -v

# Avec couverture
pytest src/graph_database/tests/ --cov=src/graph_database
```

**Résultats attendus**: Tous tests passent sans instance Neo4j réelle.

## Intégration

Le Graph Database s'intègre avec :

- **Parser Engine** (Module 1): Consomme les `ParsedDevice`
- **Discovery Engine** (Module 10): Enrichit avec données découvertes
- **API Backend** (Module 6): Exposition via endpoints REST
- **Rule Engine** (Module 2): Requêtes pour analyses métier

## Performance

- **Async/Await** complet pour toutes les opérations
- **Batch processing** pour construction massive
- **Cache de nœuds** pour éviter les recreations
- **Pool de connexions** Neo4j optimisé
- **Timeouts configurables** pour éviter les blocages

## Sécurité

- **Connexion authentifiée** Neo4j
- **Validation Pydantic** de toutes les données
- **Gestion d'erreurs** sans exposition d'infos sensibles
- **Logs sécurisés** sans credentials

## Déploiement

### Prérequis
- **Neo4j 5.0+** installé et configuré
- **Python 3.12+** avec dépendances
- **Connexion réseau** au serveur Neo4j

### Démarrage
```python
from graph_database import Neo4jService, GraphBuilder, GraphQueries
from graph_database.api.routes import init_graph_api

# Initialiser services
neo4j = Neo4jService(settings)
await neo4j.connect()

builder = GraphBuilder(neo4j, settings)
queries = GraphQueries(neo4j, settings)

# Initialiser API
init_graph_api(neo4j, builder, queries, settings)
```

---

**Status**: ✅ **COMPLET** - Module 4 implémenté et testé

Le Graph Database est maintenant opérationnel pour modéliser et analyser votre infrastructure réseau ! 🕸️