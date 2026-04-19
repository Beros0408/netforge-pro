# NETFORGE PRO
## Instructions Claude Code
### Guide Operationnel de Developpement

> **A LIRE AVANT TOUTE ACTION**

*Version 1.0 - Avril 2026*

---

## REGLES IMPERATIVES

Avant TOUTE action de developpement, Claude Code **DOIT** suivre ce protocole dans l'ordre exact.

### CHECKLIST OBLIGATOIRE

```
+---------------------------------------------------------------------+
| CHECKLIST AVANT TOUTE ACTION                                        |
+---------------------------------------------------------------------+
|                                                                     |
| [ ] 1. LIRE le Cahier des Charges (CDC)                             |
|     -> Fichier: CDC_NetForge_Pro_v2.pdf                             |
|     -> Comprendre le contexte global du projet                      |
|                                                                     |
| [ ] 2. LIRE les Prompts du Module concerne                          |
|     -> Fichier: NetForge_Pro_Prompts_Developpement_v2.pdf           |
|     -> Identifier les specifications exactes                        |
|                                                                     |
| [ ] 3. ANALYSER l'existant                                          |
|     -> Lister les fichiers/modules deja crees                       |
|     -> Identifier ce qui reste a faire                              |
|     -> Verifier les dependances entre modules                       |
|                                                                     |
| [ ] 4. VERIFIER les doublons potentiels                             |
|     -> Si doublon detecte -> FUSIONNER en gardant le meilleur       |
|     -> Ne jamais creer de code redondant                            |
|                                                                     |
| [ ] 5. CONFIRMER le plan d'action avant d'executer                  |
|     -> Presenter ce qui va etre fait                                |
|     -> Attendre validation si necessaire                            |
|                                                                     |
+---------------------------------------------------------------------+
```

---

## PHASE 1 : ANALYSE

### 1.1 Documents de Reference

| Document | Contenu | Priorite |
|---|---|---|
| CDC_NetForge_Pro_v2.pdf | Architecture globale, modules, objectifs | CRITIQUE |
| NetForge_Pro_Prompts_Developpement_v2.pdf | Specifications detaillees par module | CRITIQUE |
| NetForge_CDC_Enrichissements_v3.pdf | Discovery Engine, CLI Unifie | HAUTE |
| NetForge_Nomenclature_Interfaces.pdf | Nomenclature multi-vendor | MOYENNE |
| interface_nomenclature.py | Module Python de reference | MOYENNE |

### 1.2 Questions a se poser AVANT de coder

| Question | Objectif |
|---|---|
| QUOI ? | Quel module/fonctionnalite developper ? Quelles specs dans le prompt ? |
| POURQUOI ? | Quel objectif metier ? Integration dans l'architecture ? |
| DEPENDANCES ? | De quels modules ce code depend-il ? Qui en dependra ? |
| EXISTANT ? | Code similaire existe ? Reutiliser/etendre plutot que recreer ? |
| TESTS ? | Quels tests unitaires ? Quels criteres d'acceptation ? |

---

## PHASE 2 : PLANIFICATION

### 2.1 Ordre de Developpement

| Ordre | Module | Raison |
|---|---|---|
| 1 | Module 6 - API Backend | Fondation |
| 2 | Module 1 - Parser Engine | Entree des donnees |
| 3 | Module 10 - Discovery Engine | Decouverte reseau |
| 4 | Module 4 - Graph Database | Stockage |
| 5 | Module 2 - Rule Engine | Analyse |
| 6 | Module 5 - Frontend + CLI | Interface |
| 7 | Module 7 - Securite | Transversal |
| 8 | Module 3 - AI Engine | Intelligence |
| 9 | Module 8 - Correction | Action |
| 10 | Module 9 - Reporting | Sortie |

### 2.2 Structure Standard d'un Module

```
module_name/
+-- __init__.py
+-- main.py          # Point d'entree FastAPI
+-- config.py        # Configuration Pydantic
+-- models/          # Modeles de donnees
|   +-- __init__.py
|   +-- *.py
+-- services/        # Logique metier
|   +-- __init__.py
|   +-- *.py
+-- api/             # Routes API
|   +-- __init__.py
|   +-- routes.py
+-- utils/           # Utilitaires
+-- tests/           # Tests unitaires
    +-- conftest.py
    +-- test_*.py
```

---

## PHASE 3 : DEVELOPPEMENT

### 3.1 Regles de Nomenclature

| Element | Convention | Exemple |
|---|---|---|
| Fichiers | snake_case | vendor_detector.py |
| Classes | PascalCase | DeviceFingerprint |
| Fonctions | snake_case | detect_vendor() |
| Constantes | UPPER_SNAKE | MAX_RETRIES |
| Variables | snake_case | device_info |

### 3.2 Gestion des Doublons

SI doublon detecte :

1. IDENTIFIER les deux versions
2. COMPARER les fonctionnalites
3. FUSIONNER en gardant le meilleur (code + tests + docs)
4. SUPPRIMER la version obsolete
5. METTRE A JOUR les imports

---

## PHASE 4 : VALIDATION

### 4.1 Checklist Post-Developpement

```
[ ] Code respecte les specifications du prompt
[ ] Tests unitaires ecrits et passants (pytest)
[ ] Pas de doublons avec l'existant
[ ] Imports corrects entre modules
[ ] Documentation a jour
[ ] Pas d'erreurs de linting (flake8/black)
```

### 4.2 Commandes de Validation

```bash
# Lancer les tests
pytest module_name/tests/ -v

# Verifier le linting
flake8 module_name/
black module_name/ --check

# Couverture de tests
pytest --cov=module_name --cov-report=html
```

---

## INTERDICTIONS

**NE JAMAIS :**

- Coder sans avoir lu le prompt du module
- Ignorer les specifications du CDC
- Creer du code redondant avec l'existant
- Oublier les tests unitaires
- Hardcoder des valeurs (utiliser config)
- Ignorer la nomenclature des interfaces
- Melanger les responsabilites des modules

---

## TEMPLATE DE SESSION

Copier ce template au debut de chaque session Claude Code :

```
================================================================
NETFORGE PRO - SESSION DEV
================================================================
DOCUMENTS DE REFERENCE :
- CDC: CDC_NetForge_Pro_v2.pdf
- Prompts: NetForge_Pro_Prompts_Developpement_v2.pdf
- Enrichissements: NetForge_CDC_Enrichissements_v3.pdf

MODULE A DEVELOPPER : [Nom du module]

CHECKLIST PRE-DEV :
[ ] CDC lu et compris
[ ] Prompt du module lu
[ ] Existant analyse
[ ] Dependances identifiees
[ ] Plan valide

ACTION DEMANDEE :
[Description de ce qu'il faut faire]
================================================================
```

---

## RESUME EXECUTIF

| Etape | Action |
|---|---|
| AVANT | 1. Lire CDC + Prompt \| 2. Analyser existant \| 3. Identifier dependances \| 4. Fusionner si doublons |
| PENDANT | 5. Suivre conventions \| 6. Ecrire tests \| 7. Documenter |
| APRES | 8. Valider (pytest, lint) \| 9. Integrer \| 10. Commit Git |

---

*NetForge Pro - Instructions Claude Code v1.0 - Avril 2026*
