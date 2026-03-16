# Stop Times

Ce module audite le fichier `stop_times.txt` selon quatre axes : la présence des champs obligatoires, la validité des formats, la cohérence inter-fichiers, et la cohérence temporelle des horaires.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie la présence et l'unicité des champs clés, ainsi que la cohérence avec `trips.txt` et `stops.txt`.

| Check | Poids recommandé | Condition |
|---|---|---|
| Présence de `trip_id` | 2.0 | Toujours |
| Présence de `stop_sequence` | 2.0 | Toujours |
| Unicité de la paire `(trip_id, stop_sequence)` | 2.0 | Toujours |
| Cohérence des `trip_id` avec `trips.txt` | 2.0 | Toujours |
| Présence de `stop_id` | 1.0 | Toujours |
| Présence de `departure_time` | 1.0 | Toujours |
| Présence de `arrival_time` | 1.0 | Toujours |
| Cohérence des `stop_id` avec `stops.txt` | 2.0 | Toujours |

!!! note "Unicité composite"
    L'unicité est vérifiée sur la combinaison `(trip_id, stop_sequence)` — un même trip peut avoir plusieurs arrêts, mais pas deux fois le même numéro de séquence.

!!! warning "Dépendance inter-fichiers"
    Les checks de cohérence nécessitent que `trips.txt` et `stops.txt` soient chargés en amont.

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs de pickup et drop-off respectent les formats attendus.

| Champ | Poids recommandé | Règle |
|---|---|---|
| `pickup_type` | 1.0 | Doit valoir `0`, `1`, `2` ou `3` |
| `drop_off_type` | 1.0 | Doit valoir `0`, `1`, `2` ou `3` |

---

### 3. Cohérence temporelle (`temporal`)

Vérifie la validité du format des horaires et leur cohérence logique au sein de chaque trip.

| Check | Poids recommandé | Description |
|---|---|---|
| Format de `arrival_time` | 2.0 | Doit respecter le format `HH:MM:SS` (heures > 23 autorisées en GTFS) |
| Format de `departure_time` | 2.0 | Doit respecter le format `HH:MM:SS` (heures > 23 autorisées en GTFS) |
| `arrival_time` ≤ `departure_time` | 3.0 | Vérifie que l'heure d'arrivée est antérieure ou égale à l'heure de départ pour chaque arrêt |
| Cohérence séquentielle | 3.0 | Vérifie que le `departure_time` d'un arrêt est inférieur ou égal au `arrival_time` de l'arrêt suivant, pour chaque trip |
| Temps d'arrêt excessif | 1.0 | Détecte les arrêts dont le temps d'arrêt (`departure_time` - `arrival_time`) dépasse **1 heure** |

!!! note "Horaires GTFS > 24h"
    Le format GTFS autorise des heures supérieures à `23:59:59` pour les services qui franchissent minuit (ex: `25:30:00` = 01h30 le lendemain). Le parser interne gère correctement ces cas.

!!! note "Temps d'arrêt excessif"
    Un temps d'arrêt supérieur à 1h génère un statut `warning` (et non `error`) — ce n'est pas nécessairement une erreur, mais un signal à vérifier manuellement. Les détails (heures d'arrivée, de départ, durée en minutes) sont stockés dans le champ `details` du `CheckResult`.

---

## Fonctions spécifiques

### `_check_arrival_before_departure(df)`

**Entrée** — le DataFrame de `stop_times.txt`.

**Vérification** — pour chaque ligne, convertit `arrival_time` et `departure_time` en secondes via `_parse_time_to_seconds`. Les lignes où l'une des deux valeurs est non parseable sont ignorées. Un arrêt est invalide si `arrival_time > departure_time`. Les `affected_ids` sont construits sous la forme `trip_id:stop_sequence`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `arrival_time` ou `departure_time` absentes | Non calculable |
| `error` | Des arrêts ont `arrival_time > departure_time` | `arrêts invalides / total de lignes` |
| `pass` | Tous les `arrival_time` sont ≤ aux `departure_time` | 0% |

---

### `_check_sequential_consistency(df)`

**Entrée** — le DataFrame de `stop_times.txt`.

**Vérification** — trie les lignes par `trip_id` puis `stop_sequence`, puis parcourt chaque trip séquentiellement. Pour chaque paire d'arrêts consécutifs `n` et `n+1`, vérifie que `departure_time[n] ≤ arrival_time[n+1]`. Les paires où l'une des valeurs est non parseable sont ignorées et ne sont pas comptabilisées dans `total_count`. Les `affected_ids` sont construits sous la forme `trip_id:seq_n_seq_n+1`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `trip_id`, `stop_sequence`, `departure_time` ou `arrival_time` absentes | Non calculable |
| `error` | Des transitions ont `departure_time[n] > arrival_time[n+1]` | `transitions invalides / total de paires évaluées` |
| `pass` | Tous les horaires sont séquentiellement cohérents | 0% |

!!! note "Total_count"
    Le `total_count` représente le nombre de **paires consécutives évaluées**, et non le nombre total de lignes.

---

### `_check_excessive_dwell_time(df)`

**Entrée** — le DataFrame de `stop_times.txt`.

**Vérification** — pour chaque ligne parseable, calcule le temps d'arrêt `dwell_time = departure_time - arrival_time` en secondes. Un temps d'arrêt supérieur à **3600 secondes (1h)** est signalé. Les `affected_ids` sont construits sous la forme `trip_id:stop_sequence`. Le champ `details` contient pour chaque arrêt concerné : `arrival_time`, `departure_time`, `dwell_seconds` et `dwell_minutes`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `arrival_time` ou `departure_time` absentes | Non calculable |
| `warning` | Des arrêts ont un temps d'arrêt > 1h | `arrêts excessifs / lignes évaluées` |
| `pass` | Aucun temps d'arrêt excessif détecté | 0% |

!!! note "Warning et non error"
    Un temps d'arrêt excessif est inhabituel mais peut être légitime (terminus, dépôt) — d'où un `warning`.

---

## Référence complète

::: audit_stop_times