# Stops

Ce module audite le fichier `stops.txt` selon cinq axes : la présence des champs obligatoires, la validité des formats, la cohérence inter-fichiers, la hiérarchie des arrêts, et l'accessibilité PMR.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie la présence et l'unicité des champs clés.

| Check | Poids recommandé | Condition |
|---|---|---|
| Présence de `stop_id` | 2.0 | Toujours |
| Unicité de `stop_id` | 2.0 | Toujours |
| Présence de `stop_name` | 1.0 | Toujours |
| Présence de `stop_lat` | 1.0 | Toujours |
| Présence de `stop_lon` | 1.0 | Toujours |

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs respectent les formats attendus.

| Champ | Poids recommandé | Règle |
|---|---|---|
| `stop_url` | 1.0 | Doit être une URL bien formée |
| `stop_timezone` | 2.0 | Doit appartenir à `pytz.all_timezones` |
| `stop_lat` | 3.0 | Doit être une coordonnée géographique valide |
| `stop_lon` | 3.0 | Doit être une coordonnée géographique valide |

---

### 3. Cohérence inter-fichiers (`consistency`)

Vérifie la cohérence des `stop_id` avec `stop_times.txt`.

| Check | Poids recommandé | Description |
|---|---|---|
| `stop_id` orphelins | 2.0 | Détecte les `stop_id` présents dans `stop_times.txt` mais absents de `stops.txt` |
| `stop_id` inutilisés | 1.0 | Détecte les `stop_id` définis dans `stops.txt` mais non référencés dans `stop_times.txt` |

!!! warning "Dépendance inter-fichiers"
    Ces vérifications nécessitent que `stop_times.txt` soit chargé en amont.

---

### 4. Hiérarchie des arrêts (`stops_hierarchy`)

Vérifie l'intégrité de la hiérarchie entre arrêts et zones d'arrêt (`location_type` / `parent_station`).

| Check | Poids recommandé | Description |
|---|---|---|
| Format de `location_type` | 2.0 | Doit valoir `0`, `1`, `2`, `3` ou `4` |
| Zones d'arrêt sans `parent_station` | 4.0 | Vérifie que les stops avec `location_type=1` n'ont pas de `parent_station` renseigné |
| `parent_station` existants | 4.0 | Vérifie que chaque `parent_station` référencé pointe vers un `stop_id` existant dans le fichier |
| `parent_station` est bien une zone | 4.0 | Vérifie que chaque `parent_station` pointe vers un stop avec `location_type=1` |
| Zones d'arrêt utilisées | 2.0 | Détecte les zones d'arrêt (`location_type=1`) non référencées par aucun arrêt enfant |
| Distance géographique | 1.0 | Vérifie que chaque arrêt est à moins de **2000m** de sa zone d'arrêt parente |

!!! note "Calcul de distance"
    La distance est calculée via la formule **Haversine** à partir des coordonnées GPS (`stop_lat`, `stop_lon`) de l'arrêt et de sa zone parente. Les arrêts ou zones dont les coordonnées sont invalides ou absentes sont ignorés. Une distance supérieure à 2000m génère un statut `error`.

!!! note "Checks conditionnels"
    Les checks de hiérarchie passent en `skip` si les colonnes `location_type`, `parent_station`, `stop_lat` ou `stop_lon` sont absentes du fichier, ou si aucun arrêt avec `parent_station` n'est trouvé.

---

### 5. Accessibilité (`accessibility`)

Vérifie la validité et mesure le taux de couverture de l'accessibilité PMR.

| Check | Poids recommandé | Description |
|---|---|---|
| Format de `wheelchair_boarding` | 1.0 | Doit valoir `0`, `1` ou `2` |
| Métriques d'accessibilité | 3.0 | Calcule le taux d'arrêts accessibles (`wheelchair_boarding = 1`) parmi ceux renseignés |

!!! note "Métriques d'accessibilité"
    Le check de métriques est informatif — il ne génère pas d'erreur mais stocke dans `details` le nombre d'arrêts accessibles, non accessibles et non renseignés.

---

## Fonctions spécifiques

### `_check_station_no_parent(df)`

**Entrée** — le DataFrame de `stops.txt`.

**Vérification** — filtre les arrêts avec `location_type = 1` (zones d'arrêt). Pour chacun, vérifie que `parent_station` est vide ou absent. Si aucune zone d'arrêt n'est présente dans le fichier, le check est ignoré. Le `total_count` représente le nombre de zones d'arrêt (`location_type = 1`), pas le total de lignes.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `location_type` ou `parent_station` absentes | Non calculable |
| `skip` | Aucune zone d'arrêt (`location_type = 1`) dans le fichier | Non applicable |
| `error` | Des zones d'arrêt ont un `parent_station` renseigné | `zones invalides / total de zones d'arrêt` |
| `pass` | Aucune zone d'arrêt n'a de `parent_station` | 0% |

---

### `_check_parent_station_is_station(df)`

**Entrée** — le DataFrame de `stops.txt`.

**Vérification** — construit un dictionnaire `stop_id → location_type`. Pour chaque arrêt ayant un `parent_station` renseigné, vérifie que le `stop_id` cible a bien un `location_type = 1`. Les `parent_station` absents du fichier sont ignorés — ils sont déjà couverts par `check_orphan_ids`. Si aucun arrêt n'a de `parent_station`, le check est ignoré. Le `total_count` ne compte que les arrêts dont le `parent_station` est présent dans le fichier et donc effectivement évalués.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `parent_station`, `location_type` ou `stop_id` absentes | Non calculable |
| `skip` | Aucun `parent_station` renseigné dans le fichier | Non applicable |
| `error` | Des `parent_station` pointent vers un arrêt qui n'est pas `location_type = 1` | `arrêts invalides / arrêts évalués` |
| `pass` | Tous les `parent_station` pointent vers des zones d'arrêt | 0% |

---

### `_check_stop_distance_from_station(df)`

**Entrée** — le DataFrame de `stops.txt`.

**Vérification** — construit un dictionnaire `stop_id → (stop_lat, stop_lon)`. Pour chaque arrêt ayant un `parent_station` renseigné, calcule la distance en mètres entre l'arrêt et sa zone via la formule de Haversine (rayon terrestre = 6 371 000 m). Un arrêt est invalide si cette distance dépasse **2000 m**. Les arrêts ou stations dont les coordonnées sont absentes ou non parseable sont ignorés et ne sont pas comptabilisés dans `total_count`. Le champ `details` contient pour chaque arrêt concerné : `distance_m` et `parent_station`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `parent_station`, `stop_lat`, `stop_lon` ou `stop_id` absentes | Non calculable |
| `skip` | Aucun arrêt avec `parent_station` renseigné | Non applicable |
| `error` | Des arrêts sont à plus de 2000 m de leur zone | `arrêts trop éloignés / arrêts évalués` |
| `pass` | Tous les arrêts sont à moins de 2000 m de leur zone | 0% |

---

## Référence complète

::: audit_stops