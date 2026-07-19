"""
src/records.py — Records et highlights du tournoi CDM 2026.

Calcule les stats marquantes sur l'ensemble des matchs :
meilleure défense, attaque la plus prolifique, plus grand upset, etc.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def tournament_records(df: pd.DataFrame) -> list[dict]:
    """
    Retourne une liste de records du tournoi, chacun sous la forme :
        {'icon', 'label', 'value', 'detail', 'color'}
    """
    df = df.copy()
    df["total_goals"] = df["home_goals"] + df["away_goals"]
    df["goal_diff"]   = (df["home_goals"] - df["away_goals"]).abs()

    from src.team_analysis import build_team_profiles
    from src.analysis import annotate_matches

    tp = build_team_profiles(df)
    annotated = annotate_matches(df)

    records: list[dict] = []

    # 1. Plus grande victoire
    bw = df.loc[df["goal_diff"].idxmax()]
    w  = bw["home_team"] if bw["winner"] == "home" else bw["away_team"]
    l  = bw["away_team"] if bw["winner"] == "home" else bw["home_team"]
    records.append({
        "icon": "⚡",
        "label": "Plus grande victoire",
        "value": f"{int(bw['home_goals'])}–{int(bw['away_goals'])}",
        "detail": f"{bw['home_team']} vs {bw['away_team']}",
        "color": "#f39c12",
    })

    # 2. Match le plus prolifique
    hi = df.loc[df["total_goals"].idxmax()]
    records.append({
        "icon": "🎯",
        "label": "Match le plus prolifique",
        "value": f"{int(hi['total_goals'])} buts",
        "detail": f"{hi['home_team']} {int(hi['home_goals'])}–{int(hi['away_goals'])} {hi['away_team']}",
        "color": "#3498db",
    })

    # 3. Meilleure défense (min 4 matchs)
    best_def = tp[tp["matches"] >= 4].nsmallest(1, "conceded_per_match")
    if not best_def.empty:
        bd = best_def.iloc[0]
        records.append({
            "icon": "🧱",
            "label": "Défense la plus hermétique",
            "value": f"{bd['conceded_per_match']:.1f} but/m",
            "detail": f"{bd['team']} — {bd['matches']} matchs",
            "color": "#00B140",
        })

    # 4. Meilleure conversion (min 3 matchs)
    top_conv = tp[tp["matches"] >= 3].nlargest(1, "avg_conversion_rate")
    if not top_conv.empty:
        tc = top_conv.iloc[0]
        records.append({
            "icon": "🎯",
            "label": "Conversion la plus clinique",
            "value": f"{tc['avg_conversion_rate']:.0f}%",
            "detail": f"{tc['team']} — buts / tirs cadrés",
            "color": "#9b59b6",
        })

    # 5. Plus grande attaque (buts totaux)
    most_goals = tp.nlargest(1, "goals_for").iloc[0]
    records.append({
        "icon": "🔥",
        "label": "Attaque la plus prolifique",
        "value": f"{int(most_goals['goals_for'])} buts",
        "detail": f"{most_goals['team']} — {most_goals['matches']} matchs",
        "color": "#e74c3c",
    })

    # 6. Plus grand upset (dominant qui a perdu — plus gros écart de possession)
    surp = annotated[annotated["is_surprise"] == True].copy()
    if not surp.empty:
        surp["poss_diff"] = (surp["home_possession"] - surp["away_possession"]).abs()
        bu = surp.loc[surp["poss_diff"].idxmax()]
        dom = bu["home_team"] if bu["dominant_side"] == "home" else bu["away_team"]
        win = bu["home_team"] if bu["winner"] == "home" else bu["away_team"]
        poss_d = bu["poss_diff"]
        records.append({
            "icon": "💥",
            "label": "Plus grand upset",
            "value": f"+{poss_d:.0f}% possession",
            "detail": f"{dom} dominait mais {win} a gagné",
            "color": "#f39c12",
        })

    return records


def finalist_comparison(df: pd.DataFrame) -> dict | None:
    """
    Renvoie un dict comparant les deux finalistes sur leurs stats du tournoi.
    Auto-détecte les finalistes depuis la SF.
    """
    from src.team_analysis import build_team_profiles

    tp = build_team_profiles(df)
    sf = df[df["round"] == "Semi-finals"]
    final = df[df["round"] == "Final"]

    if not final.empty:
        f = final.iloc[0]
        team_a, team_b = f["home_team"], f["away_team"]
        champion = f["home_team"] if f["winner"] == "home" else f["away_team"]
    elif len(sf) >= 2:
        # Extraire les 2 vainqueurs des SF
        finalists = []
        for _, m in sf.iterrows():
            w = m["winner"]
            finalists.append(m["home_team"] if w == "home" else m["away_team"])
        if len(finalists) < 2:
            return None
        team_a, team_b = finalists[0], finalists[1]
        champion = None
    else:
        return None

    ra = tp[tp["team"] == team_a]
    rb = tp[tp["team"] == team_b]
    if ra.empty or rb.empty:
        return None

    ra, rb = ra.iloc[0], rb.iloc[0]

    METRICS = [
        ("avg_possession",        "Possession moy.",     "%"),
        ("avg_shots",             "Tirs / match",        ""),
        ("avg_shots_on_target",   "Tirs cadrés / match", ""),
        ("avg_conversion_rate",   "Conversion",          "%"),
        ("goals_per_match",       "Buts / match",        ""),
        ("conceded_per_match",    "Buts concédés / m",   ""),
        ("efficiency_score",      "Efficiency score",    ""),
    ]

    comparison = []
    for col, label, unit in METRICS:
        va = ra.get(col, np.nan)
        vb = rb.get(col, np.nan)
        if pd.isna(va) or pd.isna(vb):
            continue
        # Pour conceded_per_match : moins c'est mieux (winner = celui qui a le moins)
        if "conceded" in col:
            advantage = team_a if va < vb else team_b if vb < va else None
        else:
            advantage = team_a if va > vb else team_b if vb > va else None
        comparison.append({
            "label": label,
            "unit": unit,
            "val_a": round(float(va), 1),
            "val_b": round(float(vb), 1),
            "advantage": advantage,
        })

    return {
        "team_a": team_a,
        "team_b": team_b,
        "champion": champion,
        "comparison": comparison,
        "wins_a": int(ra["wins"]),
        "wins_b": int(rb["wins"]),
        "matches_a": int(ra["matches"]),
        "matches_b": int(rb["matches"]),
    }
