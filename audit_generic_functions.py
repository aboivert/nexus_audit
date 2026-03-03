import pandas as pd
from audit_models import CheckResult
import re
from urllib.parse import urlparse
from datetime import datetime


def is_truly_empty(value):
    """Vérifie si une valeur est vraiment vide (NaN, None, '', 'nan', etc.)"""
    if pd.isna(value):
        return True
    
    str_value = str(value).strip().lower()
    
    # Valeurs considérées comme vides
    empty_values = {'', 'nan', 'none', 'null', 'n/a', 'na', '#n/a'}
    
    return str_value in empty_values


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


def check_id_unicity(df: pd.DataFrame, fields: str | list[str], weight: float = 1.0) -> CheckResult:
    
    # Normalisation : on travaille toujours avec une liste
    fields_list = [fields] if isinstance(fields, str) else fields
    label_fields = ", ".join(fields_list)

    # Colonnes absentes
    missing_cols = [f for f in fields_list if f not in df.columns]
    if missing_cols:
        return CheckResult(
            check_id = f"mandatory.{'_'.join(fields_list)}_unicity",
            label    = f"Unicité des {label_fields}",
            category = "mandatory",
            status   = "skip",
            weight   = weight,
            message  = f"Colonne(s) absente(s) : {', '.join(missing_cols)}, unicité non vérifiable",
        )

    # Doublons
    duplicates = df[df.duplicated(fields_list, keep=False)]
    if not duplicates.empty:
        # Pour les affected_ids on concatène les valeurs des champs concernés
        affected_ids = (
            duplicates[fields_list]
            .astype(str)
            .agg(":".join, axis=1)
            .unique()
            .tolist()
        )
        return CheckResult(
            check_id       = f"mandatory.{'_'.join(fields_list)}_unicity",
            label          = f"Unicité des {label_fields}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"{len(affected_ids)} doublon(s) détecté(s) sur ({label_fields})",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = f"mandatory.{'_'.join(fields_list)}_unicity",
        label       = f"Unicité des {label_fields}",
        category    = "mandatory",
        status      = "pass",
        weight      = weight,
        message     = f"Tous les {label_fields} sont uniques",
        total_count = len(df),
    )


def check_field_presence(df: pd.DataFrame, field: str, id_field: str | list[str], weight: float = 1.0) -> CheckResult:
    
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
        id_fields = [id_field] if isinstance(id_field, str) else id_field
        affected_ids = (
            missing[id_fields].astype(str).agg(":".join, axis=1).tolist()
            if all(f in df.columns for f in id_fields)
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


def check_at_least_one_field_presence(df: pd.DataFrame, fields: list[str], id_field: str, weight: float = 1.0) -> CheckResult:
    """
    Vérifie qu'au moins un champ parmi la liste est renseigné pour chaque ligne.
    Ex : au moins route_short_name ou route_long_name pour chaque route.
    """
    label_fields = ", ".join(fields)

    # Aucune des colonnes n'existe
    existing_cols = [f for f in fields if f in df.columns]
    if not existing_cols:
        return CheckResult(
            check_id       = f"mandatory.{'_or_'.join(fields)}_presence",
            label          = f"Présence d'au moins un champ parmi {label_fields}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"Aucune des colonnes ({label_fields}) n'est présente",
            total_count    = len(df),
            affected_count = len(df),
        )

    # Lignes où tous les champs existants sont vides
    def all_empty(row):
        return all(
            pd.isna(row[f]) or str(row[f]).strip() == ""
            for f in existing_cols
        )

    problematic = df[df.apply(all_empty, axis=1)]

    if not problematic.empty:
        affected_ids = (
            problematic[id_field].astype(str).tolist()
            if id_field in df.columns
            else problematic.index.astype(str).tolist()
        )
        return CheckResult(
            check_id       = f"mandatory.{'_or_'.join(fields)}_presence",
            label          = f"Présence d'au moins un champ parmi {label_fields}",
            category       = "mandatory",
            status         = "error",
            weight         = weight,
            message        = f"{len(problematic)} ligne(s) sans aucune valeur parmi ({label_fields})",
            affected_ids   = affected_ids,
            affected_count = len(problematic),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = f"mandatory.{'_or_'.join(fields)}_presence",
        label       = f"Présence d'au moins un champ parmi {label_fields}",
        category    = "mandatory",
        status      = "pass",
        weight      = weight,
        message     = f"Chaque ligne a au moins un champ renseigné parmi ({label_fields})",
        total_count = len(df),
    )


def check_format_field(df: pd.DataFrame, field: str, format_config: dict, id_field: str | list[str], weight: float = 1.0) -> CheckResult:
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
        id_fields = [id_field] if isinstance(id_field, str) else id_field
        parts = [str(df.loc[idx, f]) if f in df.columns else "N/A" for f in id_fields]
        problematic_id = ":".join(parts)

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


def check_orphan_ids(df: pd.DataFrame, id_field: str, ref_df: pd.DataFrame, ref_field: str, weight: float = 1.0) -> CheckResult:
    """
    Vérifie qu'il n'y a pas d'IDs orphelins.
    Orphelin = ID référencé dans ref_df mais absent de df.
    Ex : agency_id dans routes.txt qui n'existe pas dans agency.txt.
    --> quand un fichier référence des IDs qui doivent exister ailleurs. C'est une erreur critique car ça casse les liaisons entre fichiers.
    """

    if id_field not in df.columns or ref_field not in ref_df.columns:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_orphan",
            label    = f"Absence d'orphelins {id_field}",
            category = "consistency",
            status   = "skip",
            weight   = weight,
            message  = f"Impossible de vérifier : colonne {id_field} ou {ref_field} absente",
        )

    source_ids = set(df[id_field].dropna().unique())
    ref_ids    = set(ref_df[ref_field].dropna().unique())
    orphans    = ref_ids - source_ids

    if orphans:
        return CheckResult(
            check_id       = f"consistency.{id_field}_no_orphan",
            label          = f"Absence d'orphelins {id_field}",
            category       = "consistency",
            status         = "error",
            weight         = weight,
            message        = f"{len(orphans)} {id_field} référencés mais absents",
            affected_ids   = [str(i) for i in orphans],
            affected_count = len(orphans),
            total_count    = len(ref_ids),
        )

    return CheckResult(
        check_id    = f"consistency.{id_field}_no_orphan",
        label       = f"Absence d'orphelins {id_field}",
        category    = "consistency",
        status      = "pass",
        weight      = weight,
        message     = f"Tous les {id_field} référencés existent",
        total_count = len(ref_ids),
    )


def check_unused_ids(df: pd.DataFrame, id_field: str, ref_df: pd.DataFrame, ref_field: str, weight: float = 1.0) -> CheckResult:
    """
    Vérifie qu'il n'y a pas d'IDs non utilisés.
    Non utilisé = ID présent dans df mais jamais référencé dans ref_df.
    Ex : agency_id dans agency.txt jamais utilisé dans routes.txt.
    -->  quand un fichier définit des IDs qui ne sont jamais utilisés ailleurs. C'est un warning — la donnée est inutile mais ne casse rien.
    """

    if id_field not in df.columns or ref_field not in ref_df.columns:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_unused",
            label    = f"Absence de {id_field} non utilisés",
            category = "consistency",
            status   = "skip",
            weight   = weight,
            message  = f"Impossible de vérifier : colonne {id_field} ou {ref_field} absente",
        )

    source_ids = set(df[id_field].dropna().unique())
    ref_ids    = set(ref_df[ref_field].dropna().unique())
    unused     = source_ids - ref_ids

    if unused:
        return CheckResult(
            check_id       = f"consistency.{id_field}_no_unused",
            label          = f"Absence de {id_field} non utilisés",
            category       = "consistency",
            status         = "warning",
            weight         = weight,
            message        = f"{len(unused)} {id_field} définis mais jamais utilisés",
            affected_ids   = [str(i) for i in unused],
            affected_count = len(unused),
            total_count    = len(source_ids),
        )

    return CheckResult(
        check_id    = f"consistency.{id_field}_no_unused",
        label       = f"Absence de {id_field} non utilisés",
        category    = "consistency",
        status      = "pass",
        weight      = weight,
        message     = f"Tous les {id_field} sont utilisés",
        total_count = len(source_ids),
    )