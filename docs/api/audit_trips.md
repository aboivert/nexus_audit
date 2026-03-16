# Trips

Ce module audite le fichier `trips.txt` selon quatre axes : la présence des champs obligatoires, la validité des formats, la cohérence inter-fichiers, et l'accessibilité PMR.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie la présence et l'unicité des champs clés, ainsi que la cohérence avec `routes.txt`, `calendar.txt` et `calendar_dates.txt`.

| Check | Poids recommandé | Condition |
|---|---|---|
| Présence de `trip_id` | 3.0 | Toujours |
| Unicité de `trip_id` | 3.0 | Toujours |
| Présence de `route_id` | 3.0 | Toujours |
| Présence de `service_id` | 3.0 | Toujours |
| Cohérence des `route_id` avec `routes.txt` | 2.0 | Toujours |
| Existence des `service_id` dans `calendar.txt` et/ou `calendar_dates.txt` | 2.0 | Seulement si au moins l'un des deux fichiers est chargé |
| Présence d'au moins un nom (`trip_headsign` ou `trip_short_name`) | 2.0 | Toujours |

!!! note "Existence des service_id"
    Les `service_id` sont recherchés dans `calendar.txt` **et** `calendar_dates.txt` simultanément — un `service_id` valide dans l'un ou l'autre des deux fichiers est accepté. Si les deux fichiers sont absents, le check passe en `skip`.

!!! warning "Dépendance inter-fichiers"
    Ce module dépend de `routes.txt`, `calendar.txt`, `calendar_dates.txt`, `stop_times.txt` et optionnellement `shapes.txt`.

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs respectent les formats attendus.

| Champ | Poids recommandé | Règle |
|---|---|
| `direction_id` | 1.0 | Doit valoir `0` ou `1` |
| `bikes_allowed` | 1.0 | Doit valoir `0`, `1` ou `2` |

---

### 3. Cohérence inter-fichiers (`consistency`)

Vérifie l'utilisation des `trip_id` dans `stop_times.txt` et la cohérence des `shape_id` avec `shapes.txt`.

| Check | Poids recommandé | Description |
|---|---|---|
| `trip_id` inutilisés | 1.0 | Détecte les `trip_id` définis dans `trips.txt` mais sans aucun horaire dans `stop_times.txt` |
| Existence des `shape_id` dans `shapes.txt` | 2.0 | Vérifie que tous les `shape_id` référencés dans `trips.txt` existent dans `shapes.txt` |

!!! warning "Dépendance inter-fichiers"
    Si `shapes.txt` est absent, le check sur les `shape_id` passe en `skip`.

---

### 4. Accessibilité (`accessibility`)

Vérifie la validité et mesure le taux de couverture de l'accessibilité PMR.

| Check | Poids recommandé | Description |
|---|---|---|
| Format de `wheelchair_accessible` | 1.0 | Doit valoir `0`, `1` ou `2` |
| Métriques d'accessibilité | 3.0 | Calcule le taux de trips accessibles (`wheelchair_accessible = 1`) parmi ceux renseignés |

!!! note "Métriques d'accessibilité"
    Le check de métriques ne génère pas d'erreur — il produit un statut informatif et stocke dans `details` le nombre de trips accessibles, non accessibles, et non renseignés. C'est un indicateur de couverture plutôt qu'une validation stricte.

---

## Fonctions spécifiques

### `_check_service_id_existence(df, calendar_df, calendar_dates_df)`

**Entrée** — le DataFrame de `trips.txt`, le DataFrame de `calendar.txt` (ou `None` si absent), et le DataFrame de `calendar_dates.txt` (ou `None` si absent).

**Vérification** — un `service_id` est valide s'il est défini dans `calendar.txt` **ou** dans `calendar_dates.txt` (ou les deux). Construit un DataFrame union des `service_id` uniques présents dans les fichiers disponibles, puis délègue à `check_orphan_ids` pour détecter les `service_id` de `trips.txt` absents de ce référentiel combiné.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Ni `calendar.txt` ni `calendar_dates.txt` disponibles | Non calculable |
| `error` | Des `service_id` n'existent ni dans `calendar.txt` ni dans `calendar_dates.txt` | `IDs orphelins / total des service_id référencés dans trips.txt` |
| `pass` | Tous les `service_id` existent dans au moins un des deux fichiers | 0% |

!!! note "Union des référentiels"
    Le référentiel est construit par **union** des deux fichiers — un `service_id` défini uniquement dans `calendar_dates.txt` (sans entrée dans `calendar.txt`) est tout à fait valide.

---

## Référence complète

::: audit_trips