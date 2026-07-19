"""
pages/home.py — Tableau de bord CDM 2026 Data Lab.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import agreement_summary
from src.team_analysis import build_team_profiles
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(
    page_title="CDM 2026 — Data Lab",
    page_icon="⚽",
    layout="wide",
)

df, meta = get_data()
render_sidebar(meta)

# ── EN-TÊTE ──────────────────────────────────────────────────────────────────
st.title("⚽ CDM 2026 — Le Bilan en données")

summary = agreement_summary(df)
pct = summary["pct_dominant_won"]

col_hook, col_kpi = st.columns([3, 2])
with col_hook:
    st.markdown("### Ce que 104 matchs de données réelles révèlent")
    st.markdown(
        "La Coupe du Monde 2026 est terminée. "
        "**104 matchs · 48 équipes · 5 stats par match.** "
        "Voici ce que les données ont vraiment dit — et là où le football "
        "a défié les chiffres."
    )
    if pct is not None:
        color = GREEN if pct >= 60 else "#f39c12" if pct >= 50 else RED
        insight_card(
            f"<b>Bilan final :</b> l'équipe dominante a gagné <b>{pct}%</b> du temps "
            f"sur {summary['n_evaluables']} matchs analysables. "
            f"<b>{summary['n_surprises']} matchs</b> ont défié les chiffres — le football reste imprévisible.",
            color,
        )

with col_kpi:
    tp = build_team_profiles(df)
    c1, c2 = st.columns(2)
    c1.metric("Matchs analysés", meta["n_matches"])
    c2.metric("Dominant gagne", f"{pct} %" if pct else "—")
    c3, c4 = st.columns(2)
    c3.metric("Surprises", summary["n_surprises"])
    c4.metric("Modèle IA", "~79%", help="Accuracy cross-validation 5-fold.")

transparency_banner(meta, compact=True)

st.divider()

# ── LES 4 ANGLES ─────────────────────────────────────────────────────────────
st.subheader("Les 4 angles du projet")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("#### 📊 Stats vs Résultats")
    st.markdown(
        "La stat qui prédit le mieux la victoire n'est **pas** la possession. "
        "C'est la précision des tirs. Le modèle l'a confirmé."
    )
with c2:
    st.markdown("#### 🎲 Surprises")
    st.markdown(
        f"**{summary['n_surprises']} matchs** où les chiffres ont menti. "
        "Le football dans toute sa beauté imprévisible."
    )
with c3:
    st.markdown("#### 🧬 ADN des équipes")
    st.markdown(
        "Norway : 80% de victoires avec 53% de possession. "
        "Chaque équipe a une empreinte unique."
    )
with c4:
    st.markdown("#### 🤖 Modèle IA")
    st.markdown(
        "79% d'accuracy. Et un résultat contre-intuitif : "
        "plus de tirs bruts = *moins* de chances de gagner."
    )

st.divider()

# ── AVANCEMENT DU TOURNOI ─────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📍 Bilan du tournoi")
    if not df.empty and "round" in df.columns:
        _order = {
            "Group": 0, "Round of 32": 1, "Round of 16": 2,
            "Quarter": 3, "Semi": 4, "Final": 5,
        }
        rc = df.groupby("round").size().reset_index(name="n")
        rc["_s"] = rc["round"].apply(
            lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
        )
        rc = rc.sort_values("_s").drop(columns="_s")
        colors = [
            "#00B140" if "Group" in r
            else "#3498db" if ("32" in r or "16" in r)
            else "#f39c12"
            for r in rc["round"]
        ]
        fig = go.Figure(go.Bar(
            x=rc["round"], y=rc["n"],
            text=rc["n"], textposition="outside",
            marker_color=colors,
        ))
        fig.update_layout(
            template="plotly_dark", height=260,
            margin=dict(t=10, b=0, l=0, r=0),
            yaxis_title="Matchs", xaxis_title=None, showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("🏁 Résultats clés")
    if not df.empty:
        for _, r in df.tail(5).iloc[::-1].iterrows():
            date = str(r["date"])[:10]
            score = f"{int(r['home_goals'])}–{int(r['away_goals'])}"
            st.markdown(f"**{r['home_team']}** {score} **{r['away_team']}** `{date}`")

st.divider()

# ── TOP ÉQUIPES ───────────────────────────────────────────────────────────────
st.subheader("🏆 Les 6 équipes les plus efficaces du tournoi")
st.caption(
    "Efficiency score = victoires / possession — qui a fait le plus avec le moins ? "
    "Le classement de tout le tournoi, données réelles."
)

top = tp[tp["matches"] >= 3].nlargest(6, "efficiency_score")
# 2 rangees de 3 (bien sur mobile, bien sur desktop)
top_list = list(top.iterrows())
for row_start in range(0, 6, 3):
    row_teams = top_list[row_start:row_start + 3]
    cols_row = st.columns(len(row_teams))
    for j, (_, r) in enumerate(row_teams):
        conv = r["avg_conversion_rate"]
        conv_str = f"{conv:.0f}% conv" if pd.notna(conv) else "conv. n/d"
        with cols_row[j]:
            rank = row_start + j + 1
            st.metric(
                r["team"],
                f"{int(r['wins'])}/{int(r['matches'])} V",
                delta=f"#{rank} · {r['avg_possession']:.0f}% · {conv_str}",
                delta_color="off",
            )

st.caption(
    f"Données au {meta['last_updated_str']} · "
    "Source : [The Stats Zone](https://www.thestatszone.com/fwc26/) · "
    "[Code source](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)"
)
