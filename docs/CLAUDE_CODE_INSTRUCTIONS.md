# NETFORGE PRO - INSTRUCTIONS CLAUDE CODE
## Guide Opérationnel de Développement

---

# 🚨 RÈGLES IMPÉRATIVES (À LIRE EN PREMIER)

Avant **TOUTE** action de développement, Claude Code **DOIT** suivre ce protocole dans l'ordre exact.

---

## PHASE 0 : VÉRIFICATION PRÉALABLE (OBLIGATOIRE)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHECKLIST AVANT TOUTE ACTION                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  □ 1. LIRE le Cahier des Charges (CDC)                         │
│       → Fichier: CDC_NetForge_Pro_v2.pdf                        │
│       → Comprendre le contexte global du projet                 │
│                                                                 │
│  □ 2. LIRE les Prompts du Module concerné                       │
│       → Fichier: NetForge_Pro_Prompts_Developpement_v2.pdf      │
│       → Identifier les spécifications exactes                   │
│                                                                 │
│  □ 3. ANALYSER l'existant                                       │
│       → Lister les fichiers/modules déjà créés                  │
│       → Identifier ce qui reste à faire                         │
│       → Vérifier les dépendances entre modules                  │
│                                                                 │
│  □ 4. VÉRIFIER les doublons potentiels                          │
│       → Si doublon détecté → FUSIONNER en gardant le meilleur   │
│       → Ne jamais créer de code redondant                       │
│                                                                 │
│  □ 5. CONFIRMER le plan d'action avant d'exécuter               │
│       → Présenter ce qui va être fait                           │
│       → Attendre validation si nécessaire                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1 : ANALYSE (Avant de coder)

### 1.1 Lecture des Documents de Référence

| Document | Contenu | Priorité |
|----------|---------|----------|
| `CDC_NetForge_Pro_v2.pdf` | Architecture globale, modules, objectifs | 🔴 CRITIQUE |
| `NetForge_Pro_Prompts_Developpement_v2.pdf` | Spécifications détaillées par module | 🔴 CRITIQUE |
| `NetForge_CDC_Enrichissements_v3.pdf` | Discovery Engine, CLI Unifié | 🟠 HAUTE |
| `NetForge_Nomenclature_Interfaces.pdf` | Nomenclature multi-vendor | 🟡 MOYENNE |
| `interface_nomenclature.py` | Module Python de référence | 🟡 MOYENNE |

### 1.2 Questions à se poser

```
AVANT de coder, répondre à :

1. QUOI ?
   → Quel module/fonctionnalité développer ?
   → Quelles sont les spécifications exactes dans le prompt ?

2. POURQUOI ?
   → Quel est l'objectif métier ?
   → Comment ça s'intègre dans l'architecture globale ?

3. DÉPENDANCES ?
   → De quels modules ce code dépend-il ?
   → Quels modules dépendront de ce code ?

4. EXISTANT ?
   → Y a-t-il du code similaire déjà écrit ?
   → Peut-on réutiliser/étendre plutôt que recréer ?

5. TESTS ?
   → Quels tests unitaires sont requis ?
   → Quels critères d'acceptation valider ?
```

---

## PHASE 2 : PLANIFICATION (Avant d'exécuter)

### 2.1 Ordre de Développement des Modules

```
SÉQUENCE RECOMMANDÉE :

1. Module 6  - API Backend         (fondation)
2. Module 1  - Parser Engine       (entrée des données)
3. Module 10 - Discovery Engine    (découverte réseau)
4. Module 4  - Graph Database      (stockage)
5. Module 2  - Rule Engine         (analyse)
6. Module 5  - Frontend + CLI      (interface)
7. Module 7  - Sécurité            (transversal)
8. Module 3  - AI Engine           (intelligence)
9. Module 8  - Correction          (action)
10. Module 9 - Reporting           (sortie)
```

### 2.2 Structure Standard d'un Module

```
module_name/
├── __init__.py
├── main.py                 # Point d'entrée FastAPI
├── config.py               # Configuration Pydantic
├── models/                 # Modèles de données
│   ├── __init__.py
│   └── *.py
├── services/               # Logique métier
│   ├── __init__.py
│   └── *.py
├── api/                    # Routes API
│   ├── __init__.py
│   └── routes.py
├── utils/                  # Utilitaires
│   ├── __init__.py
│   └── *.py
└── tests/                  # Tests unitaires
    ├── __init__.py
    ├── conftest.py
    └── test_*.py
```

---

## PHASE 3 : DÉVELOPPEMENT (Règles d'exécution)

### 3.1 Règles de Codage

```python
# ✅ BONNES PRATIQUES

# 1. Toujours utiliser des type hints
def parse_config(config: str, vendor: Vendor) -> ParsedDevice:
    pass

# 2. Documenter avec docstrings
def detect_vendor(sysdescr: str) -> VendorType:
    """
    Détecte le constructeur à partir du sysDescr SNMP.
    
    Args:
        sysdescr: Chaîne sysDescr SNMP
    
    Returns:
        VendorType: cisco, huawei, arista, fortinet
    
    Raises:
        VendorNotFoundError: Si vendor non reconnu
    """
    pass

# 3. Utiliser Pydantic pour les modèles
class DeviceInfo(BaseModel):
    hostname: str
    vendor: VendorType
    os_version: str

# 4. Gestion des erreurs explicite
try:
    result = parse_config(config)
except ParsingError as e:
    logger.error(f"Parsing failed: {e}")
    raise
```

### 3.2 Règles de Nomenclature

| Élément | Convention | Exemple |
|---------|------------|---------|
| Fichiers | snake_case | `vendor_detector.py` |
| Classes | PascalCase | `DeviceFingerprint` |
| Fonctions | snake_case | `detect_vendor()` |
| Constantes | UPPER_SNAKE | `MAX_RETRIES` |
| Variables | snake_case | `device_info` |

### 3.3 Gestion des Doublons

```
SI doublon détecté :

1. IDENTIFIER les deux versions
2. COMPARER les fonctionnalités
3. FUSIONNER en gardant :
   → La version la plus complète
   → Les tests les plus exhaustifs
   → La meilleure documentation
4. SUPPRIMER la version obsolète
5. METTRE À JOUR les imports
```

---

## PHASE 4 : VALIDATION (Après avoir codé)

### 4.1 Checklist Post-Développement

```
□ Code respecte les spécifications du prompt
□ Tests unitaires écrits et passants (pytest)
□ Pas de doublons avec l'existant
□ Imports corrects entre modules
□ Documentation à jour
□ Pas d'erreurs de linting (flake8/black)
□ Types vérifiés (mypy si applicable)
```

### 4.2 Commandes de Validation

```bash
# Lancer les tests
pytest module_name/tests/ -v

# Vérifier le linting
flake8 module_name/
black module_name/ --check

# Vérifier les types
mypy module_name/

# Couverture de tests
pytest --cov=module_name --cov-report=html
```

---

## PHASE 5 : INTÉGRATION (Finalisation)

### 5.1 Avant de Passer au Module Suivant

```
1. ✓ Module actuel 100% fonctionnel
2. ✓ Tests passent à 100%
3. ✓ Intégration avec modules dépendants vérifiée
4. ✓ Documentation mise à jour
5. ✓ Commit Git avec message descriptif
```

### 5.2 Convention de Commits

```bash
# Format: <type>(<module>): <description>

git commit -m "feat(parser): add Huawei VRP parser"
git commit -m "fix(discovery): correct SNMP timeout handling"
git commit -m "test(rule-engine): add OSPF mismatch detection tests"
git commit -m "docs(api): update OpenAPI documentation"
```

---

# 📋 TEMPLATE DE DÉMARRAGE

Copier ce template au début de chaque session Claude Code :

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    NETFORGE PRO - SESSION DEV
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 DOCUMENTS DE RÉFÉRENCE :
   • CDC: CDC_NetForge_Pro_v2.pdf
   • Prompts: NetForge_Pro_Prompts_Developpement_v2.pdf
   • Enrichissements: NetForge_CDC_Enrichissements_v3.pdf

🎯 MODULE À DÉVELOPPER : [Nom du module]

📋 CHECKLIST PRÉ-DEV :
   □ CDC lu et compris
   □ Prompt du module lu
   □ Existant analysé
   □ Dépendances identifiées
   □ Plan validé

🚀 ACTION DEMANDÉE :
   [Description de ce qu'il faut faire]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# ⚠️ INTERDICTIONS

```
❌ NE JAMAIS :

• Coder sans avoir lu le prompt du module
• Ignorer les spécifications du CDC
• Créer du code redondant avec l'existant
• Oublier les tests unitaires
• Hardcoder des valeurs (utiliser config)
• Ignorer la nomenclature des interfaces
• Mélanger les responsabilités des modules
```

---

# 💡 SUGGESTIONS ADDITIONNELLES

## 1. Fichier de Configuration Projet

Créer un `pyproject.toml` à la racine :

```toml
[project]
name = "netforge-pro"
version = "1.0.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"

[tool.black]
line-length = 100
target-version = ['py311']

[tool.mypy]
python_version = "3.11"
strict = true
```

## 2. Structure Projet Globale

```
netforge-pro/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── CDC_NetForge_Pro_v2.pdf
│   ├── NetForge_Pro_Prompts_Developpement_v2.pdf
│   └── architecture/
├── src/
│   ├── parser_engine/         # Module 1
│   ├── rule_engine/           # Module 2
│   ├── ai_engine/             # Module 3
│   ├── graph_database/        # Module 4
│   ├── frontend/              # Module 5
│   ├── api_backend/           # Module 6
│   ├── security_module/       # Module 7
│   ├── correction_engine/     # Module 8
│   ├── reporting/             # Module 9
│   ├── discovery_engine/      # Module 10
│   └── shared/                # Code partagé
│       ├── models/
│       ├── utils/
│       └── interface_nomenclature.py
├── tests/
│   ├── integration/
│   └── e2e/
└── scripts/
    ├── setup.sh
    └── run_tests.sh
```

## 3. Variables d'Environnement Standard

```bash
# .env.example
# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=netforge
POSTGRES_USER=netforge
POSTGRES_PASSWORD=changeme

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

# Redis
REDIS_URL=redis://localhost:6379/0

# AI
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
ANTHROPIC_API_KEY=sk-ant-xxx

# Discovery
SNMP_COMMUNITY=public
SSH_TIMEOUT=30
SCAN_WORKERS=10
```

## 4. Commandes Make Utiles

```makefile
# Makefile

.PHONY: install dev test lint format

install:
	pip install -e ".[dev]"

dev:
	docker-compose up -d
	uvicorn src.api_backend.main:app --reload

test:
	pytest -v --cov=src

lint:
	flake8 src/
	mypy src/

format:
	black src/
	isort src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

---

# ✅ RÉSUMÉ EXÉCUTIF

```
AVANT DE CODER :
   1. Lire CDC + Prompt
   2. Analyser existant
   3. Identifier dépendances
   4. Fusionner si doublons

PENDANT LE CODE :
   5. Suivre les conventions
   6. Écrire les tests
   7. Documenter

APRÈS LE CODE :
   8. Valider (pytest, lint)
   9. Intégrer
   10. Commit Git
```

---

*Document de référence Claude Code - NetForge Pro v1.0*
*Dernière mise à jour : Avril 2026*
