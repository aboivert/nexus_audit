# Calendar Dates

Ce module audite le fichier `calendar_dates.txt` selon trois axes : la présence des champs obligatoires, la validité des formats, et la cohérence logique des exceptions de service.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie la présence des champs clés et la cohérence des `service_id` avec `calendar.txt`.

| Check | Poids recommandé | Condition |
|---|---|---|
| Présence de `service_id` | 1.0 | Toujours |
| Présence de `date` | 1.0 | Toujours |
| Unicité de la paire `(service_id, date)` | 1.0 | Toujours |
| Cohérence des `service_id` avec `calendar.txt` | 1.0 | Seulement si `calendar.txt` est chargé |

!!! note "Unicité composite"
    L'unicité est vérifiée sur la **combinaison** `(service_id, date)` et non sur chaque champ séparément — un même service peut apparaître plusieurs fois à des dates différentes.

!!! warning "Dépendance inter-fichiers"
    Si `calendar.txt` est absent, le check de cohérence des `service_id` passe en statut `skip`.

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs respectent les formats attendus.

| Champ | Poids recommandé | Règle |
|---|---|---|
| `date` | 1.0 | Doit être une date valide |
| `exception_type` | 1.0 | Doit valoir `1` (ajout de service) ou `2` (suppression de service) |

---

### 3. Cohérence des données (`consistency`)

Vérifie la cohérence logique des exceptions par rapport au calendrier de référence.

| Check | Poids recommandé | Description |
|---|---|---|
| Dates dans la période du service | 1.0 | Vérifie que chaque date est comprise dans la plage `start_date` / `end_date` de son `service_id` dans `calendar.txt` |
| Absence de conflits d'exceptions | 1.0 | Vérifie qu'aucune paire `(service_id, date)` n'a simultanément un `exception_type` à `1` et à `2` |

!!! note "Checks logiques spécifiques"
    Ces deux checks sont des vérifications métier propres à ce module. Ils passent en `skip` si les colonnes nécessaires sont absentes, ou si `calendar.txt` n'est pas disponible.

!!! warning "Dépendance inter-fichiers"
    La vérification des dates dans la période nécessite que `calendar.txt` soit chargé avec des colonnes `start_date` et `end_date` valides.

---

## Fonctions spécifiques

### `_check_dates_in_calendar_period(df, calendar_df)`

**Entrée** — le DataFrame de `calendar_dates.txt` et le DataFrame de `calendar.txt` (ou `None` si absent).

**Vérification** — construit un dictionnaire `service_id → (start_date, end_date)` depuis `calendar.txt`. Pour chaque ligne de `calendar_dates.txt`, vérifie que la `date` est comprise dans la plage `[start_date, end_date]` de son `service_id`. Les `service_id` absents de `calendar.txt` sont ignorés — ils sont déjà couverts par `check_orphan_ids`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | `calendar.txt` absent | Non calculable |
| `skip` | Colonnes `date`, `service_id`, `start_date` ou `end_date` absentes | Non calculable |
| `warning` | Des dates sont hors de la période de leur service | `dates hors période / total de lignes` |
| `pass` | Toutes les dates sont dans la période de leur service | 0% |

!!! note "Warning et non error"
    Une date hors période génère un `warning` et non un `error` — c'est une anomalie à signaler mais qui ne rompt pas la cohérence du référentiel.

---

### `_check_no_conflicting_exceptions(df)`

**Entrée** — le DataFrame de `calendar_dates.txt`.

**Vérification** — groupe les lignes par paire `(service_id, date)` et collecte l'ensemble des `exception_type` présents dans chaque groupe. Un conflit est détecté quand une même paire possède simultanément un `exception_type = 1` (ajout de service) et un `exception_type = 2` (suppression de service) — ce qui est logiquement contradictoire.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `service_id`, `date` ou `exception_type` absentes | Non calculable |
| `error` | Des paires `(service_id, date)` ont les deux types simultanément | `paires en conflit / total de service_id uniques` |
| `pass` | Aucun conflit détecté | 0% |

!!! warning "Error et non warning"
    Un conflit d'exceptions est toujours un `error` — une même journée ne peut pas être à la fois ajoutée et supprimée pour un même service, ce qui rend les données inutilisables.

---

## Référence complète

::: audit_calendar_dates