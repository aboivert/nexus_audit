# Agency

Ce module audite le fichier `agency.txt` selon trois axes : la présence des champs obligatoires, la validité des formats, et la cohérence avec `routes.txt`.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie que les trois champs indispensables sont bien présents pour chaque ligne du fichier.

| Check | Poids recommandé| Condition |
|---|---|---|
| Présence de `agency_name` | 2.0 | Toujours |
| Présence de `agency_url` | 1.0 | Toujours |
| Présence de `agency_timezone` | 2.0 | Toujours |
| Présence de `agency_id` | 4.0 | Seulement si `len(df) > 1` |
| Unicité de `agency_id` | 4.0 | Seulement si `len(df) > 1` |

!!! note "Cas particulier — agence unique"
    Si le fichier contient une seule agence (`len(df) <= 1`), les checks sur `agency_id` passent en statut `skip`. Le champ est optionnel dans ce cas selon la spec GTFS.

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs respectent les formats attendus.

| Champ | Poids recommande | Règle |
|---|---|---|
| `agency_timezone` | 4.0 | Doit appartenir à `pytz.all_timezones` |
| `agency_lang` | 1.0 | Doit être un code ISO valide (`fr`, `en`, `de`…) |
| `agency_url` | 2.0 | Doit être une URL bien formée |
| `agency_fare_url` | 1.0 | Doit être une URL bien formée |
| `agency_phone` | 2.0 | Doit correspondre à `^[\+]?[\s\-\(\)0-9]{8,}$` |
| `agency_email` | 1.0 | Doit correspondre au format e-mail standard |

---

### 3. Cohérence inter-fichiers (`consistency`)

Vérifie la cohérence des `agency_id` entre `agency.txt` et `routes.txt`.

| Check | Poids recommandé | Description |
|---|---|---|
| IDs orphelins | 2.0 | Détecte les `agency_id` présents dans `routes.txt` mais absents de `agency.txt` |
| IDs inutilisés | 1.0 | Détecte les `agency_id` définis dans `agency.txt` mais non référencés dans `routes.txt` |

!!! warning "Dépendance inter-fichiers"
    Cette vérification nécessite que `routes.txt` soit chargé en amont. Un DataFrame vide ou absent peut entraîner des faux positifs.

---

## Référence complète

::: audit_agency