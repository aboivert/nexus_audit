# Calendar

Ce module audite le fichier `calendar.txt` selon trois axes : la présence des champs obligatoires, la validité des formats, et la cohérence logique des données de service.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie la présence et l'unicité de `service_id`, ainsi que la présence de tous les champs de jours et de dates.

| Check | Poids recommandé | Condition |
|---|---|---|
| Présence de `service_id` | 2.0 | Toujours |
| Unicité de `service_id` | 2.0 | Toujours |
| Présence de `monday` | 1.0 | Toujours |
| Présence de `tuesday` | 1.0 | Toujours |
| Présence de `wednesday` | 1.0 | Toujours |
| Présence de `thursday` | 1.0 | Toujours |
| Présence de `friday` | 1.0 | Toujours |
| Présence de `saturday` | 1.0 | Toujours |
| Présence de `sunday` | 1.0 | Toujours |
| Présence de `start_date` | 1.0 | Toujours |
| Présence de `end_date` | 1.0 | Toujours |

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs respectent les formats attendus.

| Champ | Poids recommandé | Règle |
|---|---|---|
| `monday` | 1.0 | Doit valoir `0` ou `1` |
| `tuesday` | 1.0 | Doit valoir `0` ou `1` |
| `wednesday` | 1.0 | Doit valoir `0` ou `1` |
| `thursday` | 1.0 | Doit valoir `0` ou `1` |
| `friday` | 1.0 | Doit valoir `0` ou `1` |
| `saturday` | 1.0 | Doit valoir `0` ou `1` |
| `sunday` | 1.0 | Doit valoir `0` ou `1` |
| `start_date` | 1.0 | Doit être une date valide |
| `end_date` | 1.0 | Doit être une date valide |

---

### 3. Cohérence des données (`consistency`)

Vérifie la cohérence logique des services ainsi que leur utilisation dans `trips.txt`.

| Check | Poids recommandé | Description |
|---|---|---|
| `service_id` inutilisés | 1.0 | Détecte les `service_id` définis dans `calendar.txt` mais non référencés dans `trips.txt` |
| `start_date` < `end_date` | 2.0 | Vérifie que la date de début est strictement antérieure à la date de fin pour chaque service |
| Au moins un jour actif | 1.0 | Vérifie qu'aucun service n'a tous ses jours à `0` (service jamais actif) |

!!! note "Checks logiques spécifiques"
    Les deux derniers checks (`start_before_end` et `at_least_one_active_day`) sont des vérifications métier propres à ce module — elles ne passent en `skip` que si les colonnes concernées sont absentes du fichier.

!!! warning "Dépendance inter-fichiers"
    La détection des `service_id` inutilisés nécessite que `trips.txt` soit chargé en amont. Un DataFrame vide ou absent peut entraîner des faux positifs.

---

## Fonctions spécifiques

### `_check_start_before_end(df)`

**Entrée** — le DataFrame de `calendar.txt`.

**Vérification** — compare directement `start_date` et `end_date` pour chaque ligne. Un service est invalide si `start_date >= end_date` — la date de début doit être **strictement** antérieure à la date de fin.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `start_date` ou `end_date` absentes | Non calculable |
| `error` | Des services ont `start_date >= end_date` | `services invalides / total de lignes` |
| `pass` | Toutes les `start_date` sont antérieures aux `end_date` | 0% |

---

### `_check_at_least_one_active_day(df)`

**Entrée** — le DataFrame de `calendar.txt`.

**Vérification** — parmi les sept colonnes de jours (`monday` à `sunday`), seules celles effectivement présentes dans le DataFrame sont évaluées. Pour chaque service, fait la somme des valeurs des colonnes de jours existantes — un service est invalide si cette somme est égale à 0 (tous les jours à `0`).

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Aucune colonne de jours présente | Non calculable |
| `error` | Des services n'ont aucun jour actif | `services sans jour actif / total de lignes` |
| `pass` | Tous les services ont au moins un jour actif | 0% |

---

## Référence complète

::: audit_calendar