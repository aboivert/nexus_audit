# Routes

Ce module audite le fichier `routes.txt` selon quatre axes : la présence des champs obligatoires, la validité des formats, la cohérence inter-fichiers, et l'accessibilité visuelle.

---

## Audits effectués

### 1. Champs obligatoires (`mandatory`)

Vérifie la présence et l'unicité des champs clés, ainsi que la cohérence avec `agency.txt`.

| Check | Poids recommandé| Condition |
|---|---|---|
| Présence de `route_id` | 4.0 | Toujours |
| Unicité de `route_id` | 4.0 | Toujours |
| Présence d'au moins un nom (`route_short_name` ou `route_long_name`) | 2.0 | Toujours |
| Présence de `route_type` | 2.0 | Toujours |
| Présence de `agency_id` | 2.0 | Seulement si `agency.txt` contient plusieurs agences |
| Existence des `agency_id` dans `agency.txt` | 2.0 | Seulement si `agency.txt` est chargé et `agency_id` présent |

!!! note "Nom de route"
    La spec GTFS exige qu'au moins l'un des deux champs `route_short_name` ou `route_long_name` soit renseigné. Les deux peuvent être absents simultanément — c'est ce cas qui est détecté.

!!! warning "Dépendance inter-fichiers"
    Les checks sur `agency_id` passent en `skip` si `agency.txt` est absent, ou si une seule agence est définie (auquel cas `agency_id` est optionnel).

---

### 2. Validité des formats (`format`)

Vérifie que les valeurs respectent les formats attendus.

| Champ | Poids recommandé | Règle |
|---|---|---|
| `route_type` | 2.0 | Doit être un code de type de transport valide (GTFS standard et étendu) |
| `route_color` | 2.0 | Doit être une couleur hexadécimale à 6 caractères (ex: `FF5733`) |
| `route_text_color` | 2.0 | Doit être une couleur hexadécimale à 6 caractères |
| `route_url` | 1.0 | Doit être une URL bien formée |
| `continuous_pickup` | 1.0 | Doit valoir `0`, `1`, `2` ou `3` |
| `continuous_drop_off` | 1.0 | Doit valoir `0`, `1`, `2` ou `3` |

---

### 3. Cohérence inter-fichiers (`consistency`)

Vérifie l'utilisation des `route_id` dans `trips.txt` et détecte les noms de routes dupliqués.

| Check | Poids recommandé | Description |
|---|---|---|
| `route_id` orphelins | 3.0 | Détecte les `route_id` présents dans `trips.txt` mais absents de `routes.txt` |
| `route_id` inutilisés | 2.0 | Détecte les `route_id` définis dans `routes.txt` mais non référencés dans `trips.txt` |
| Doublons de `route_short_name` | 1.0 | Détecte les noms courts identiques au sein d'une même agence |
| Doublons de `route_long_name` | 1.0 | Détecte les noms longs identiques au sein d'une même agence |

!!! note "Détection des doublons par agence"
    La comparaison des noms est faite par agence (groupée sur `agency_id` + nom). Si `agency_id` est absent, la comparaison se fait globalement sur tout le fichier.

!!! warning "Dépendance inter-fichiers"
    La détection des `route_id` orphelins et inutilisés nécessite que `trips.txt` soit chargé en amont.

---

### 4. Accessibilité (`accessibility`)

Vérifie la lisibilité visuelle des couleurs de route.

| Check | Poids recommandé | Description |
|---|---|---|
| Contraste WCAG | 1.0 | Vérifie que le ratio de contraste entre `route_color` et `route_text_color` est supérieur ou égal à **4.5:1** (norme WCAG AA) |

!!! note "Calcul du contraste"
    Le ratio est calculé selon la formule WCAG à partir de la luminance relative de chaque couleur. Les lignes dont les couleurs sont absentes ou invalides sont ignorées. Un ratio inférieur à 4.5:1 génère un statut `warning`.

---

## Fonctions spécifiques

### `_check_agency_id_presence(df, agency_df)`

**Entrée** — le DataFrame de `routes.txt` et le DataFrame de `agency.txt` (ou `None` si absent).

**Vérification** — la règle GTFS stipule que `agency_id` n'est obligatoire que si le réseau compte plusieurs agences. Si `agency.txt` est absent, impossible de trancher. Si une seule agence est présente, le champ est optionnel. Au-delà d'une agence, délègue à `check_field_presence`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | `agency.txt` absent | Non calculable |
| `skip` | Une seule agence dans `agency.txt` | Non applicable |
| `error` | `agency_id` absent ou vide dans `routes.txt` (plusieurs agences) | `lignes vides / total` |
| `pass` | Toutes les lignes ont un `agency_id` | 0% |

---

### `_check_agency_id_existence(df, agency_df)`

**Entrée** — le DataFrame de `routes.txt` et le DataFrame de `agency.txt` (ou `None` si absent).

**Vérification** — vérifie que chaque `agency_id` référencé dans `routes.txt` existe bien dans `agency.txt`. Délègue à `check_orphan_ids`. Si `agency.txt` est absent ou si la colonne `agency_id` est absente de `routes.txt`, le check est ignoré.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | `agency.txt` absent | Non calculable |
| `skip` | Colonne `agency_id` absente de `routes.txt` | Non calculable |
| `error` | Des `agency_id` n'existent pas dans `agency.txt` | `IDs orphelins / total des agency_id référencés dans routes.txt` |
| `pass` | Tous les `agency_id` existent dans `agency.txt` | 0% |

---

### `_check_duplicate_route_names(df, field)`

**Entrée** — le DataFrame de `routes.txt` et le nom du champ à vérifier (`route_short_name` ou `route_long_name`).

**Vérification** — normalise les valeurs (strip), puis construit une clé de groupement `agency_id || field` si `agency_id` est présent, ou uniquement `field` sinon. Détecte les lignes dont la clé est dupliquée, en excluant les valeurs vides ou `nan`. Le check est donc **par agence** : deux routes de deux agences différentes peuvent partager le même nom sans déclencher d'anomalie.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonne `field` absente | Non calculable |
| `warning` | Des noms sont dupliqués au sein d'une même agence | `routes dupliquées / total de lignes` |
| `pass` | Aucun doublon détecté | 0% |

!!! note "Warning et non error"
    Un nom dupliqué est ambigu mais ne rompt pas la cohérence du référentiel — d'où un `warning`.

---

### `_check_color_contrast(df)`

**Entrée** — le DataFrame de `routes.txt`.

**Vérification** — pour chaque ligne ayant des valeurs valides (exactement 6 caractères hexadécimaux) dans `route_color` et `route_text_color`, calcule la luminance relative de chaque couleur selon la formule WCAG, puis le ratio de contraste `(L_lighter + 0.05) / (L_darker + 0.05)`. Un ratio inférieur à **4.5:1** est insuffisant. Les lignes avec des valeurs absentes ou invalides sont ignorées. Le `total_count` ne compte que les lignes effectivement évaluées. Le champ `details` contient pour chaque route en anomalie les valeurs `route_color`, `route_text_color` et `ratio`.

**Sortie**

| Statut | Condition | Taux d'anomalie |
|---|---|---|
| `skip` | Colonnes `route_color` ou `route_text_color` absentes | Non calculable |
| `warning` | Des routes ont un ratio de contraste < 4.5:1 | `routes non conformes / lignes évaluées` |
| `pass` | Tous les ratios sont ≥ 4.5:1 | 0% |

---

## Référence complète

::: audit_routes