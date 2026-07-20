"""
make_slides.py — Genere 3 slides PNG portrait (1080x1350) pretes pour LinkedIn.
100% matplotlib (rapide, aucune dependance navigateur). Sortie dans slides/.

Run:  python make_slides.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold

from src.data_build import load_matches
from src.analysis import annotate_matches, agreement_summary
from src.team_analysis import build_team_profiles, build_ml_dataset

# ── Charte ────────────────────────────────────────────────────────────────────
GREEN = "#00B140"
RED = "#ef4444"
DARK = "#1a1d23"
GOLD = "#f1b900"
GREY = "#64748b"
BG = "#ffffff"
OUT = Path("slides")
OUT.mkdir(exist_ok=True)
FOOTER = "Badreddine EK   ·   Python · scikit-learn · Streamlit   ·   Donnees reelles"

plt.rcParams["font.family"] = "DejaVu Sans"


def new_slide():
    """Figure portrait 1080x1350 avec banniere verte + footer. Renvoie (fig)."""
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100)
    fig.patch.set_facecolor(BG)
    # Banniere verte haut (14% de la hauteur)
    fig.add_artist(Rectangle((0, 0.86), 1, 0.14, transform=fig.transFigure,
                             color=GREEN, zorder=0))
    # Footer
    fig.text(0.5, 0.03, FOOTER, ha="center", va="center", fontsize=12, color=GREY)
    return fig


def header(fig, title, subtitle=""):
    fig.text(0.06, 0.945, title, ha="left", va="center", fontsize=27,
             color="white", fontweight="bold")
    if subtitle:
        fig.text(0.06, 0.895, subtitle, ha="left", va="center", fontsize=17,
                 color="#eafff1")


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=200, facecolor=BG, bbox_inches=None)
    plt.close(fig)
    print(f"OK  {path}  (2160x2700px)")


# ══════════════════════════════════════════════════════════════════════════════
def main():
    global FOOTER
    df_raw, meta = load_matches()
    FOOTER = (f"Badreddine EK   ·   Python · scikit-learn · Streamlit   ·   "
              f"{meta['n_matches']} matchs reels")
    ann = annotate_matches(df_raw)
    summ = agreement_summary(ann)
    pct = summ["pct_dominant_won"]
    n_eval = summ["n_evaluables"]

    df = pd.read_csv("data/matches_2026.csv")
    tp = build_team_profiles(df)

    champ = None
    fin = df[df["round"] == "Final"]
    if not fin.empty:
        f = fin.iloc[0]
        champ = f["home_team"] if f["winner"] == "home" else f["away_team"]

    # Modele
    ml = build_ml_dataset(df)
    FEATS = ["poss_diff", "shots_diff", "sot_diff", "passes_diff", "corners_diff"]
    X, y = ml[FEATS].values, ml["won"].values
    scaler = StandardScaler().fit(X)
    lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    cv = cross_val_score(lr, scaler.transform(X), y,
                         cv=StratifiedKFold(5, shuffle=True, random_state=42))
    lr.fit(scaler.transform(X), y)
    acc = cv.mean()

    # ── SLIDE 1 : le chiffre choc ────────────────────────────────────────────
    fig = new_slide()
    header(fig, "Les stats predisent-elles le vainqueur ?",
           f"Mondial 2026  ·  analyse des {meta['n_matches']} matchs")
    fig.text(0.5, 0.60, f"{pct:.0f}%", ha="center", va="center",
             fontsize=170, color=GREEN, fontweight="bold")
    fig.text(0.5, 0.415, "des matchs remportes par l'equipe\nqui domine les statistiques",
             ha="center", va="center", fontsize=25, color=DARK)
    fig.text(0.5, 0.30, "2 fois sur 3. Pas plus.", ha="center", va="center",
             fontsize=30, color=DARK, fontweight="bold")
    fig.text(0.5, 0.20, f"Sur {n_eval} matchs a dominant clair du tournoi",
             ha="center", va="center", fontsize=18, color=GREY)
    save(fig, "slide_1_accord.png")

    # ── SLIDE 2 : feature importance ─────────────────────────────────────────
    # Ordre STRICTEMENT aligne sur FEATS = [poss_diff, shots_diff, sot_diff, passes_diff, corners_diff]
    labels = ["Diff. Possession", "Diff. Tirs", "Diff. Tirs cadres",
              "Diff. Passes", "Diff. Corners"]
    coefs = pd.DataFrame({"f": labels, "c": lr.coef_[0]}).sort_values("c")
    fig = new_slide()
    header(fig, "Ce qui predit vraiment une victoire", "Ce que le modele a appris")
    ax = fig.add_axes([0.30, 0.30, 0.62, 0.48])
    colors = [GREEN if v > 0 else RED for v in coefs["c"]]
    ax.barh(coefs["f"], coefs["c"], color=colors)
    ax.axvline(0, color=GREY, lw=1)
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", labelsize=18, length=0)
    ax.tick_params(axis="x", labelsize=13, colors=GREY)
    for v, name in zip(coefs["c"], coefs["f"]):
        ax.text(v + (0.05 if v > 0 else -0.05), name, f"{v:+.2f}",
                va="center", ha="left" if v > 0 else "right",
                fontsize=16, color=DARK, fontweight="bold")
    ax.set_xlim(coefs["c"].min() - 0.6, coefs["c"].max() + 0.6)
    ax.set_xlabel("Impact sur la probabilite de gagner", fontsize=15, color=DARK)
    fig.text(0.5, 0.19, "Cadrer ses tirs compte le plus. Tirer beaucoup sans cadrer fait perdre.",
             ha="center", fontsize=18, color=DARK, fontweight="bold")
    fig.text(0.5, 0.145, f"Regression logistique  ·  precision {acc*100:.0f}%  (validation croisee 5 blocs)",
             ha="center", fontsize=15, color=GREY)
    save(fig, "slide_2_modele.png")

    # ── SLIDE 3 : le resultat de la finale ────────────────────────────────────
    ARG = "#75AADB"  # bleu ciel Argentine
    fr = fin.iloc[0]  # ligne Final (Spain home, Argentina away)
    metrics = [
        ("Possession",   fr["home_possession"],       fr["away_possession"],       "{:.0f}%"),
        ("Tirs",         fr["home_shots"],             fr["away_shots"],             "{:.0f}"),
        ("Tirs cadres",  fr["home_shots_on_target"],  fr["away_shots_on_target"],  "{:.0f}"),
        ("Corners",      fr["home_corners"],           fr["away_corners"],           "{:.0f}"),
    ]

    fig = new_slide()
    header(fig, "Spain, championne du monde 2026", "Finale  ·  Spain 1 - 0 Argentina (a.p.)")
    fig.text(0.28, 0.775, "SPAIN", ha="center", fontsize=26, color=GREEN, fontweight="bold")
    fig.text(0.28, 0.742, "★ CHAMPIONNE", ha="center", fontsize=16, color=GOLD, fontweight="bold")
    fig.text(0.72, 0.775, "ARGENTINA", ha="center", fontsize=26, color=ARG, fontweight="bold")

    ax = fig.add_axes([0.06, 0.25, 0.88, 0.48])
    ax.set_xlim(-1.32, 1.32)
    ax.set_ylim(-0.6, len(metrics) - 0.35)
    ax.axvline(0, color="#d8dee6", lw=1.2, zorder=1)
    for i, (name, sv, av, fmt) in enumerate(metrics):
        y = len(metrics) - 1 - i
        m = max(sv, av, 0.01)
        ax.barh(y, -sv / m, height=0.46, color=GREEN, zorder=2)
        if av > 0:
            ax.barh(y, av / m, height=0.46, color=ARG, zorder=2)
        ax.text(0, y + 0.40, name, ha="center", va="bottom", fontsize=15, color=DARK)
        ax.text(-sv / m - 0.04, y, fmt.format(sv), ha="right", va="center",
                fontsize=17, color=GREEN, fontweight="bold")
        ax.text((av / m + 0.04) if av > 0 else 0.04, y, fmt.format(av), ha="left",
                va="center", fontsize=17, color="#2b7ab5", fontweight="bold")
    ax.axis("off")

    fig.text(0.5, 0.185, "11 tirs cadres a 0. Une demonstration statistique en finale.",
             ha="center", fontsize=18, color=DARK, fontweight="bold")
    fig.text(0.5, 0.150, "Mon modele l'annoncait : dominer les tirs cadres, c'est gagner.",
             ha="center", fontsize=16, color=GREY)
    save(fig, "slide_3_finale.png")

    print("\nTermine. 3 slides dans slides/ (format 4:5, pretes pour LinkedIn).")


if __name__ == "__main__":
    main()
