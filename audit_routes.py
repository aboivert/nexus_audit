import pandas as pd
from audit_models import CheckResult
from audit_generic_functions import check_id_presence, check_id_unicity, check_field_presence, check_format_field, check_orphan_ids, check_unused_ids, check_at_least_one_field_presence
import re

format = {'route_type':{'genre':'required','description':"Validité des types de route", 'type':'listing', 'valid_fields':{0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 300, 301, 302, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 500, 600, 601, 602, 603, 604, 605, 606, 607, 700, 701, 702, 703, 704, 705, 706, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700 }},
          'route_color':{'genre':'optional','description':"Validité des couleurs de route", 'type':'regex', 'pattern':re.compile(r'^[0-9A-Fa-f]{6}$')},
          'route_text_color':{'genre':'optional','description':"Validité des couleurs de texte de route", 'type':'regex', 'pattern':re.compile(r'^[0-9A-Fa-f]{6}$')},
          'route_url':{'genre':'optional','description':"Validité des URL", 'type':'url'},
          'continuous_pickup':{'genre':'optional','description':"Validité des continuous_pickup", 'type':'listing', 'valid_fields':{0, 1, 2, 3}},
          'continuous_drop_off':{'genre':'optional','description':"Validité des continuous_drop_off", 'type':'listing', 'valid_fields':{0, 1, 2, 3}},
}


def _check_route_id(df: pd.DataFrame) -> list[CheckResult]:

    return [
        check_id_presence(df, "route_id", weight=3.0),
        check_id_unicity(df,  "route_id", weight=3.0),
    ]

def _check_mandatory_fields(df: pd.DataFrame, agency_df: pd.DataFrame) -> list[CheckResult]:
    """
    Vérifie la présence des champs obligatoires route_id, trip_id.
    """
    return [
        check_at_least_one_field_presence(df, ["route_short_name", "route_long_name"], "route_id", weight=3.0),
        check_field_presence(df, "route_type", "route_id", weight=1.0),
        _check_agency_id_presence(df, agency_df),
        _check_agency_id_existence(df, agency_df),
    ]


def _check_data_format(df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_format_field(df, "route_type", format["route_type"], "route_id", weight=1.0),
        check_format_field(df, "route_color", format["route_color"], "route_id", weight=1.0),
        check_format_field(df, "route_text_color", format["route_text_color"], "route_id", weight=1.0),
        check_format_field(df, "route_url", format["route_url"], "route_id", weight=1.0),
        check_format_field(df, "continuous_pickup", format["continuous_pickup"], "route_id", weight=1.0),
        check_format_field(df, "continuous_drop_off", format["continuous_drop_off"], "route_id", weight=1.0),
    ]


def _check_data_consistency(df: pd.DataFrame, trips_df: pd.DataFrame) -> list[CheckResult]:
    return [
        check_orphan_ids(df, "route_id", trips_df, "route_id", weight=2.0),
        check_unused_ids(df, "route_id", trips_df, "route_id", weight=2.0),
        _check_duplicate_route_names(df, "route_short_name"),
        _check_duplicate_route_names(df, "route_long_name"),
    ]


def _check_accessibility(df: pd.DataFrame) -> list[CheckResult]:
    return [
        _check_color_contrast(df),
    ]


def _check_agency_id_presence(df: pd.DataFrame, agency_df: pd.DataFrame | None) -> CheckResult:
    """
    Vérifie la présence du champ agency_id dans routes.txt.
    Obligatoire seulement si plusieurs agences dans agency.txt.
    """

    # agency.txt absent → on ne peut pas savoir
    if agency_df is None:
        return CheckResult(
            check_id = "routes.mandatory.agency_id_presence",
            label    = "Présence du champ agency_id",
            category = "mandatory",
            status   = "skip",
            weight   = 3.0,
            message  = "agency.txt absent, impossible de déterminer si agency_id est obligatoire",
        )

    # Une seule agence → agency_id optionnel
    if len(agency_df) <= 1:
        return CheckResult(
            check_id = "routes.mandatory.agency_id_presence",
            label    = "Présence du champ agency_id",
            category = "mandatory",
            status   = "skip",
            weight   = 3.0,
            message  = "agency_id optionnel (une seule agence)",
        )

    # Plusieurs agences → on vérifie la présence
    return check_field_presence(df, "agency_id", "route_id", weight=3.0)


def _check_agency_id_existence(df: pd.DataFrame, agency_df: pd.DataFrame | None) -> CheckResult:
    """
    Vérifie que les agency_id référencés dans routes.txt existent dans agency.txt.
    """

    # agency.txt absent → pas de référentiel
    if agency_df is None:
        return CheckResult(
            check_id = "routes.mandatory.agency_id_existence",
            label    = "Existence des agency_id dans agency.txt",
            category = "mandatory",
            status   = "skip",
            weight   = 3.0,
            message  = "agency.txt absent, vérification non applicable",
        )

    # agency_id absent de routes.txt → rien à vérifier
    if "agency_id" not in df.columns:
        return CheckResult(
            check_id = "routes.mandatory.agency_id_existence",
            label    = "Existence des agency_id dans agency.txt",
            category = "mandatory",
            status   = "skip",
            weight   = 3.0,
            message  = "agency_id absent de routes.txt, vérification non applicable",
        )

    return check_orphan_ids(agency_df, "agency_id", df, "agency_id", weight=3.0, category="mandatory")


def _check_duplicate_route_names(df: pd.DataFrame, field: str) -> CheckResult:
    """
    Détecte les noms de routes dupliqués par agence pour un champ donné.
    (route_short_name ou route_long_name)
    """
    if field not in df.columns:
        return CheckResult(
            check_id = f"routes.consistency.duplicate_{field}",
            label    = f"Absence de {field} dupliqués par agence",
            category = "consistency",
            status   = "skip",
            weight   = 1.0,
            message  = f"Colonne {field} absente",
        )

    # Normalisation sans copie du DataFrame
    normalized = df[field].astype(str).str.strip()

    # Clé de groupement : agency_id + field ou uniquement field
    if "agency_id" in df.columns:
        group_key = df["agency_id"].astype(str) + "||" + normalized
    else:
        group_key = normalized

    # Détection des doublons en excluant les valeurs vides
    duplicates = df[
        group_key.duplicated(keep=False) &
        normalized.notna() &
        (normalized != "") &
        (normalized != "nan")
    ]

    if not duplicates.empty:
        affected_ids = (
            duplicates["route_id"].astype(str).tolist()
            if "route_id" in df.columns
            else duplicates.index.astype(str).tolist()
        )
        return CheckResult(
            check_id       = f"routes.consistency.duplicate_{field}",
            label          = f"Absence de {field} dupliqués par agence",
            category       = "consistency",
            status         = "warning",
            weight         = 1.0,
            message        = f"{len(duplicates)} route(s) avec un {field} dupliqué au sein d'une même agence",
            affected_ids   = affected_ids,
            affected_count = len(duplicates),
            total_count    = len(df),
        )

    return CheckResult(
        check_id    = f"routes.consistency.duplicate_{field}",
        label       = f"Absence de {field} dupliqués par agence",
        category    = "consistency",
        status      = "pass",
        weight      = 1.0,
        message     = f"Aucun {field} dupliqué détecté",
        total_count = len(df),
    )


def _check_color_contrast(df: pd.DataFrame) -> CheckResult:
    """
    Vérifie le contraste WCAG (ratio >= 4.5:1) entre route_color et route_text_color.
    """

    # Colonnes absentes → skip
    if "route_color" not in df.columns or "route_text_color" not in df.columns:
        return CheckResult(
            check_id = "routes.accessibility.color_contrast",
            label    = "Contraste WCAG entre route_color et route_text_color",
            category = "accessibility",
            status   = "skip",
            weight   = 1.0,
            message  = "Colonnes route_color et/ou route_text_color absentes",
        )

    def relative_luminance(hex_color: str) -> float:
        """Calcule la luminance relative d'une couleur hexadécimale."""
        hex_color = str(hex_color).strip().lstrip('#')
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255

        def gamma(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * gamma(r) + 0.7152 * gamma(g) + 0.0722 * gamma(b)

    def contrast_ratio(hex1: str, hex2: str) -> float:
        """Calcule le ratio de contraste entre deux couleurs."""
        l1 = relative_luminance(hex1)
        l2 = relative_luminance(hex2)
        lighter = max(l1, l2)
        darker  = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    affected_ids = []
    details      = {}
    total_count  = 0

    for _, row in df.iterrows():
        route_color      = str(row["route_color"]).strip().lstrip('#')
        route_text_color = str(row["route_text_color"]).strip().lstrip('#')
        route_id         = str(row["route_id"]) if "route_id" in df.columns else str(row.name)

        # Valeurs vides ou invalides → on ignore
        if len(route_color) != 6 or len(route_text_color) != 6:
            continue

        try:
            ratio = round(contrast_ratio(route_color, route_text_color), 2)
            total_count += 1

            if ratio < 4.5:
                affected_ids.append(route_id)
                details[route_id] = {
                    "route_color":      route_color,
                    "route_text_color": route_text_color,
                    "ratio":            ratio,
                }
        except (ValueError, TypeError):
            continue

    if affected_ids:
        return CheckResult(
            check_id       = "routes.accessibility.color_contrast",
            label          = "Contraste WCAG entre route_color et route_text_color",
            category       = "accessibility",
            status         = "warning",
            weight         = 1.0,
            message        = f"{len(affected_ids)} route(s) avec un ratio de contraste insuffisant (< 4.5:1)",
            affected_ids   = affected_ids,
            affected_count = len(affected_ids),
            total_count    = total_count,
            details        = details,
        )

    return CheckResult(
        check_id    = "routes.accessibility.color_contrast",
        label       = "Contraste WCAG entre route_color et route_text_color",
        category    = "accessibility",
        status      = "pass",
        weight      = 1.0,
        message     = "Tous les contrastes de couleur sont suffisants (>= 4.5:1)",
        total_count = total_count,
    )