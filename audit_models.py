"""
Modèles de données pour les audits GTFS.
Définit les structures CheckResult, CategoryScore et FileScore.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    """
    Résultat d'un check individuel.
    Retourné par chaque fonction d'audit.
    """
    check_id        : str                    # Identifiant unique, ex: "agency.format.timezone"
    label           : str                    # Description lisible, ex: "Validité du fuseau horaire"
    category        : str                    # "mandatory" | "format" | "consistency" | "stats"
    status          : str                    # "pass" | "warning" | "error" | "skip"
    weight          : float                  # Pondération définie par l'auteur du check
    message         : str                    # Explication humaine du résultat
    affected_ids    : list[str]  = field(default_factory=list)   # IDs des éléments problématiques
    affected_count  : int        = 0         # Nombre d'éléments en anomalie
    total_count     : int        = 0         # Nombre total d'éléments évalués
    recommendations : list[str]  = field(default_factory=list)   # Actions correctives (plus tard)
    details         : Optional[dict] = None  # Données brutes optionnelles

    @property
    def anomaly_rate(self) -> Optional[float]:
        """Taux d'anomalie en %, calculé automatiquement."""
        if self.total_count > 0:
            return round((self.affected_count / self.total_count) * 100, 2)
        return None

    @property
    def score(self) -> Optional[float]:
        """
        Score de 0 à 100, calculé automatiquement selon deux modes :
        - Si on a des stats (affected_count + total_count) → taux de réussite
        - Sinon → pénalité fixe selon le statut
        Les checks 'skip' n'ont pas de score (retourne None).
        """
        if self.status == "skip":
            return None

        # Mode 1 — Taux de réussite
        if self.total_count > 0:
            return round(100 * (1 - self.affected_count / self.total_count), 1)

        # Mode 2 — Pénalité fixe
        return {
            "pass":    100.0,
            "warning":  60.0,
            "error":     0.0,
        }.get(self.status, 0.0)


@dataclass
class CategoryScore:
    """
    Score agrégé pour une catégorie de checks au sein d'un fichier.
    Construit à partir d'une liste de CheckResult.
    """
    category : str
    checks   : list[CheckResult] = field(default_factory=list)

    @property
    def score(self) -> Optional[float]:
        """Moyenne pondérée des scores des checks éligibles (hors skip)."""
        eligible = [c for c in self.checks if c.score is not None and c.weight > 0]
        if not eligible:
            return None
        weighted_sum = sum(c.score * c.weight for c in eligible)
        total_weight = sum(c.weight for c in eligible)
        return round(weighted_sum / total_weight, 1)

    @property
    def total_weight(self) -> float:
        """Somme des weights des checks éligibles. Sert au calcul du FileScore."""
        return sum(c.weight for c in self.checks if c.score is not None and c.weight > 0)


@dataclass
class FileScore:
    """
    Score global d'un fichier GTFS.
    Construit à partir d'une liste de CategoryScore.
    """
    file       : str
    categories : list[CategoryScore] = field(default_factory=list)

    @property
    def score(self) -> Optional[float]:
        """Moyenne pondérée des catégories (pondérée par leur total_weight)."""
        eligible = [cat for cat in self.categories if cat.score is not None]
        if not eligible:
            return None
        weighted_sum = sum(cat.score * cat.total_weight for cat in eligible)
        total_weight = sum(cat.total_weight for cat in eligible)
        if total_weight == 0:
            return None
        return round(weighted_sum / total_weight, 1)

    @property
    def grade(self) -> Optional[str]:
        """Note littérale calculée à partir du score."""
        s = self.score
        if s is None:
            return None
        if s >= 95: return "A+"
        if s >= 90: return "A"
        if s >= 85: return "B+"
        if s >= 80: return "B"
        if s >= 75: return "C+"
        if s >= 70: return "C"
        if s >= 60: return "D"
        return "F"
