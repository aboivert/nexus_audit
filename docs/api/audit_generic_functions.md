# Fonctions génériques

Ce module définit les fonctions d'audit réutilisées par tous les modules GTFS. Chaque fonction retourne un `CheckResult` — à l'exception de `is_truly_empty` qui est une fonction utilitaire interne.

---

## `check_id_presence(df, field)`

**Entrée** — un DataFrame et le nom du champ identifiant à vérifier (ex: `"stop_id"`).

**Vérification** — si la colonne est absente du DataFrame, toutes les lignes sont considérées en erreur. Sinon, détecte les lignes où la valeur est `NaN` ou une chaîne vide. Les identifiants reportés dans `affected_ids` sont les index du DataFrame.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `error` | Colonne absente | 100% |
| `error` | Valeurs manquantes détectées | `affected_count / total_count` |
| `pass` | Toutes les valeurs sont présentes | 0% |

---

## `check_id_unicity(df, fields)`

**Entrée** — un DataFrame et un champ ou une liste de champs formant la clé à vérifier (ex: `"trip_id"` ou `["trip_id", "stop_sequence"]`).

**Vérification** — si une ou plusieurs colonnes sont absentes, le check passe en `skip`. Sinon, détecte toutes les lignes dont la combinaison de valeurs apparaît plus d'une fois. Les `affected_ids` sont construits en concaténant les valeurs des champs concernés avec `:` comme séparateur.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Une colonne est absente | Non calculable |
| `error` | Des combinaisons dupliquées existent | `combinaisons dupliquées / total de lignes` |
| `pass` | Toutes les valeurs sont uniques | 0% |

---

## `check_field_presence(df, field, id_field)`

**Entrée** — un DataFrame, le champ à vérifier (`field`), et le champ (ou liste de champs) servant d'identifiant pour reporter les lignes en erreur (`id_field`).

**Vérification** — similaire à `check_id_presence`, mais les `affected_ids` sont construits à partir de `id_field` plutôt que de l'index. Si `id_field` est une liste, les valeurs sont concaténées avec `:`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `error` | Colonne absente | 100% |
| `error` | Valeurs manquantes détectées | `lignes vides / total` |
| `pass` | Toutes les valeurs sont présentes | 0% |

---

## `check_at_least_one_field_presence(df, fields, id_field)`

**Entrée** — un DataFrame, une liste de champs dont **au moins un** doit être renseigné par ligne (ex: `["route_short_name", "route_long_name"]`), et le champ identifiant.

**Vérification** — seules les colonnes effectivement présentes dans le DataFrame sont évaluées. Pour chaque ligne, vérifie qu'au moins une des colonnes existantes contient une valeur non vide. Si aucune des colonnes n'existe, toutes les lignes sont en erreur.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `error` | Aucune colonne n'existe | 100% |
| `error` | Des lignes ont tous leurs champs vides | `lignes sans aucun champ renseigné / total` |
| `pass` | Chaque ligne a au moins un champ renseigné | 0% |

---

## `check_format_field(df, field, format_config, id_field)`

**Entrée** — un DataFrame, le champ à valider, un dictionnaire `format_config` décrivant la règle de validation (`type`, `genre`, `valid_fields` ou `pattern`), et le champ identifiant.

**Vérification** — si le champ est absent et optionnel → `skip` ; si absent et requis → `error`. Sinon, chaque valeur non vide est validée selon son type :

| Type | Règle |
|---|---|
| `listing` | Doit appartenir à un ensemble de valeurs autorisées |
| `url` | Doit avoir un schéma et un netloc valides (`urlparse`) |
| `regex` | Doit correspondre au pattern compilé |
| `coordinates` | Doit être un float dans les bornes latitude (`-90/+90`) ou longitude (`-180/+180`) |
| `date` | Doit correspondre au format `YYYYMMDD` |
| `time` | Doit correspondre à `HH:MM:SS` avec minutes et secondes valides (heures > 23 autorisées) |
| `positive_integer` | Doit être un entier ≥ 0 |
| `positive_number` | Doit être un nombre ≥ 0 |
| `decimal` | Doit être convertible en `float` |

Les valeurs vides sont comptabilisées séparément des valeurs invalides dans `details`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Champ optionnel absent | Non calculable |
| `error` | Champ requis absent | 100% |
| `warning` | Valeurs invalides ou vides détectées | `(invalides + vides) / total` |
| `pass` | Toutes les valeurs sont valides | 0% |

!!! note "Détail des anomalies"
    En cas de `warning`, le champ `details` du `CheckResult` contient deux listes distinctes : `invalid` (valeurs présentes mais incorrectes) et `empty` (valeurs manquantes). Cela permet de distinguer une donnée absente d'une donnée mal formatée.

---

## `check_orphan_ids(df, id_field, ref_df, ref_field)`

**Entrée** — `df` le DataFrame de référence contenant les définitions d'IDs, `id_field` le champ d'ID dans `df`, `ref_df` le DataFrame qui référence ces IDs, `ref_field` le champ dans `ref_df` pointant vers `id_field`.

**Vérification** — calcule la différence entre les IDs référencés dans `ref_df` et ceux définis dans `df`. Un ID orphelin est un ID utilisé dans `ref_df` mais absent de `df` — c'est une rupture de référentiel critique.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Une colonne est absente | Non calculable |
| `error` | Des IDs orphelins existent | `IDs orphelins / total des IDs référencés dans ref_df` |
| `pass` | Tous les IDs référencés existent | 0% |

!!! warning "Criticité"
    Un ID orphelin est toujours un `error` — il représente une rupture de référentiel entre deux fichiers GTFS qui rend les données incohérentes.

---

## `check_unused_ids(df, id_field, ref_df, ref_field)`

**Entrée** — `df` le DataFrame contenant les définitions d'IDs, `id_field` le champ d'ID dans `df`, `ref_df` le DataFrame qui devrait les référencer, `ref_field` le champ dans `ref_df` pointant vers `id_field`.

**Vérification** — calcule la différence inverse : IDs définis dans `df` mais jamais référencés dans `ref_df`. Contrairement aux orphelins, ce n'est pas une rupture critique — les données sont simplement inutilisées.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Une colonne est absente | Non calculable |
| `warning` | Des IDs inutilisés existent | `IDs inutilisés / total des IDs définis dans df` |
| `pass` | Tous les IDs sont utilisés | 0% |

!!! note "Warning et non error"
    Un ID inutilisé génère un `warning` et non un `error` — les données sont superflues mais ne cassent aucune relation inter-fichiers.

---

## `check_accessibility_metrics(df, field, id_field)`

**Entrée** — un DataFrame et le champ d'accessibilité à analyser (ex: `"wheelchair_boarding"`).

**Vérification** — normalise toutes les valeurs en string, puis distingue trois catégories : accessibles (`1`), non accessibles (`2`), et non renseignés (`0`, vide, `nan`). Calcule deux taux :

- **Taux de renseignement** — % de lignes avec une valeur `1` ou `2` parmi le total
- **Taux d'accessibilité** — % de valeurs `1` parmi les lignes renseignées (`1` ou `2` uniquement)

**Sortie** — toujours `pass` (check informatif, jamais bloquant). Taux d'anomalie non applicable. Les métriques sont stockées dans `details` :

| Clé | Description |
|---|---|
| `completion_rate` | Taux de renseignement (%) |
| `accessibility_rate` | Taux d'accessibilité parmi les lignes renseignées (%) |
| `accessible_count` | Nombre de lignes avec valeur `1` |
| `not_accessible_count` | Nombre de lignes avec valeur `2` |
| `no_info_count` | Nombre de lignes non renseignées |

---

## Référence complète

::: audit_generic_functions