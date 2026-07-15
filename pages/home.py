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
st.title("⚽ CDM 2026 — Data Lab")

summary = agreement_summary(df)
pct = summary["pct_dominant_won"]

col_hook, col_kpi = st.columns([3, 2])
with col_hook:
    st.markdown("### Les stats prédisent-elles le vainqueur ?")
    st.markdown(
        "Pendant que la Coupe du Monde 2026 se joue "
        "(11 juin → 19 juillet, USA · Mexique · Canada), "
        "ce Data Lab confronte les **chiffres réels** de chaque match "
        "au résultat final."
    )
    if pct is not None:
        color = GREEN if pct >= 60 else "#f39c12" if pct >= 50 else RED
        insight_card(
            f"<b>Réponse à date :</b> l'équipe dominante gagne <b>{pct}%</b> du temps "
            f"sur {summary['n_evaluables']} matchs analysables. "
            f"Mais {summary['n_surprises']} matchs ont défié les chiffres.",
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
        "Quelle stat prédit le mieux ? "
        "Spoiler : ce n'est *pas* la possession — "
        "c'est la **précision** des tirs."
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
    st.subheader("📍 Avancement du tournoi")
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
    st.subheader("🕹️ Derniers résultats")
    if not df.empty:
        for _, r in df.tail(5).iloc[::-1].iterrows():
            date = str(r["date"])[:10]
            score = f"{int(r['home_goals'])}–{int(r['away_goals'])}"
            st.markdown(f"**{r['home_team']}** {score} **{r['away_team']}** `{date}`")

st.divider()

# ── TOP ÉQUIPES ───────────────────────────────────────────────────────────────
st.subheader("🏆 Les 6 équipes les plus efficaces")
st.caption(
    "Efficiency score = taux de victoire / possession moyenne. "
    "Un score élevé = beaucoup de victoires sans forcément dominer le ballon."
)

top = tp[tp["matches"] >= 3].nlargest(6, "efficiency_score")
cols_t = st.columns(6)
for i, (_, r) in enumerate(top.iterrows()):
    conv = r["avg_conversion_rate"]
    conv_str = f"{conv:.0f}% conv" if pd.notna(conv) else "conv. n/d"
    with cols_t[i]:
        st.metric(
            r["team"],
            f"{int(r['wins'])}/{int(r['matches'])} V",
            delta=f"{r['avg_possession']:.0f}% poss · {conv_str}",
            delta_color="off",
        )

st.caption(
    f"Données au {meta['last_updated_str']} · "
    "Source : [The Stats Zone](https://www.thestatszone.com/fwc26/) · "
    "[Code source](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)"
)
