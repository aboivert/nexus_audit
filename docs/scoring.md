# Système de scoring

Le système de scoring évalue la qualité d'un fichier GTFS en agrégeant les résultats de tous les checks d'audit en un score final sur 100, assorti d'une note lettrée.

Il repose sur trois structures imbriquées : `CheckResult` → `CategoryScore` → `FileScore`.

---

## Vue d'ensemble

```
CheckResult        CheckResult        CheckResult  ...
     │                  │                  │
     └──────────────────┴──────────────────┘
                        │
                  CategoryScore  (ex: "mandatory")
                        │
              CategoryScore  CategoryScore  ...
                        │         │
                        └────┬────┘
                             │
                          FileScore  →  score (0-100)  →  grade (A+ … F)
```

Chaque `CheckResult` a un **poids** (`weight`) qui reflète l'importance relative du check. Les scores sont agrégés par **moyenne pondérée** à chaque niveau.

---

## Les classes en détail

### CheckResult

`CheckResult` est la brique de base du système. Chaque fonction d'audit retourne une liste de `CheckResult` — un par vérification effectuée. C'est un **dataclass** Python, ce qui signifie que ses attributs sont déclarés directement à la définition de la classe, sans logique dans `__init__`.

#### Attributs

| Attribut | Type | Obligatoire | Description |
|---|---|---|---|
| `check_id` | `str` | ✅ | Identifiant unique du check, ex: `"agency.format.timezone"`. Suit la convention `fichier.catégorie.champ` |
| `label` | `str` | ✅ | Description lisible du check, ex: `"Validité du fuseau horaire"` |
| `category` | `str` | ✅ | Catégorie du check — voir tableau des catégories ci-dessous |
| `status` | `str` | ✅ | Résultat du check : `"pass"`, `"warning"`, `"error"` ou `"skip"` |
| `weight` | `float` | ✅ | Pondération du check dans le calcul du score. Plus le poids est élevé, plus ce check influence le score final |
| `message` | `str` | ✅ | Explication humaine du résultat, ex: `"3 fuseaux horaires invalides détectés"` |
| `affected_ids` | `list[str]` | ❌ | Liste des identifiants des éléments problématiques (ex: les `agency_id` en erreur). Vide par défaut |
| `affected_count` | `int` | ❌ | Nombre d'éléments en anomalie. `0` par défaut |
| `total_count` | `int` | ❌ | Nombre total d'éléments évalués. `0` par défaut |
| `recommendations` | `list[str]` | ❌ | Actions correctives suggérées (fonctionnalité prévue). Vide par défaut |
| `details` | `dict \| None` | ❌ | Données brutes optionnelles pour debug ou affichage avancé. `None` par défaut |

#### Statuts possibles

| Statut | Signification |
|---|---|
| `pass` | Le check est réussi, aucune anomalie détectée |
| `warning` | Des anomalies mineures ont été détectées |
| `error` | Des anomalies bloquantes ont été détectées |
| `skip` | Le check a été ignoré (non applicable dans ce contexte) |

Les checks en statut `skip` sont **exclus du calcul du score** — ils ne pénalisent pas le résultat.

#### Propriété `anomaly_rate`

Calcule le taux d'anomalie en pourcentage à partir de `affected_count` et `total_count` :

```python
anomaly_rate = (affected_count / total_count) * 100
```

Retourne `None` si `total_count == 0` pour éviter une division par zéro.

#### Propriété `score`

Calcule le score du check sur une échelle de 0 à 100. Retourne `None` si le statut est `skip`.

**Mode 1 — Taux de réussite** (utilisé quand `total_count > 0`)

```python
score = 100 * (1 - affected_count / total_count)
```

Par exemple, si 3 lignes sur 10 sont en anomalie : `score = 100 * (1 - 3/10) = 70.0`

**Mode 2 — Pénalité fixe** (utilisé quand `total_count == 0`, c'est-à-dire quand le check est binaire)

| Statut | Score |
|---|---|
| `pass` | 100.0 |
| `warning` | 60.0 |
| `error` | 0.0 |
| `skip` | `None` (exclu) |

---

### CategoryScore

`CategoryScore` agrège tous les `CheckResult` d'une même catégorie au sein d'un fichier GTFS. C'est également un **dataclass**, construit après l'exécution de tous les checks d'un fichier.

#### Attributs

| Attribut | Type | Description |
|---|---|---|
| `category` | `str` | Nom de la catégorie, ex: `"mandatory"`, `"format"` |
| `checks` | `list[CheckResult]` | Liste de tous les `CheckResult` appartenant à cette catégorie. Vide par défaut |

#### Catégories existantes

| Catégorie | Description |
|---|---|
| `mandatory` | Présence et unicité des champs obligatoires |
| `format` | Validité du format des valeurs |
| `consistency` | Cohérence inter-fichiers (IDs orphelins, inutilisés…) |
| `stats` | Indicateurs statistiques |
| `accessibility` | Accessibilité PMR |
| `temporal` | Cohérence des données temporelles |
| `stops_hierarchy` | Hiérarchie des arrêts |

#### Propriété `score`

Calcule la **moyenne pondérée** des scores des checks éligibles. Un check est éligible si son score n'est pas `None` (donc statut ≠ `skip`) et que son poids est strictement supérieur à 0 :

```python
score = Σ (check.score × check.weight) / Σ check.weight
```

Retourne `None` si aucun check éligible n'existe dans la catégorie.

#### Propriété `total_weight`

Retourne la somme des poids des checks éligibles uniquement :

```python
total_weight = Σ check.weight  # checks éligibles seulement
```

Ce `total_weight` est **réutilisé par `FileScore`** pour pondérer les catégories entre elles — une catégorie avec beaucoup de checks importants (poids élevés) aura donc plus d'influence sur le score final qu'une catégorie légère.

---

### FileScore

`FileScore` est le niveau le plus haut du système. Il agrège tous les `CategoryScore` d'un fichier GTFS pour produire un **score global sur 100** et une **note lettrée**.

#### Attributs

| Attribut | Type | Description |
|---|---|---|
| `file` | `str` | Nom du fichier GTFS audité, ex: `"agency.txt"` |
| `categories` | `list[CategoryScore]` | Liste de toutes les catégories du fichier. Vide par défaut |

#### Propriété `score`

Calcule la **moyenne pondérée** des scores de catégories éligibles (score non `None`), pondérée par le `total_weight` de chaque catégorie :

```python
score = Σ (cat.score × cat.total_weight) / Σ cat.total_weight
```

Retourne `None` si aucune catégorie n'est éligible, ou si le poids total est égal à 0.

Ce double niveau de pondération (poids des checks → poids des catégories) garantit que **les checks les plus importants ont toujours le plus d'impact** sur le score final, quelle que soit la catégorie dans laquelle ils se trouvent.

#### Propriété `grade`

Convertit le score numérique en note lettrée :

| Score | Grade |
|---|---|
| ≥ 95 | A+ |
| ≥ 90 | A |
| ≥ 85 | B+ |
| ≥ 80 | B |
| ≥ 75 | C+ |
| ≥ 70 | C |
| ≥ 60 | D |
| < 60 | F |

Retourne `None` si le score est `None`.

---

## Calcul du score — récapitulatif

| Niveau | Formule | Exclut |
|---|---|---|
| `CheckResult.score` | Taux de réussite ou pénalité fixe | statut `skip` |
| `CategoryScore.score` | Moyenne pondérée des checks | checks `skip` ou poids = 0 |
| `FileScore.score` | Moyenne pondérée des catégories | catégories sans score |

---

## Exemple complet

Prenons un fichier `agency.txt` avec les checks suivants :

| Check | Catégorie | Statut | affected | total | Poids | Score |
|---|---|---|---|---|---|---|
| `agency_name` présence | mandatory | pass | 0 | 5 | 1.0 | 100.0 |
| `agency_id` présence | mandatory | error | 5 | 5 | 3.0 | 0.0 |
| `agency_timezone` format | format | warning | 1 | 5 | 1.0 | 80.0 |
| `agency_url` format | format | pass | 0 | 5 | 1.0 | 100.0 |
| `agency_id` orphelins | consistency | pass | 0 | 5 | 2.0 | 100.0 |

**CategoryScore "mandatory"**

```
score = (100.0 × 1.0 + 0.0 × 3.0) / (1.0 + 3.0) = 25.0
total_weight = 4.0
```

**CategoryScore "format"**

```
score = (80.0 × 1.0 + 100.0 × 1.0) / (1.0 + 1.0) = 90.0
total_weight = 2.0
```

**CategoryScore "consistency"**

```
score = (100.0 × 2.0) / 2.0 = 100.0
total_weight = 2.0
```

**FileScore**

```
score = (25.0 × 4.0 + 90.0 × 2.0 + 100.0 × 2.0) / (4.0 + 2.0 + 2.0)
      = (100 + 180 + 200) / 8
      = 60.0  →  grade: D
```

L'absence de `agency_id` (poids 3.0) tire fortement le score vers le bas, ce qui illustre bien le rôle des poids dans le système.


## Référence complète

::: audit_models