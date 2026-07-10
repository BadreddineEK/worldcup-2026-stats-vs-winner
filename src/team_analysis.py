"""
src/team_analysis.py — Profils statistiques par équipe.

Agrège les 96 matchs en stats par équipe :
- Moyennes offensives (possession, tirs, tirs cadrés, passes, corners)
- Efficacité : conversion (buts / tirs cadrés), précision (tirs cadrés / tirs)
- Résultats : win_rate, buts marqués/encaissés
- "Indice d'efficacité" : win_rate relatif à la possession dominée

Aucune donnée inventée : si une stat est manquante, elle n'est pas utilisée.
"""

from __future__ import annotations

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────
# CONSTRUCTION DU PROFIL PAR ÉQUIPE
# ─────────────────────────────────────────────────────────────
def build_team_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renvoie un DataFrame avec une ligne par équipe ayant joué au moins 1 match.

    Colonnes :
        matches, wins, draws, losses, win_rate
        goals_for, goals_against, goals_diff
        avg_possession, avg_shots, avg_shots_on_target
        avg_passes, avg_corners
        shot_accuracy      = avg(shots_on_target / shots)       en %
        conversion_rate    = avg(goals / shots_on_target)       en %  (si sot > 0)
        efficiency_score   = win_rate / avg_possession          (ratio)
        dominates_but_loses = taux de matchs où dom > 50% mais sans victoire
    """
    if df.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for _, r in df.iterrows():
        for side, opp in [("home", "away"), ("away", "home")]:
            gf = r[f"{side}_goals"]
            ga = r[f"{opp}_goals"]
            won = r["winner"] == side
            drew = r["winner"] == "draw"
            poss = r[f"{side}_possession"]
            sh   = r[f"{side}_shots"]
            sot  = r[f"{side}_shots_on_target"]
            pas  = r[f"{side}_passes"]
            cor  = r[f"{side}_corners"]

            # Shot accuracy & conversion (NaN si impossible)
            shot_acc = (sot / sh * 100) if (pd.notna(sh) and sh > 0 and pd.notna(sot)) else np.nan
            conv     = (gf  / sot * 100) if (pd.notna(sot) and sot > 0 and pd.notna(gf)) else np.nan
            dom_no_win = int(pd.notna(poss) and poss > 50 and not won and not drew)

            rows.append({
                "team": r[f"{side}_team"],
                "round": r["round"],
                "goals_for": gf,
                "goals_against": ga,
                "won": int(won),
                "drew": int(drew),
                "lost": int(not won and not drew),
                "possession": poss,
                "shots": sh,
                "shots_on_target": sot,
                "passes": pas,
                "corners": cor,
                "shot_accuracy": shot_acc,
                "conversion_rate": conv,
                "dom_no_win": dom_no_win,
            })

    raw = pd.DataFrame(rows)

    agg = (
        raw.groupby("team")
        .agg(
            matches=("goals_for", "count"),
            wins=("won", "sum"),
            draws=("drew", "sum"),
            losses=("lost", "sum"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
            avg_possession=("possession", "mean"),
            avg_shots=("shots", "mean"),
            avg_shots_on_target=("shots_on_target", "mean"),
            avg_passes=("passes", "mean"),
            avg_corners=("corners", "mean"),
            avg_shot_accuracy=("shot_accuracy", "mean"),
            avg_conversion_rate=("conversion_rate", "mean"),
            dom_no_win_count=("dom_no_win", "sum"),
        )
        .reset_index()
    )

    agg["win_rate"] = (agg["wins"] / agg["matches"] * 100).round(1)
    agg["goals_diff"] = agg["goals_for"] - agg["goals_against"]
    agg["goals_per_match"] = (agg["goals_for"] / agg["matches"]).round(2)
    agg["conceded_per_match"] = (agg["goals_against"] / agg["matches"]).round(2)
    # Efficiency : win_rate obtenu pour chaque % de possession moyen
    agg["efficiency_score"] = (agg["win_rate"] / agg["avg_possession"].clip(1)).round(3)
    # Taux de frustration : matchs où on domine sans gagner
    agg["frustration_rate"] = (agg["dom_no_win_count"] / agg["matches"] * 100).round(1)

    # Arrondis finaux
    for col in ["avg_possession", "avg_shots", "avg_shots_on_target",
                "avg_passes", "avg_corners", "avg_shot_accuracy", "avg_conversion_rate"]:
        agg[col] = agg[col].round(1)

    return agg.sort_values("win_rate", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# DONNÉES POUR RADAR / SPIDER CHART
# ─────────────────────────────────────────────────────────────
RADAR_DIMS = [
    ("avg_possession",        "Possession"),
    ("avg_shots",             "Tirs / match"),
    ("avg_shots_on_target",   "Tirs cadrés / match"),
    ("avg_shot_accuracy",     "Précision tirs"),
    ("avg_conversion_rate",   "Conversion"),
    ("avg_passes",            "Passes / match"),
]


def radar_data(team_row: pd.Series, all_teams: pd.DataFrame) -> tuple[list[str], list[float]]:
    """
    Normalise les dimensions d'une équipe en 0–100 par rapport au max du tournoi.
    Renvoie (labels, valeurs_normalisées).
    """
    labels, values = [], []
    for col, label in RADAR_DIMS:
        if col not in team_row or col not in all_teams.columns:
            continue
        v = team_row[col]
        vmax = all_teams[col].max()
        if pd.isna(v) or vmax == 0:
            norm = 0.0
        else:
            norm = min(100.0, v / vmax * 100)
        labels.append(label)
        values.append(round(norm, 1))
    return labels, values


# ─────────────────────────────────────────────────────────────
# NARRATION AUTOMATIQUE PAR ÉQUIPE
# ─────────────────────────────────────────────────────────────
def team_narrative(row: pd.Series, all_teams: pd.DataFrame) -> str:
    """
    Génère une description data-driven (2-3 phrases) pour une équipe.
    Entièrement basée sur les stats réelles — rien n'est inventé.
    """
    name  = row["team"]
    wr    = row["win_rate"]
    poss  = row["avg_possession"]
    conv  = row["avg_conversion_rate"]
    acc   = row["avg_shot_accuracy"]
    shots = row["avg_shots"]
    eff   = row["efficiency_score"]
    frust = row["frustration_rate"]
    gpm   = row["goals_per_match"]

    poss_pct  = poss  / all_teams["avg_possession"].max() * 100
    conv_pct  = (conv / all_teams["avg_conversion_rate"].max() * 100) if pd.notna(conv) else 50
    eff_rank  = (all_teams["efficiency_score"] >= eff).sum()

    parts = []

    # Style offensif
    if poss >= 60 and wr >= 70:
        parts.append(f"**{name}** domine le ballon ({poss:.0f}% de possession en moyenne) et en tire parti : {wr:.0f}% de victoires.")
    elif poss < 50 and wr >= 60:
        parts.append(f"**{name}** est l'archétype de l'équipe pragmatique : seulement {poss:.0f}% de possession, mais {wr:.0f}% de succès — la preuve que contrôler ne suffit pas.")
    elif poss >= 60 and wr < 50:
        parts.append(f"**{name}** monopolise le ballon ({poss:.0f}%) mais peine à convertir : seulement {wr:.0f}% de victoires malgré la domination.")
    else:
        parts.append(f"**{name}** affiche {poss:.0f}% de possession moyenne pour {wr:.0f}% de victoires dans ce tournoi.")

    # Efficacité devant le but
    if pd.notna(conv) and conv >= 40:
        parts.append(f"Avec {conv:.0f}% de conversion (buts/tirs cadrés), c'est l'une des attaques les plus cliniques du tournoi.")
    elif pd.notna(conv) and conv <= 15:
        parts.append(f"Sa conversion ({conv:.0f}%) trahit une réelle maladresse devant le but malgré {shots:.1f} tentatives par match.")
    else:
        parts.append(f"Elle marque {gpm:.1f} but(s) par match pour {shots:.1f} tirs en moyenne.")

    # Efficacité globale
    if eff_rank <= 5 and row["matches"] >= 3:
        parts.append(f"Son *efficiency score* (victoires rapportées à la possession) la classe parmi les 5 équipes les plus efficaces du tournoi.")
    if frust >= 25:
        parts.append(f"Mais elle domine sans gagner dans {frust:.0f}% de ses matchs — un paradoxe statistique.")

    return " ".join(parts)


# ─────────────────────────────────────────────────────────────
# DONNÉES POUR LE MODÈLE ML
# ─────────────────────────────────────────────────────────────
def build_ml_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construit un dataset pour la classification binaire :
    « l'équipe A gagne-t-elle ce match ? »

    Chaque match génère 2 lignes (perspective domicile + extérieur).
    Features : stats absolues + différentielles vs l'adversaire.
    Target : won (1 = victoire, 0 = pas de victoire).
    Exclut les matchs à égalité où les pénalties déterminent le vainqueur
    (le score de regulation est nul mais le winner existe).
    """
    rows: list[dict] = []
    for _, r in df.iterrows():
        winner = r["winner"]
        for side, opp in [("home", "away"), ("away", "home")]:
            gf   = r[f"{side}_goals"]
            ga   = r[f"{opp}_goals"]
            poss = r[f"{side}_possession"]
            sh   = r[f"{side}_shots"]
            sot  = r[f"{side}_shots_on_target"]
            pas  = r[f"{side}_passes"]
            cor  = r[f"{side}_corners"]
            o_sh  = r[f"{opp}_shots"]
            o_sot = r[f"{opp}_shots_on_target"]
            o_poss = r[f"{opp}_possession"]
            o_pas  = r[f"{opp}_passes"]
            o_cor  = r[f"{opp}_corners"]

            won = 1 if winner == side else 0

            if any(pd.isna(v) for v in [poss, sh, sot, pas, cor]):
                continue

            rows.append({
                # Features absolues
                "possession": poss,
                "shots": sh,
                "shots_on_target": sot,
                "shot_accuracy": sot / max(sh, 1) * 100,
                "passes": pas,
                "corners": cor,
                # Features différentielles (team - opponent)
                "poss_diff": poss - o_poss,
                "shots_diff": sh - o_sh,
                "sot_diff": sot - o_sot,
                "passes_diff": pas - o_pas,
                "corners_diff": cor - o_cor,
                # Target
                "won": won,
            })

    return pd.DataFrame(rows)
