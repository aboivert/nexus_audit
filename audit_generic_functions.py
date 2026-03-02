import pandas as pd
from audit_models import CheckResult

def check_id_presence(df: pd.DataFrame, field: str, weight: float = 1.0) -> CheckResult:
    
    # Colonne absente
    if field not in df.columns:
        return CheckResult(
            check_id       = f"mandatory.{field}_presence",
            label          = f"Présence du champ {field}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"Colonne {field} absente",
            total_count    = len(df),
            affected_count = len(df),
        )
    
    # Valeurs vides
    missing = df[df[field].isna() | (df[field] == "")]
    if not missing.empty:
        return CheckResult(
            check_id       = f"mandatory.{field}_presence",
            label          = f"Présence du champ {field}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"{len(missing)} valeurs manquantes pour {field}",
            affected_ids   = missing.index.astype(str).tolist(),
            affected_count = len(missing),
            total_count    = len(df),
        )
    
    return CheckResult(
        check_id    = f"mandatory.{field}_presence",
        label       = f"Présence du champ {field}",
        category    = "mandatory",
        status      = "pass",
        weight      = weight,
        message     = f"Toutes les valeurs {field} sont présentes",
        total_count = len(df),
    )


def check_id_unicity(df: pd.DataFrame, field: str, weight: float = 1.0) -> CheckResult:
    
    # Colonne absente → non vérifiable
    if field not in df.columns:
        return CheckResult(
            check_id = f"mandatory.{field}_unicity",
            label    = f"Unicité des {field}",
            category = "mandatory",
            status   = "skip",
            weight   = weight,
            message  = f"Colonne {field} absente, unicité non vérifiable",
        )
    
    # Doublons
    duplicates = df[df.duplicated(field, keep=False) & df[field].notna()]
    if not duplicates.empty:
        duplicate_ids = duplicates[field].unique().tolist()
        return CheckResult(
            check_id       = f"mandatory.{field}_unicity",
            label          = f"Unicité des {field}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"{len(duplicate_ids)} {field} en doublon",
            affected_ids   = [str(i) for i in duplicate_ids],
            affected_count = len(duplicate_ids),
            total_count    = df[field].notna().sum(),
        )
    
    return CheckResult(
        check_id    = f"mandatory.{field}_unicity",
        label       = f"Unicité des {field}",
        category    = "mandatory",
        status      = "pass",
        weight      = weight,
        message     = f"Tous les {field} sont uniques",
        total_count = df[field].notna().sum(),
    )


def check_field_presence(df: pd.DataFrame, field: str, id_field: str, weight: float = 1.0) -> CheckResult:
    
    # Colonne absente
    if field not in df.columns:
        return CheckResult(
            check_id       = f"mandatory.{field}_presence",
            label          = f"Présence du champ {field}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"Colonne {field} absente",
            total_count    = len(df),
            affected_count = len(df),
        )
    
    # Valeurs vides
    missing = df[df[field].isna() | (df[field] == "")]
    if not missing.empty:
        affected_ids = (
            missing[id_field].astype(str).tolist()
            if id_field in df.columns
            else missing.index.astype(str).tolist()
        )
        return CheckResult(
            check_id       = f"mandatory.{field}_presence",
            label          = f"Présence du champ {field}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"{len(missing)} valeurs manquantes pour {field}",
            affected_ids   = affected_ids,
            affected_count = len(missing),
            total_count    = len(df),
        )
    
    # Tout va bien
    return CheckResult(
        check_id    = f"mandatory.{field}_presence",
        label       = f"Présence du champ {field}",
        category    = "mandatory",
        status      = "pass",
        weight      = weight,
        message     = f"Toutes les valeurs {field} sont présentes",
        total_count = len(df),
    )


def check_format_field(df: pd.DataFrame, field: str, format_config: dict, id_field: str, weight: float = 1.0) -> CheckResult:
    """
    Vérifie la validité du format d'un champ.
    Supporte les types : listing, url, regex, coordinates, date, time.
    """
    invalid_ids = []
    empty_ids   = []

    # Colonne absente
    if field not in df.columns:
        # Champ optionnel absent → skip
        if format_config["genre"] == "optional":
            return CheckResult(
                check_id = f"format.{field}_valid",
                label    = format_config["description"],
                category = "format",
                status   = "skip",
                weight   = weight,
                message  = f"Champ optionnel {field} absent",
            )
        # Champ requis absent → error
        return CheckResult(
            check_id       = f"format.{field}_valid",
            label          = format_config["description"],
            category       = "format",
            status         = "error",
            weight         = weight,
            message        = f"Champ {field} absent",
            total_count    = len(df),
            affected_count = len(df),
        )

    # Détection des anomalies (ta logique existante, inchangée)
    for idx, data in df[field].items():
        problematic_id = str(df.loc[idx, id_field]) if id_field in df.columns else str(idx)

        if is_truly_empty(data):
            empty_ids.append(problematic_id)
            continue

        if format_config["type"] == "listing":
            if str(data) not in format_config["valid_fields"]:
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "url":
            try:
                parsed = urlparse(str(data))
                if not all([parsed.scheme, parsed.netloc]):
                    invalid_ids.append(f"{problematic_id}:{data}")
            except:
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "regex":
            if not format_config["pattern"].match(str(data)):
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "coordinates":
            coord_type = format_config.get("coord_type", "latitude")
            try:
                coord_value = float(data)
                if coord_type == "latitude" and not (-90 <= coord_value <= 90):
                    invalid_ids.append(f"{problematic_id}:{data}")
                elif coord_type == "longitude" and not (-180 <= coord_value <= 180):
                    invalid_ids.append(f"{problematic_id}:{data}")
            except (ValueError, TypeError):
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "date":
            date_format = format_config.get("date_format", "%Y%m%d")
            try:
                datetime.strptime(str(data).strip(), date_format)
            except:
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "time":
            time_str = str(data).strip()
            try:
                if not re.match(r'^\d{1,2}:\d{2}:\d{2}$', time_str):
                    invalid_ids.append(f"{problematic_id}:{data}")
                else:
                    parts    = time_str.split(":")
                    minutes  = int(parts[1])
                    seconds  = int(parts[2])
                    if not (0 <= minutes <= 59) or not (0 <= seconds <= 59):
                        invalid_ids.append(f"{problematic_id}:{data}")
            except:
                invalid_ids.append(f"{problematic_id}:{data}")

    # Résultat
    affected     = invalid_ids + empty_ids
    total        = len(df)
    affected_count = len(affected)

    if affected:
        return CheckResult(
            check_id       = f"format.{field}_valid",
            label          = format_config["description"],
            category       = "format",
            status         = "warning",
            weight         = weight,
            message        = f"{len(invalid_ids)} valeurs invalides, {len(empty_ids)} valeurs vides pour {field}",
            affected_ids   = affected,
            affected_count = affected_count,
            total_count    = total,
            details        = {"invalid": invalid_ids, "empty": empty_ids},
        )

    return CheckResult(
        check_id    = f"format.{field}_valid",
        label       = format_config["description"],
        category    = "format",
        status      = "pass",
        weight      = weight,
        message     = f"Tous les formats {field} sont valides",
        total_count = total,
    )