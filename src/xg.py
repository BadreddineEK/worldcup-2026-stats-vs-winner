"""
src/xg.py — Expected Goals (xG) proxy pour la CDM 2026.

Methode : xG = shots_on_target * taux_conversion_tournoi
         + (shots - shots_on_target) * taux_conversion_tournoi * 0.08

Le taux de conversion de base est calcule sur l ensemble du tournoi.
Ce proxy simple est documentable, explicable, et produit des insights
pertinents (overperformance = chance factor, underperformance = malchance).

Aucune valeur n est inventee : si une stat est manquante, le match est ignore.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _tournament_base_rate(df: pd.DataFrame) -> float:
    """Taux de conversion moyen du tournoi : buts / tirs cadres."""
    total_goals = df["home_goals"].sum() + df["away_goals"].sum()
    total_sot = df["home_shots_on_target"].sum() + df["away_shots_on_target"].sum()
    return float(total_goals / total_sot) if total_sot > 0 else 0.30


def compute_match_xg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule le xG par equipe par match.

    Retourne un DataFrame avec colonnes :
        team, fixture_id, date, round,
        goals, xg, overperformance,
        shots_on_target, shots
    """
    base = _tournament_base_rate(df)
    off_coeff = base * 0.08  # tirs hors cadre contribuent ~8x moins

    rows: list[dict] = []
    for _, r in df.iterrows():
        for side, _ in [("home", "away"), ("away", "home")]:
            sot = r.get(f"{side}_shots_on_target")
            sh = r.get(f"{side}_shots")
            g = r.get(f"{side}_goals")
            if any(pd.isna(v) for v in [sot, sh, g]):
                continue
            off = max(0.0, float(sh) - float(sot))
            xg = round(float(sot) * base + off * off_coeff, 2)
            rows.append(
                {
                    "team": r[f"{side}_team"],
                    "fixture_id": r["fixture_id"],
                    "date": str(r["date"])[:10],
                    "round": r["round"],
                    "goals": int(g),
                    "xg": xg,
                    "overperformance": round(float(g) - xg, 2),
                    "shots_on_target": int(sot),
                    "shots": int(sh),
                }
            )

    return pd.DataFrame(rows)


def team_xg_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resume xG par equipe (sur tout le tournoi).

    Colonnes cles :
        matches, goals_total, xg_total,
        overperf_total, overperf_per_match,
        pct_vs_expected   (100 = dans la norme, >100 = chanceux)
    """
    raw = compute_match_xg(df)
    if raw.empty:
        return pd.DataFrame()

    agg = (
        raw.groupby("team")
        .agg(
            matches=("fixture_id", "count"),
            goals_total=("goals", "sum"),
            xg_total=("xg", "sum"),
            overperf_total=("overperformance", "sum"),
        )
        .reset_index()
    )

    agg["goals_per_match"] = (agg["goals_total"] / agg["matches"]).round(2)
    agg["xg_per_match"] = (agg["xg_total"] / agg["matches"]).round(2)
    agg["overperf_per_match"] = (agg["overperf_total"] / agg["matches"]).round(2)
    agg["pct_vs_expected"] = (
        agg["goals_total"] / agg["xg_total"].clip(0.01) * 100
    ).round(1)

    return agg.sort_values("overperf_total", ascending=False).reset_index(drop=True)


def xg_label(overperf: float) -> str:
    """Texte narratif pour l overperformance xG."""
    if overperf > 1.5:
        return "Tres chanceux"
    if overperf > 0.5:
        return "Au-dessus des attentes"
    if overperf > -0.5:
        return "Dans la norme"
    if overperf > -1.5:
        return "Sous ses attentes"
    return "Tres malchanceux"
