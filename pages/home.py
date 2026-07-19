"""
pages/home.py — Bilan CDM 2026 Data Lab.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.analysis import agreement_summary
from src.records import finalist_comparison, tournament_records
from src.team_analysis import build_team_profiles
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(
    page_title="CDM 2026 — Le Bilan Data",
    page_icon="trophy",
    layout="wide",
)

df, meta = get_data()
render_sidebar(meta)

# ── EN-TÊTE ──────────────────────────────────────────────────────────────────
st.title("CDM 2026 — Le Bilan en données")

summary = agreement_summary(df)
pct = summary["pct_dominant_won"]
tp = build_team_profiles(df)

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
            f"<b>{summary['n_surprises']} matchs</b> ont défié les chiffres.",
            color,
        )

with col_kpi:
    c1, c2 = st.columns(2)
    c1.metric("Matchs analysés", meta["n_matches"])
    c2.metric("Dominant gagne", f"{pct} %" if pct else "—")
    c3, c4 = st.columns(2)
    c3.metric("Surprises", summary["n_surprises"])
    c4.metric("Modèle IA", "~79%", help="Accuracy cross-validation 5-fold.")

transparency_banner(meta, compact=True)

st.divider()

# ── RECORDS DU MONDIAL ───────────────────────────────────────────────────────
st.subheader("Les chiffres qui ont marqué ce Mondial")

records = tournament_records(df)
# Afficher en 2 rangées de 3
# Cartes natives Streamlit (s adaptent au theme light/dark)
rec_cols = [st.columns(3), st.columns(3)]
for i, r in enumerate(records):
    with rec_cols[i // 3][i % 3]:
        with st.container(border=True):
            st.markdown(f"**{r['icon']} {r['label']}**")
            st.markdown(
                f"<span style='font-size:26px;font-weight:700;color:{r['color']}'>"
                f"{r['value']}</span>",
                unsafe_allow_html=True,
            )
            st.caption(r["detail"])


st.divider()

# ── LE CHOC FINAL : SPAIN vs ARGENTINA ──────────────────────────────────────
cmp = finalist_comparison(df)
if cmp:
    ta, tb = cmp["team_a"], cmp["team_b"]
    ch = cmp["champion"]
    title_str = f"Spain vs Argentina" if ch is None else f"Spain vs Argentina — Champion : {ch}"
    st.subheader(f"Le choc final : {title_str}")

    col_fa, col_vs, col_fb = st.columns([5, 1, 5])
    with col_fa:
        ra_row = tp[tp["team"]==ta]
        if not ra_row.empty:
            r = ra_row.iloc[0]
            champion_badge = " 🏆" if ch == ta else ""
            st.markdown(f"### {ta}{champion_badge}")
            st.metric("Victoires en tournoi", f"{cmp['wins_a']}/{cmp['matches_a']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Possession moy.", f"{r['avg_possession']:.0f}%")
            c2.metric("Buts / match", f"{r['goals_per_match']:.1f}")
            c3.metric("Concédés / m", f"{r['conceded_per_match']:.1f}")
    with col_vs:
        st.markdown("## VS")
    with col_fb:
        rb_row = tp[tp["team"]==tb]
        if not rb_row.empty:
            r = rb_row.iloc[0]
            champion_badge = " 🏆" if ch == tb else ""
            st.markdown(f"### {tb}{champion_badge}")
            st.metric("Victoires en tournoi", f"{cmp['wins_b']}/{cmp['matches_b']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Possession moy.", f"{r['avg_possession']:.0f}%")
            c2.metric("Buts / match", f"{r['goals_per_match']:.1f}")
            c3.metric("Concédés / m", f"{r['conceded_per_match']:.1f}")

    # Tableau comparatif détaillé
    comp_rows = cmp["comparison"]
    if comp_rows:
        comp_data = []
        for m in comp_rows:
            adv_a = "✅" if m["advantage"] == ta else ("❌" if m["advantage"] == tb else "=")
            adv_b = "✅" if m["advantage"] == tb else ("❌" if m["advantage"] == ta else "=")
            va_fmt = f"{m['val_a']:.1f}{m['unit']}"
            vb_fmt = f"{m['val_b']:.1f}{m['unit']}"
            comp_data.append({ta: f"{adv_a} {va_fmt}", "Statistique": m["label"], tb: f"{vb_fmt} {adv_b}"})
        st.dataframe(pd.DataFrame(comp_data), width="stretch", hide_index=True)

    if ch:
        insight_card(
            f"<b>Champion CDM 2026 : {ch}</b> — "
            + ("Défense légendaire (0.1 but concédé/m) et domination technique." if ch == "Spain"
               else "Attaque de feu (2.7 buts/m) et réalisme clinique en finale."),
            GREEN,
        )
    else:
        insight_card(
            f"<b>La finale se joue !</b> Spain (défense) vs Argentina (attaque). "
            "L'app se met à jour automatiquement après le coup de sifflet final.",
            "#f39c12",
        )

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
        "Spain et Argentina : deux styles opposés ou deux profils proches ? "
        "Le clustering révèle la réponse."
    )
with c4:
    st.markdown("#### 🤖 Modèle IA")
    st.markdown(
        "79% d'accuracy. Résultat contre-intuitif : "
        "les tirs bruts ont un coefficient négatif."
    )

st.divider()

# ── SCATTER COMPLET : TOUS LES STYLES ────────────────────────────────────────
st.subheader("Portrait statistique des 48 équipes")
st.caption("Possession vs buts marqués par match. Taille = matchs gagnés. Finalisent en étoile.")

scatter_df = tp[tp["matches"] >= 3].copy()
finalist_teams = set()
if cmp:
    finalist_teams = {cmp["team_a"], cmp["team_b"]}

scatter_df["is_finalist"] = scatter_df["team"].isin(finalist_teams)
scatter_df["is_champion"] = scatter_df["team"] == (cmp["champion"] if cmp else "")

# On ne nomme que les equipes marquantes pour eviter le fouillis
_top = set(scatter_df.nlargest(7, "goals_per_match")["team"])
_ext = set(scatter_df.nlargest(2, "avg_possession")["team"]) | set(scatter_df.nsmallest(2, "avg_possession")["team"])
_to_label = _top | _ext | finalist_teams
scatter_df["show_label"] = scatter_df["team"].isin(_to_label)

fig_s = go.Figure()
# Non-finalistes
nf = scatter_df[~scatter_df["is_finalist"]]
fig_s.add_trace(go.Scatter(
    x=nf["avg_possession"], y=nf["goals_per_match"],
    mode="markers+text",
    text=[r["team"] if r["show_label"] else "" for _, r in nf.iterrows()],
    textposition="top center",
    textfont=dict(size=9, color="#334155"),
    marker=dict(
        size=nf["wins"] * 3 + 7,
        color=nf["win_rate"],
        colorscale="RdYlGn",
        cmin=0, cmax=100,
        opacity=0.8,
        colorbar=dict(title="Victoires %", thickness=12),
    ),
    hovertemplate="<b>%{customdata}</b><br>Possession : %{x:.0f}%<br>Buts/match : %{y:.1f}<extra></extra>",
    customdata=nf["team"],
    name="Équipes",
    showlegend=False,
))
# Finalistes en étoile
for _, row in scatter_df[scatter_df["is_finalist"]].iterrows():
    is_champ = row["is_champion"]
    color = "#FFD700" if is_champ else "#00B140"
    label = row["team"] + (" 🏆" if is_champ else " ⭐")
    fig_s.add_trace(go.Scatter(
        x=[row["avg_possession"]], y=[row["goals_per_match"]],
        mode="markers+text",
        text=[label],
        textposition="top center",
        textfont=dict(size=12, color="#1a1d23", family="Arial Black"),
        marker=dict(size=22, symbol="star", color=color, line=dict(color="#1a1d23", width=1.5)),
        name=row["team"],
        hovertemplate=f"<b>{row['team']}</b><br>Possession : {row['avg_possession']:.0f}%<br>Buts/match : {row['goals_per_match']:.1f}<br>Victoires : {row['win_rate']:.0f}%<extra></extra>",
    ))

fig_s.add_vline(x=50, line_dash="dot", line_color="#94a3b8", annotation_text="50 %")
fig_s.update_layout(
    xaxis_title="Possession moyenne (%)",
    yaxis_title="Buts marqués par match",
    template="simple_white",
    height=500,
    margin=dict(t=30, b=10),
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig_s, width="stretch")

st.divider()

# ── BILAN DU TOURNOI ─────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])
with col_left:
    st.subheader("Bilan du tournoi")
    if not df.empty and "round" in df.columns:
        _order = {"Group": 0, "Round of 32": 1, "Round of 16": 2,
                  "Quarter": 3, "Semi": 4, "Final": 5, "3rd": 6}
        rc = df.groupby("round").size().reset_index(name="n")
        rc["_s"] = rc["round"].apply(
            lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
        )
        rc = rc.sort_values("_s").drop(columns="_s")
        colors = ["#00B140" if "Group" in r else "#3498db" if any(x in r for x in ["32","16"])
                  else "#f39c12" if any(x in r for x in ["Quarter","Semi","Final","3rd"])
                  else "#888" for r in rc["round"]]
        fig = go.Figure(go.Bar(
            x=rc["round"], y=rc["n"], text=rc["n"], textposition="outside",
            marker_color=colors,
        ))
        fig.update_layout(template="simple_white", height=260,
                          margin=dict(t=10, b=0), yaxis_title="Matchs", showlegend=False)
        st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("Résultats clés")
    if not df.empty:
        key_rounds = df[df["round"].isin(["Semi-finals","Final","3rd Place Final"])].sort_values("fixture_id")
        for _, r in key_rounds.iterrows():
            date = str(r["date"])[:10]
            hg, ag = int(r["home_goals"]), int(r["away_goals"])
            st.markdown(f"**{r['home_team']}** {hg}–{ag} **{r['away_team']}** `{r['round']}`")

st.divider()

# ── TOP ÉQUIPES ───────────────────────────────────────────────────────────────
st.subheader("Les 6 équipes les plus efficaces du tournoi")
st.caption("Efficiency score = victoires / possession — qui a fait le plus avec le moins ? Données réelles.")

top = tp[tp["matches"] >= 3].nlargest(6, "efficiency_score")
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
    "Source : The Stats Zone (pages publiques FIFA World Cup 2026) · "
    "[Code source](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)"
)
