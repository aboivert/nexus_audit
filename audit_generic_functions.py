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