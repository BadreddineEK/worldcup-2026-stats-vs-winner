"""
pages/finale.py — La Finale CDM 2026 : Spain vs Argentina.
Hero page : champion, stats, bracket, prediction.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.bracket import build_bracket_figure, compute_simulated_winners
from src.clustering import champion_similarity, get_historical_champions
from src.i18n import t
from src.records import finalist_comparison
from src.team_analysis import build_ml_dataset, build_team_profiles, radar_data
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="La Finale", page_icon=":material/emoji_events:", layout="wide")
df_raw, meta = get_data()
lang = st.session_state.get("lang", "fr")
render_sidebar(meta)

df = pd.read_csv("data/matches_2026.csv")
tp = build_team_profiles(df)
cmp = finalist_comparison(df)

ta = cmp["team_a"] if cmp else "Spain"
tb = cmp["team_b"] if cmp else "Argentina"
ch = cmp["champion"] if cmp else None

# ── HERO ──────────────────────────────────────────────────────────────────────
st.title(t("finale_title", lang))
st.markdown(t("finale_intro", lang))
transparency_banner(meta, compact=True)

st.divider()

# Champion badge si connu
if ch:
    st.success(f"🏆 **{t('finale_champion_badge', lang)} : {ch}** 🏆", icon=None)

# ── STATS COMPARAISON HERO ────────────────────────────────────────────────────
ra_row = tp[tp["team"]==ta]
rb_row = tp[tp["team"]==tb]
if not ra_row.empty and not rb_row.empty:
    ra, rb = ra_row.iloc[0], rb_row.iloc[0]

    col_a, col_mid, col_b = st.columns([5, 1, 5])
    with col_a:
        badge_a = " 🏆" if ch == ta else (" ⭐" if not ch else "")
        st.markdown(f"## {ta}{badge_a}")
        st.metric(t("wins", lang), f"{int(ra['wins'])}/{int(ra['matches'])}")
        c1, c2, c3 = st.columns(3)
        c1.metric(t("poss_label", lang), f"{ra['avg_possession']:.0f}%",
                  f"{ra['avg_possession']-rb['avg_possession']:+.0f}pp vs {tb[:3]}.")
        c2.metric(t("goals_pm", lang), f"{ra['goals_per_match']:.1f}",
                  f"{ra['goals_per_match']-rb['goals_per_match']:+.1f}")
        c3.metric(t("conc_pm", lang), f"{ra['conceded_per_match']:.1f}",
                  f"{ra['conceded_per_match']-rb['conceded_per_match']:+.1f}", delta_color="inverse")
    with col_mid:
        st.markdown("### VS")
    with col_b:
        badge_b = " 🏆" if ch == tb else (" ⭐" if not ch else "")
        st.markdown(f"## {tb}{badge_b}")
        st.metric(t("wins", lang), f"{int(rb['wins'])}/{int(rb['matches'])}")
        c1, c2, c3 = st.columns(3)
        c1.metric(t("poss_label", lang), f"{rb['avg_possession']:.0f}%",
                  f"{rb['avg_possession']-ra['avg_possession']:+.0f}pp vs {ta[:3]}.")
        c2.metric(t("goals_pm", lang), f"{rb['goals_per_match']:.1f}",
                  f"{rb['goals_per_match']-ra['goals_per_match']:+.1f}")
        c3.metric(t("conc_pm", lang), f"{rb['conceded_per_match']:.1f}",
                  f"{rb['conceded_per_match']-ra['conceded_per_match']:+.1f}", delta_color="inverse")

    st.divider()

    # ── PREDICTION DU MODELE ──────────────────────────────────────────────────
    st.subheader(t("finale_model_pred", lang))
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    @st.cache_data(ttl=3600, show_spinner=False)
    def get_lr(n):
        ml = build_ml_dataset(pd.read_csv("data/matches_2026.csv"))
        F = ["poss_diff","shots_diff","sot_diff","passes_diff","corners_diff"]
        X, y = ml[F].values, ml["won"].values
        sc2 = StandardScaler().fit(X)
        lr2 = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        lr2.fit(sc2.transform(X), y)
        return lr2, sc2

    lr, sc = get_lr(meta["n_matches"])
    diffs = np.array([[ra["avg_possession"]-rb["avg_possession"],
                       ra["avg_shots"]-rb["avg_shots"],
                       ra["avg_shots_on_target"]-rb["avg_shots_on_target"],
                       ra["avg_passes"]-rb["avg_passes"],
                       ra["avg_corners"]-rb["avg_corners"]]])
    pa_raw = float(lr.predict_proba(sc.transform(diffs))[0][1])
    pb_raw = float(lr.predict_proba(sc.transform(-diffs))[0][1])
    total = pa_raw + pb_raw; pa = pa_raw / total; pb = 1 - pa

    c1, cv, c2 = st.columns([2, 1, 2])
    with c1:
        color_a = GREEN if pa > 0.5 else "#64748b"
        st.metric(ta, f"{pa*100:.1f}%")
        st.progress(pa)
    with cv:
        margin = abs(pa - 0.5) * 100
        if margin < 5:
            st.markdown("### ≈")
        elif pa > 0.5:
            st.markdown(f"### →")
        else:
            st.markdown(f"### ←")
    with c2:
        color_b = GREEN if pb > 0.5 else "#64748b"
        st.metric(tb, f"{pb*100:.1f}%")
        st.progress(pb)

    fav = ta if pa > pb else tb
    if abs(pa - 0.5) < 0.05:
        insight_card("Match ultra-serré selon les données — moins de 5pt d'écart." if lang == "fr"
                     else "Data-wise, this is too close to call — less than 5pp gap.", "#f59e0b")
    else:
        insight_card(
            (f"Le modèle avantage <b>{fav}</b> ({max(pa,pb)*100:.0f}%) "
             f"sur la base de ses statistiques du tournoi. "
             f"Spain : défense légendaire (0.1 but/m). Argentina : attaque de feu ({rb['goals_per_match']:.1f} buts/m)."
             if lang == "fr"
             else f"Model favours <b>{fav}</b> ({max(pa,pb)*100:.0f}%) "
                  f"based on tournament stats. "
                  f"Spain: legendary defence (0.1 goals/m). Argentina: lethal attack ({rb['goals_per_match']:.1f} goals/m)."),
            GREEN if max(pa, pb) > 0.6 else "#f59e0b",
        )

    # Radar
    st.subheader("Comparaison radar" if lang == "fr" else "Radar comparison")
    la, va = radar_data(ra, tp); lb, vb = radar_data(rb, tp)
    fig_r = go.Figure()
    for name, vals, color in [(ta, va, "#00B140"), (tb, vb, "#f59e0b")]:
        vc = vals + [vals[0]]; lc = la + [la[0]]
        fig_r.add_trace(go.Scatterpolar(r=vc, theta=lc, fill="toself", name=name,
                                        line_color=color, fillcolor=color, opacity=0.25))
    fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        template="simple_white", height=360, margin=dict(t=30, b=10))
    st.plotly_chart(fig_r, width="stretch")

    st.divider()

    # ── CONTEXTE HISTORIQUE ───────────────────────────────────────────────────
    st.subheader(t("finale_historic", lang))
    hist = get_historical_champions()
    c1, c2 = st.columns(2)
    for col, team, row in [(c1, ta, ra), (c2, tb, rb)]:
        sims = champion_similarity(row, hist)
        with col:
            st.markdown(f"**{team}** {t('finale_similar_to', lang)} :")
            if not sims.empty:
                b = sims.iloc[0]
                st.metric(f"{b['champion']} {int(b['year'])}", f"{b['similarity']:.0f}%")
                st.caption(b["note"])

st.divider()

# ── BRACKET ───────────────────────────────────────────────────────────────────
st.subheader(t("finale_bracket", lang))
tab_live, tab_sim = st.tabs([
    "Parcours réel" if lang == "fr" else "Real bracket",
    "Et si les stats décidaient ?" if lang == "fr" else "What if stats decided?",
])
with tab_live:
    st.caption(("Vainqueurs réels — vert. TBD = à venir. Sur mobile : pincez pour zoomer."
                if lang == "fr"
                else "Real winners in green. TBD = upcoming. Mobile: pinch to zoom."))
    fig_bracket = build_bracket_figure(df, year=2026)
    st.plotly_chart(fig_bracket, width="stretch")
with tab_sim:
    st.markdown("**Et si les stats dominantes avaient toujours décidé ?**" if lang == "fr"
                else "**What if stats always decided the winner?**")
    sim = compute_simulated_winners(df)
    fig_sim = build_bracket_figure(df, year=2026, simulated_winners=sim)
    st.plotly_chart(fig_sim, width="stretch")

st.caption(t("finale_disclaimer", lang).format(meta["n_matches"]))
