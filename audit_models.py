"""
GTFS audit data models.
Defines CheckResult, CategoryScore and FileScore structures.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CheckResult:
    """Single check result returned by each audit function."""
    check_id        : str                    # Identifiant unique, ex: "agency.format.timezone"
    label           : str                    # Description lisible, ex: "Validité du fuseau horaire"
    category        : str                    # "mandatory" | "format" | "consistency" | "stats" | "accessibility" | "temporal" | "stops_hierarchy"
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
        """Returns the anomaly rate as a percentage, or None if total_count is 0."""
        if self.total_count > 0:
            return round((self.affected_count / self.total_count) * 100, 2)
        return None

    @property
    def score(self) -> Optional[float]:
        """
        Returns a score from 0 to 100, or None if status is 'skip'.
        Uses success rate if total_count > 0, otherwise applies a fixed penalty by status
        (pass=100, warning=60, error=0).
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
    """Aggregated score for a check category within a file, built from a list of CheckResult."""
    category : str
    checks   : list[CheckResult] = field(default_factory=list)

    @property
    def score(self) -> Optional[float]:
        """Returns the weighted average score of eligible checks (skipped checks excluded), or None."""
        eligible = [c for c in self.checks if c.score is not None and c.weight > 0]
        if not eligible:
            return None
        weighted_sum = sum(c.score * c.weight for c in eligible)
        total_weight = sum(c.weight for c in eligible)
        return round(weighted_sum / total_weight, 1)

    @property
    def total_weight(self) -> float:
        """Returns the sum of weights of eligible checks. Used for FileScore computation."""
        return sum(c.weight for c in self.checks if c.score is not None and c.weight > 0)


@dataclass
class FileScore:
    """Overall score for a GTFS file, built from a list of CategoryScore."""
    file       : str
    categories : list[CategoryScore] = field(default_factory=list)

    @property
    def score(self) -> Optional[float]:
        """Returns the weighted average score across all categories, or None if none are eligible."""
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
        """Returns a letter grade (A+ to F) derived from the file score, or None if unavailable."""
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
