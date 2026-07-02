"""
src/analysis.py — La question du projet, en chiffres.

« L'équipe qui domine les statistiques d'un match gagne-t-elle vraiment ? »

On mesure la "domination" match par match sur trois stats clés (possession,
tirs, tirs cadrés), on la confronte au résultat réel, et on isole les
"surprises" (le dominant perd ou ne gagne pas).

Règle d'honnêteté : une comparaison n'est faite QUE si la stat est disponible
pour les deux équipes. Sinon → non comptée (jamais inventée).
"""

from __future__ import annotations

import pandas as pd

# Stats confrontées : (colonne domicile, colonne extérieur, libellé lisible)
STAT_PAIRS = [
    ("home_possession", "away_possession", "Possession"),
    ("home_shots", "away_shots", "Tirs"),
    ("home_shots_on_target", "away_shots_on_target", "Tirs cadrés"),
]


def _leader(home_val, away_val) -> str | None:
    """'home' / 'away' / 'egalite' selon qui mène la stat ; None si indisponible."""
    if pd.isna(home_val) or pd.isna(away_val):
        return None
    if home_val > away_val:
        return "home"
    if away_val > home_val:
        return "away"
    return "egalite"


def annotate_matches(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute, pour chaque stat, qui la domine et si ce dominant a gagné.

    Nouvelles colonnes par stat (ex. possession) :
        possession_leader        : 'home'|'away'|'egalite'|None
        possession_leader_won    : True|False|None  (None = égalité stat, ou non dispo)
    Plus une synthèse globale :
        dominant_side            : équipe qui mène la MAJORITÉ des stats dispo
        dominant_won             : le dominant global a-t-il gagné ?
        is_surprise              : dominant global n'a PAS gagné
    """
    df = df.copy()
    if df.empty:
        for _, _, label in STAT_PAIRS:
            key = _slug(label)
            df[f"{key}_leader"] = pd.Series(dtype="object")
            df[f"{key}_leader_won"] = pd.Series(dtype="object")
        df["dominant_side"] = pd.Series(dtype="object")
        df["dominant_won"] = pd.Series(dtype="object")
        df["is_surprise"] = pd.Series(dtype="object")
        return df

    for home_col, away_col, label in STAT_PAIRS:
        key = _slug(label)
        leaders = df.apply(lambda r: _leader(r[home_col], r[away_col]), axis=1)
        df[f"{key}_leader"] = leaders
        df[f"{key}_leader_won"] = df.apply(
            lambda r: _leader_won(r[f"{key}_leader"], r["winner"]), axis=1
        )

    df["dominant_side"] = df.apply(_overall_dominant, axis=1)
    df["dominant_won"] = df.apply(
        lambda r: _leader_won(r["dominant_side"], r["winner"]), axis=1
    )
    df["is_surprise"] = df["dominant_won"].apply(lambda v: v is False)
    return df


def _slug(label: str) -> str:
    return (
        label.lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace(" ", "_")
    )


def _leader_won(leader, winner) -> bool | None:
    """Le meneur de la stat a-t-il gagné le match ?"""
    if leader is None or leader == "egalite":
        return None
    if pd.isna(winner) or winner == "draw":
        return False  # match nul : le dominant n'a pas "gagné"
    return leader == winner


def _overall_dominant(row) -> str | None:
    """Équipe qui domine la majorité des stats disponibles pour ce match."""
    votes = {"home": 0, "away": 0}
    counted = 0
    for _, _, label in STAT_PAIRS:
        leader = row.get(f"{_slug(label)}_leader")
        if leader in ("home", "away"):
            votes[leader] += 1
            counted += 1
    if counted == 0:
        return None
    if votes["home"] > votes["away"]:
        return "home"
    if votes["away"] > votes["home"]:
        return "away"
    return None  # domination partagée : pas de dominant clair


def agreement_summary(annotated: pd.DataFrame) -> dict:
    """
    Synthèse : sur les matchs où un dominant clair existe, combien ont gagné ?

    Renvoie :
        {
          "n_matches": int,            # matchs joués
          "n_evaluables": int,         # matchs avec un dominant clair
          "n_dominant_won": int,
          "n_surprises": int,
          "pct_dominant_won": float | None,   # 0..100
        }
    """
    evaluable = annotated[annotated["dominant_won"].notna()]
    n_eval = int(len(evaluable))
    n_won = int((evaluable["dominant_won"] == True).sum())  # noqa: E712
    pct = round(100 * n_won / n_eval, 1) if n_eval else None
    return {
        "n_matches": int(len(annotated)),
        "n_evaluables": n_eval,
        "n_dominant_won": n_won,
        "n_surprises": n_eval - n_won,
        "pct_dominant_won": pct,
    }


def find_surprises(annotated: pd.DataFrame) -> pd.DataFrame:
    """Matchs où l'équipe dominant les stats n'a PAS gagné."""
    if annotated.empty:
        return annotated
    return annotated[annotated["is_surprise"] == True].copy()  # noqa: E712


def stat_agreement_by_type(annotated: pd.DataFrame) -> pd.DataFrame:
    """
    Taux d'accord stat par stat : « quand une équipe mène aux TIRS,
    gagne-t-elle ? », etc. Utile pour classer les stats les plus prédictives.
    """
    rows = []
    for _, _, label in STAT_PAIRS:
        key = _slug(label)
        col = f"{key}_leader_won"
        if col not in annotated.columns:
            continue
        series = annotated[col].dropna()
        n = int(len(series))
        won = int((series == True).sum())  # noqa: E712
        rows.append(
            {
                "Statistique": label,
                "Matchs évaluables": n,
                "Le meneur a gagné": won,
                "Taux (%)": round(100 * won / n, 1) if n else None,
            }
        )
    return pd.DataFrame(rows)
