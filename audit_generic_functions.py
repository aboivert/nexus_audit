"""
GTFS audit generic functions.
Defines generic functions used across various GTFS files.
"""

import pandas as pd
from audit_models import CheckResult
import re
from urllib.parse import urlparse
from datetime import datetime


def is_truly_empty(value):
    """Returns True if value is empty (NaN, None, '', 'nan', 'n/a', etc.)."""
    if pd.isna(value):
        return True
    
    str_value = str(value).strip().lower()
    
    # Valeurs considérées comme vides
    empty_values = {'', 'nan', 'none', 'null', 'n/a', 'na', '#n/a'}
    
    return str_value in empty_values


def check_id_presence(df: pd.DataFrame, field: str, weight: float) -> CheckResult:
    """
    Checks that a field is present and has no missing values in a DataFrame.

    :param df: Target DataFrame.
    :param field: Field name to check.
    :param weight: Check weight for scoring.
    """ 
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


def check_id_unicity(df: pd.DataFrame, fields: str | list[str], weight: float) -> CheckResult:
    """
    Checks that one or more fields form a unique key across all rows.

    :param df: Target DataFrame.
    :param fields: Field name or list of field names to check for duplicates.
    :param weight: Check weight for scoring.
    """   
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


def check_field_presence(df: pd.DataFrame, field: str, id_field: str | list[str], weight: float) -> CheckResult:
    """
    Checks that a field is present and non-empty, returning affected IDs from a reference field.

    :param df: Target DataFrame.
    :param field: Field name to check.
    :param id_field: Field(s) used to identify problematic rows in the result.
    :param weight: Check weight for scoring.
    """   
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


def check_at_least_one_field_presence(df: pd.DataFrame, fields: list[str], id_field: str, weight: float) -> CheckResult:
    """
    Checks that each row has at least one non-empty value among the given fields.

    :param df: Target DataFrame.
    :param fields: List of fields where at least one must be filled.
    :param id_field: Field used to identify problematic rows.
    :param weight: Check weight for scoring.
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


def check_format_field(df: pd.DataFrame, field: str, format_config: dict, id_field: str | list[str], weight: float, category: str = "format") -> CheckResult:
    """
    Checks the format validity of a field. Supports types: listing, url, regex, coordinates, date, time, positive_integer, positive_number, decimal.
    Skips optional absent fields, errors on required absent fields.

    :param df: Target DataFrame.
    :param field: Field name to validate.
    :param format_config: Dict describing expected format (type, genre, description, etc.).
    :param id_field: Field(s) used to identify problematic rows.
    :param weight: Check weight for scoring.
    :param category: Check category (default: 'format').
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
                category = category,
                status   = "skip",
                weight   = weight,
                message  = f"Champ optionnel {field} absent",
            )
        # Champ requis absent → error
        return CheckResult(
            check_id       = f"format.{field}_valid",
            label          = format_config["description"],
            category       = category,
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

        elif format_config["type"] == "positive_integer":
            try:
                val = int(str(data).strip())
                if val < 0:
                    invalid_ids.append(f"{problematic_id}:{data}")
            except (ValueError, TypeError):
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "positive_number":
            try:
                val = float(str(data).strip())
                if val < 0:
                    invalid_ids.append(f"{problematic_id}:{data}")
            except (ValueError, TypeError):
                invalid_ids.append(f"{problematic_id}:{data}")

        elif format_config["type"] == "decimal":
            try:
                float(str(data).strip())
            except (ValueError, TypeError):
                invalid_ids.append(f"{problematic_id}:{data}")

    # Résultat
    affected     = invalid_ids + empty_ids
    total        = len(df)
    affected_count = len(affected)

    if affected:
        return CheckResult(
            check_id       = f"format.{field}_valid",
            label          = format_config["description"],
            category       = category,
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
        category    = category,
        status      = "pass",
        weight      = weight,
        message     = f"Tous les formats {field} sont valides",
        total_count = total,
    )


def check_orphan_ids(df: pd.DataFrame, id_field: str, ref_df: pd.DataFrame, ref_field: str, weight: float, category: str = "consistency") -> CheckResult:
    """
    Checks for orphan IDs: IDs referenced in ref_df but absent from df.
    Errors are critical as they break cross-file relationships.

    :param df: DataFrame containing the reference ID definitions.
    :param id_field: ID field in df.
    :param ref_df: DataFrame referencing those IDs.
    :param ref_field: Field in ref_df pointing to id_field.
    :param weight: Check weight for scoring.
    :param category: Check category (default: 'consistency').
    """
    if df is None:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_orphan",
            label    = f"Absence d'orphelins {id_field}",
            category = category,
            status   = "error",
            weight   = weight,
            message  = "Fichier source absent, impossible de vérifier les orphelins",
        )

    if ref_df is None:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_orphan",
            label    = f"Absence d'orphelins {id_field}",
            category = category,
            status   = "error",
            weight   = weight,
            message  = "Fichier de référence absent, impossible de vérifier les orphelins",
        )

    if id_field not in df.columns or ref_field not in ref_df.columns:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_orphan",
            label    = f"Absence d'orphelins {id_field}",
            category = category,
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
            category       = category,
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
        category    = category,
        status      = "pass",
        weight      = weight,
        message     = f"Tous les {id_field} référencés existent",
        total_count = len(ref_ids),
    )


def check_unused_ids(df: pd.DataFrame, id_field: str, ref_df: pd.DataFrame, ref_field: str, weight: float, category: str = "consistency") -> CheckResult:
    """
    Checks for unused IDs: IDs defined in df but never referenced in ref_df.
    Results in a warning — data is useless but not breaking.

    :param df: DataFrame containing the ID definitions.
    :param id_field: ID field in df.
    :param ref_df: DataFrame that should reference those IDs.
    :param ref_field: Field in ref_df pointing to id_field.
    :param weight: Check weight for scoring.
    :param category: Check category (default: 'consistency').
    """
    if df is None:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_unused",
            label    = f"Absence de {id_field} non utilisés",
            category = category,
            status   = "error",
            weight   = weight,
            message  = "Fichier source absent, impossible de vérifier les non utilisés",
        )

    if ref_df is None:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_unused",
            label    = f"Absence de {id_field} non utilisés",
            category = category,
            status   = "error",
            weight   = weight,
            message  = "Fichier de référence absent, impossible de vérifier les non utilisés",
        )

    if id_field not in df.columns or ref_field not in ref_df.columns:
        return CheckResult(
            check_id = f"consistency.{id_field}_no_unused",
            label    = f"Absence de {id_field} non utilisés",
            category = category,
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
            category       = category,
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
        category    = category,
        status      = "pass",
        weight      = weight,
        message     = f"Tous les {id_field} sont utilisés",
        total_count = len(source_ids),
    )


def check_accessibility_metrics(df: pd.DataFrame, field: str, id_field: str | list[str], weight: float) -> CheckResult:
    """
    Analyses a UFR accessibility field: computes completion rate (values 1 & 2)
    and accessibility rate (value 1 among 1 & 2).

    :param df: Target DataFrame.
    :param field: Accessibility field to analyse.
    :param id_field: Field(s) used to identify rows.
    :param weight: Check weight for scoring.
    """
    # Colonne absente → skip
    if field not in df.columns:
        return CheckResult(
            check_id = f"accessibility.{field}_metrics",
            label    = f"Analyse accessibilité {field}",
            category = "accessibility",
            status   = "skip",
            weight   = weight,
            message  = f"Colonne {field} absente",
        )

    total_count = len(df)

    # Normalisation des valeurs en string pour uniformiser
    values = df[field].astype(str).str.strip()

    no_info_count        = int((values.isin(['0', '', 'nan', 'none'])).sum())
    accessible_count     = int((values == '1').sum())
    not_accessible_count = int((values == '2').sum())

    # Taux de renseignement = % de valeurs 1 ou 2
    rensigned_count = accessible_count + not_accessible_count
    completion_rate = round((rensigned_count / total_count) * 100, 1) if total_count > 0 else 0.0

    # Taux d'accessibilité = % de valeurs 1 parmi 1 et 2
    accessibility_rate = round((accessible_count / rensigned_count) * 100, 1) if rensigned_count > 0 else 0.0

    return CheckResult(
        check_id       = f"accessibility.{field}_metrics",
        label          = f"Analyse accessibilité {field}",
        category       = "accessibility",
        status         = "pass",
        weight         = weight,
        message        = f"Taux de renseignement : {completion_rate}%, Taux d'accessibilité : {accessibility_rate}%",
        affected_count = no_info_count,
        total_count    = total_count,
        details        = {
            "completion_rate":    completion_rate,
            "accessibility_rate": accessibility_rate,
            "accessible_count":   accessible_count,
            "not_accessible_count": not_accessible_count,
            "no_info_count":      no_info_count,
        }
    )