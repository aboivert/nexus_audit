# Système de pondération

Le système de poids permet de moduler l'importance relative de chaque check dans le calcul du score final. Les poids sont centralisés dans un fichier JSON et chargés une seule fois au démarrage de l'application.

---

## Fonctionnement

Chaque check retourne un `CheckResult` qui contient un champ `weight` — un `float` définissant sa contribution au score de sa catégorie. Plus le poids est élevé, plus le check pèse dans le score final.

Le poids intervient dans le calcul du `CategoryScore` : un check en `pass` contribue `weight` points au numérateur, un check en `error` ou `warning` contribue `0`, et un check en `skip` est exclu du calcul. Pour le détail de la formule, voir [Système de scoring](scoring.md).

---

## `scoring_config.json`

Les poids sont définis dans `scoring_config.json`, organisé par fichier GTFS. Chaque entrée associe un `check_id` à son poids :

```json
{
  "routes.txt": {
    "routes.mandatory.route_id_presence": 4.0,
    "routes.mandatory.route_id_unicity": 4.0,
    "format.route_type_valid": 2.0,
    "routes.accessibility.color_contrast": 1.0
  }
}
```

Les poids vont de `1.0` (check informatif ou optionnel) à `4.0` (check critique).

---

## `scoring_config.py`

Le module `scoring_config.py` charge le fichier JSON **une seule fois** au démarrage et expose `SCORING_CONFIG`, un dictionnaire Python importable dans tous les modules d'audit.

Dans chaque fonction d'audit, la configuration du fichier GTFS concerné est chargée localement via `SCORING_CONFIG.get()` :
```python
from scoring_config import SCORING_CONFIG

def _check_mandatory_fields(df: pd.DataFrame) -> list[CheckResult]:
    cfg = SCORING_CONFIG.get("calendar.txt", {})
    return [
        check_id_presence(df, "service_id", weight=cfg.get("calendar.mandatory.service_id_presence", 2.0)),
    ...
    ]
```

Le `.get()` avec valeur par défaut garantit qu'une clé absente du JSON ne lève pas d'exception — le check se rabat sur un poids de `1.0`.

---

## Tableau de référence

### `agency.txt`

| check_id | Poids |
|---|---|
| `agency.mandatory.agency_name_presence` | 2.0 |
| `agency.mandatory.agency_url_presence` | 1.0 |
| `agency.mandatory.agency_timezone_presence` | 2.0 |
| `agency.mandatory.agency_id_presence` | 4.0 |
| `agency.mandatory.agency_id_unicity` | 4.0 |
| `format.agency_lang_valid` | 1.0 |
| `format.agency_phone_valid` | 2.0 |
| `format.agency_fare_url_valid` | 1.0 |
| `format.agency_email_valid` | 1.0 |
| `format.agency_timezone_valid` | 4.0 |
| `format.agency_url_valid` | 2.0 |
| `agency.consistency.agency_id_no_orphan` | 2.0 |
| `agency.consistency.agency_id_no_unused` | 1.0 |

### `calendar.txt`

| check_id | Poids |
|---|---|
| `calendar.mandatory.service_id_presence` | 2.0 |
| `calendar.mandatory.service_id_unicity` | 2.0 |
| `calendar.mandatory.monday_presence` | 1.0 |
| `calendar.mandatory.tuesday_presence` | 1.0 |
| `calendar.mandatory.wednesday_presence` | 1.0 |
| `calendar.mandatory.thursday_presence` | 1.0 |
| `calendar.mandatory.friday_presence` | 1.0 |
| `calendar.mandatory.saturday_presence` | 1.0 |
| `calendar.mandatory.sunday_presence` | 1.0 |
| `calendar.mandatory.start_date_presence` | 1.0 |
| `calendar.mandatory.end_date_presence` | 1.0 |
| `format.monday_valid` | 1.0 |
| `format.tuesday_valid` | 1.0 |
| `format.wednesday_valid` | 1.0 |
| `format.thursday_valid` | 1.0 |
| `format.friday_valid` | 1.0 |
| `format.saturday_valid` | 1.0 |
| `format.sunday_valid` | 1.0 |
| `format.start_date_valid` | 1.0 |
| `format.end_date_valid` | 1.0 |
| `calendar.consistency.service_id_no_unused` | 1.0 |
| `calendar.consistency.start_before_end` | 2.0 |
| `calendar.consistency.at_least_one_active_day` | 1.0 |

### `calendar_dates.txt`

| check_id | Poids |
|---|---|
| `calendar_dates.mandatory.service_id_presence` | 1.0 |
| `calendar_dates.mandatory.date_presence` | 1.0 |
| `calendar_dates.mandatory.service_id_date_unicity` | 1.0 |
| `calendar_dates.mandatory.service_id_consistency` | 1.0 |
| `format.date_valid` | 1.0 |
| `format.exception_type_valid` | 1.0 |
| `calendar_dates.consistency.dates_in_period` | 1.0 |
| `calendar_dates.consistency.no_conflicting_exceptions` | 1.0 |

### `routes.txt`

| check_id | Poids |
|---|---|
| `routes.mandatory.route_id_presence` | 4.0 |
| `routes.mandatory.route_id_unicity` | 4.0 |
| `routes.mandatory.route_short_or_long_name` | 2.0 |
| `routes.mandatory.route_type_presence` | 2.0 |
| `routes.mandatory.agency_id_presence` | 2.0 |
| `routes.mandatory.agency_id_existence` | 2.0 |
| `format.route_type_valid` | 2.0 |
| `format.route_color_valid` | 2.0 |
| `format.route_text_color_valid` | 2.0 |
| `format.route_url_valid` | 1.0 |
| `format.continuous_pickup_valid` | 1.0 |
| `format.continuous_drop_off_valid` | 1.0 |
| `routes.consistency.route_id_no_orphan` | 3.0 |
| `routes.consistency.route_id_no_unused` | 2.0 |
| `routes.consistency.duplicate_route_short_name` | 1.0 |
| `routes.consistency.duplicate_route_long_name` | 1.0 |
| `routes.accessibility.color_contrast` | 1.0 |

### `stop_times.txt`

| check_id | Poids |
|---|---|
| `stop_times.mandatory.trip_id_presence` | 2.0 |
| `stop_times.mandatory.stop_sequence_presence` | 2.0 |
| `stop_times.mandatory.trip_id_stop_sequence_unicity` | 2.0 |
| `stop_times.mandatory.trip_id_no_orphan` | 2.0 |
| `stop_times.mandatory.stop_id_presence` | 1.0 |
| `stop_times.mandatory.departure_time_presence` | 1.0 |
| `stop_times.mandatory.arrival_time_presence` | 1.0 |
| `stop_times.mandatory.stop_id_no_orphan` | 2.0 |
| `format.pickup_type_valid` | 1.0 |
| `format.drop_off_type_valid` | 1.0 |
| `stop_times.temporal.arrival_time_valid` | 2.0 |
| `stop_times.temporal.departure_time_valid` | 2.0 |
| `stop_times.temporal.arrival_before_departure` | 3.0 |
| `stop_times.temporal.sequential_consistency` | 3.0 |
| `stop_times.temporal.excessive_dwell_time` | 1.0 |

### `stops.txt`

| check_id | Poids |
|---|---|
| `stops.mandatory.stop_id_presence` | 2.0 |
| `stops.mandatory.stop_id_unicity` | 2.0 |
| `stops.mandatory.stop_name_presence` | 1.0 |
| `stops.mandatory.stop_lat_presence` | 1.0 |
| `stops.mandatory.stop_lon_presence` | 1.0 |
| `format.stop_url_valid` | 1.0 |
| `format.stop_timezone_valid` | 2.0 |
| `format.stop_lat_valid` | 3.0 |
| `format.stop_lon_valid` | 3.0 |
| `stops.consistency.stop_id_no_orphan` | 2.0 |
| `stops.consistency.stop_id_no_unused` | 1.0 |
| `stops.stops_hierarchy.location_type_valid` | 2.0 |
| `stops.stops_hierarchy.station_no_parent` | 4.0 |
| `stops.stops_hierarchy.parent_station_exists` | 4.0 |
| `stops.stops_hierarchy.parent_station_is_station` | 4.0 |
| `stops.stops_hierarchy.stop_id_no_unused` | 2.0 |
| `stops.stops_hierarchy.stop_distance_from_station` | 1.0 |
| `format.wheelchair_boarding_valid` | 1.0 |
| `accessibility.wheelchair_boarding_metrics` | 3.0 |

### `trips.txt`

| check_id | Poids |
|---|---|
| `trips.mandatory.trip_id_presence` | 3.0 |
| `trips.mandatory.trip_id_unicity` | 3.0 |
| `trips.mandatory.route_id_presence` | 3.0 |
| `trips.mandatory.service_id_presence` | 3.0 |
| `trips.mandatory.route_id_no_orphan` | 2.0 |
| `trips.mandatory.service_id_existence` | 2.0 |
| `trips.mandatory.trip_short_or_headsign` | 2.0 |
| `format.direction_id_valid` | 1.0 |
| `format.bikes_allowed_valid` | 1.0 |
| `trips.consistency.trip_id_no_unused` | 1.0 |
| `trips.consistency.shape_id_no_orphan` | 2.0 |
| `format.wheelchair_accessible_valid` | 1.0 |
| `accessibility.wheelchair_accessible_metrics` | 3.0 |