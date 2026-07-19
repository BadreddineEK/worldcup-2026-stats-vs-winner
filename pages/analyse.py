"""
pages/analyse.py — Ce que les stats revelent.
Stats vs resultats, Top 5 upsets visuels, facteur chance.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.analysis import agreement_summary, annotate_matches, find_surprises, stat_agreement_by_type
from src.i18n import t
from src.ui import GREEN, RED, get_data, insight_card, render_sidebar, transparency_banner
from src.xg import team_xg_summary

st.set_page_config(page_title="Stats", page_icon=":material/analytics:", layout="wide")
df_raw, meta = get_data()
lang = "fr"
render_sidebar(meta)

st.title(t("analyse_title", lang))
st.markdown(t("analyse_intro", lang))
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
summary = agreement_summary(df_raw)
pct = summary["pct_dominant_won"]

st.divider()

# ── LE CHIFFRE CLE ───────────────────────────────────────────────────────────
col_gauge, col_text = st.columns([1, 2])
with col_gauge:
    fig_g = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct or 0,
        number={"suffix": " %", "font": {"size": 40}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": "#00B140" if (pct or 0) >= 60 else "#f39c12"},
            "steps": [{"range": [0, 50], "color": "#f1f5f9"}, {"range": [50, 100], "color": "#e8f5e9"}],
            "threshold": {"line": {"color": "#64748b", "width": 3}, "value": 50},
        },
    ))
    fig_g.update_layout(height=230, margin=dict(t=10, b=10, l=25, r=25),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_g, width="stretch")
    st.caption("L'équipe qui domine les stats a gagné dans ce pourcentage des matchs.")
with col_text:
    st.markdown(f"### {pct} % des matchs. Et ce n'est pas la statistique la plus intéressante.")
    st.markdown(
        f"Sur **{summary['n_evaluables']} matchs** avec un dominant clair, "
        f"le dominant l'emporte {pct} % du temps. "
        f"**{summary['n_surprises']} matchs** ont fini autrement."
    )

# ── QUELLE STAT PREDIT LE MIEUX ──────────────────────────────────────────────
st.markdown("**Quand une équipe mène sur une stat, gagne-t-elle le match ?**")
by_type = stat_agreement_by_type(df_raw)
if not by_type.empty:
    bt = by_type.sort_values("Taux (%)", ascending=True)
    fig_bt = go.Figure(go.Bar(
        x=bt["Taux (%)"], y=bt["Statistique"],
        orientation="h",
        marker_color=["#00B140" if v >= 60 else "#f59e0b" if v >= 50 else "#ef4444"
                      for v in bt["Taux (%)"]],
        text=[f"{v:.0f} %" for v in bt["Taux (%)"]],
        textposition="outside",
        cliponaxis=False,
    ))
    fig_bt.add_vline(x=50, line_dash="dot", line_color="#94a3b8",
                     annotation_text="Hasard (50 %)", annotation_position="top")
    fig_bt.update_layout(
        xaxis_title="L'équipe qui mène cette stat gagne (%)",
        xaxis_range=[0, 100],
        template="simple_white",
        height=230,
        margin=dict(t=30, b=10, l=10, r=40),
    )
    st.plotly_chart(fig_bt, width="stretch")
    st.caption(
        "Les tirs cadrés sont le meilleur indicateur. La possession, elle, "
        "ne dit presque rien du vainqueur."
    )

st.divider()

# ── TOP 5 UPSETS ─────────────────────────────────────────────────────────────
st.subheader(t("analyse_surprises", lang))
st.caption(t("analyse_upsets_intro", lang))

annotated = annotate_matches(df_raw)
surprises = find_surprises(annotated).copy()
if not surprises.empty:
    surprises["poss_diff"] = (surprises["home_possession"] - surprises["away_possession"]).abs()
    top5 = surprises.nlargest(min(5, len(surprises)), "poss_diff")
    for _, row in top5.iterrows():
        dom  = row["home_team"] if row["dominant_side"] == "home" else row["away_team"]
        win  = row["home_team"] if row["winner"] == "home" else row["away_team"]
        score = f"{int(row['home_goals'])}–{int(row['away_goals'])}"
        rnd   = row["round"]
        diff  = row["poss_diff"]
        with st.container(border=True):
            ca, cb, cc = st.columns([3, 2, 2])
            with ca:
                st.markdown(f"**{row['home_team']}** {score} **{row['away_team']}**")
                st.caption(rnd)
            with cb:
                st.metric("Dominait le jeu", dom, f"+{diff:.0f} % possession",
                          delta_color="off")
            with cc:
                st.metric("A gagné", win, delta_color="off")

st.divider()

# ── TAUX PAR PHASE ────────────────────────────────────────────────────────────
st.subheader(t("analyse_by_phase", lang))
st.caption(t("analyse_phase_intro", lang))
if "round" in df_raw.columns and "dominant_won" in df_raw.columns:
    _ord = {"Group": 0, "Round of 32": 1, "Round of 16": 2, "Quarter": 3, "Semi": 4, "Final": 5}
    rs = (df_raw[df_raw["dominant_won"].notna()]
          .groupby("round")
          .agg(N=("dominant_won","count"), Won=("dominant_won", lambda x: (x==True).sum()))
          .reset_index())
    rs["pct"] = (rs["Won"] / rs["N"] * 100).round(1)
    rs["_s"]  = rs["round"].apply(lambda r: next((v for k,v in _ord.items() if k.lower() in r.lower()), 9))
    rs = rs.sort_values("_s")
    fig_r = go.Figure(go.Bar(
        x=rs["round"], y=rs["pct"],
        text=[f"{v:.0f}%" for v in rs["pct"]],
        textposition="outside",
        marker_color=["#00B140" if v >= 60 else "#f59e0b" if v >= 50 else "#ef4444" for v in rs["pct"]],
        customdata=rs[["N"]].values,
        hovertemplate="%{x}<br>%{y:.1f}% (%{customdata[0]} matchs)<extra></extra>",
    ))
    fig_r.add_hline(y=50, line_dash="dot", line_color="#94a3b8")
    fig_r.update_layout(yaxis_range=[0, 100], template="simple_white", height=320,
                        margin=dict(t=20, b=10), yaxis_title=t("analyse_dom_pct", lang) + " (%)")
    st.plotly_chart(fig_r, width="stretch")

st.divider()

# ── FACTEUR CHANCE ────────────────────────────────────────────────────────────
st.subheader(t("analyse_xg_title", lang))
st.caption(t("analyse_xg_intro", lang))

xg_sum = team_xg_summary(df)
if not xg_sum.empty:
    plot_df = xg_sum[xg_sum["matches"] >= 3].copy()
    max_v = max(plot_df["xg_total"].max(), plot_df["goals_total"].max()) + 1
    fig_xg = go.Figure()
    # Diagonale de reference
    fig_xg.add_shape(type="line", x0=0, y0=0, x1=max_v, y1=max_v,
                     line=dict(color="#94a3b8", dash="dot"))
    fig_xg.add_annotation(x=max_v*0.82, y=max_v*0.9, text="Buts = attendus",
                          showarrow=False, font=dict(size=10, color="#94a3b8"))
    # On ne nomme que les equipes remarquables (sur/sous-performance nette)
    plot_df["notable"] = plot_df["overperf_total"].abs() >= 1.5
    for _, r in plot_df.iterrows():
        over = r["overperf_total"]
        color = "#00B140" if over > 0.5 else "#ef4444" if over < -0.5 else "#94a3b8"
        show_label = r["notable"]
        fig_xg.add_trace(go.Scatter(
            x=[r["xg_total"]], y=[r["goals_total"]],
            mode="markers+text" if show_label else "markers",
            text=[r["team"]] if show_label else None,
            textposition="top center",
            textfont=dict(size=10, color=color),
            marker=dict(size=13 if show_label else 9, color=color,
                        opacity=0.9 if show_label else 0.55,
                        line=dict(color="white", width=1) if show_label else None),
            hovertemplate=f"<b>{r['team']}</b><br>Buts réels : {r['goals_total']}<br>Attendus : {r['xg_total']:.1f}<br>Écart : {over:+.1f}<extra></extra>",
            showlegend=False,
        ))
    fig_xg.update_layout(
        xaxis_title="Buts attendus (proxy — voir Transparence)",
        yaxis_title="Buts réellement marqués",
        template="simple_white", height=420, margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig_xg, width="stretch")
    st.caption(
        "Au-dessus de la diagonale : l'équipe a marqué plus que ses tirs ne le "
        "laissaient prévoir (réalisme ou chance). En dessous : maladresse ou malchance. "
        "Seules les équipes les plus marquantes sont nommées."
    )
    # Top lucky / unlucky
    c1, c2 = st.columns(2)
    with c1:
        lucky = xg_sum.nlargest(3, "overperf_total")[["team","goals_total","xg_total","overperf_total"]].copy()
        lucky.columns = ["Équipe", "Buts", "Attendus", "Écart"]
        st.caption("🍀 **Ont marqué plus que prévu**")
        st.dataframe(lucky, width="stretch", hide_index=True)
    with c2:
        unlucky = xg_sum.nsmallest(3, "overperf_total")[["team","goals_total","xg_total","overperf_total"]].copy()
        unlucky.columns = ["Équipe", "Buts", "Attendus", "Écart"]
        st.caption("😬 **Ont marqué moins que prévu**")
        st.dataframe(unlucky, width="stretch", hide_index=True)

st.caption(f"Données au {meta['last_updated_str']} · Source : The Stats Zone")
