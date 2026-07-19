"""
pages/adn_ml.py — ADN des equipes + Modele IA.
Efficiency scatter, 4 profils, feature importances, predicteur.
"""
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.clustering import cluster_teams, get_historical_champions, champion_similarity
from src.i18n import t
from src.team_analysis import build_ml_dataset, build_team_profiles, radar_data
from src.ui import GREEN, get_data, insight_card, render_sidebar, transparency_banner

st.set_page_config(page_title="ADN & Modele", page_icon=":material/insights:", layout="wide")
df_raw, meta = get_data()
lang = st.session_state.get("lang", "fr")
render_sidebar(meta)

st.title(t("adn_title", lang))
st.markdown(t("adn_intro", lang))
transparency_banner(meta, compact=True)

df = pd.read_csv("data/matches_2026.csv")
tp = build_team_profiles(df)

st.divider()

# ── SCATTER EFFICIENCY ────────────────────────────────────────────────────────
st.subheader(t("adn_scatter_title", lang))
st.caption(t("adn_scatter_cap", lang))

scatter = tp[tp["matches"] >= 3].copy()
finalist_teams = set()
try:
    sf = df[df["round"] == "Semi-finals"]
    for _, m in sf.iterrows():
        finalist_teams.add(m["home_team"] if m["winner"] == "home" else m["away_team"])
    final = df[df["round"] == "Final"]
    if not final.empty:
        f = final.iloc[0]
        finalist_teams = {f["home_team"], f["away_team"]}
except Exception:
    pass

scatter["is_finalist"] = scatter["team"].isin(finalist_teams)

fig_s = go.Figure()
# Equipes normales
nf = scatter[~scatter["is_finalist"]]
fig_s.add_trace(go.Scatter(
    x=nf["avg_possession"], y=nf["win_rate"],
    mode="markers+text",
    text=nf["team"].str[:5],
    textposition="top center",
    textfont=dict(size=7.5, color="#64748b"),
    marker=dict(size=nf["goals_for"].clip(1) * 1.2 + 4,
                color=nf["avg_conversion_rate"],
                colorscale="RdYlGn", cmin=20, cmax=55,
                opacity=0.75,
                colorbar=dict(title="Conv. %", thickness=10, len=0.5)),
    hovertemplate="<b>%{text}</b><br>Poss: %{x:.0f}%<br>Win: %{y:.0f}%<extra></extra>",
    showlegend=False,
))
# Finalistes en etoile
champ = None
if not df[df["round"]=="Final"].empty:
    f = df[df["round"]=="Final"].iloc[0]
    champ = f["home_team"] if f["winner"]=="home" else f["away_team"]
for _, r in scatter[scatter["is_finalist"]].iterrows():
    is_champ = r["team"] == champ
    color = "#FFD700" if is_champ else "#00B140"
    label = r["team"] + (" 🏆" if is_champ else " ⭐")
    fig_s.add_trace(go.Scatter(
        x=[r["avg_possession"]], y=[r["win_rate"]],
        mode="markers+text",
        text=[label],
        textposition="top center",
        textfont=dict(size=11, color=color, family="Arial Black"),
        marker=dict(size=20, symbol="star", color=color, line=dict(color="white", width=1.5)),
        hovertemplate=f"<b>{r['team']}</b><br>Poss: {r['avg_possession']:.0f}%<br>Win: {r['win_rate']:.0f}%<extra></extra>",
        name=r["team"],
    ))
fig_s.add_vline(x=50, line_dash="dot", line_color="#94a3b8")
fig_s.add_hline(y=50, line_dash="dot", line_color="#94a3b8")
fig_s.update_layout(
    xaxis_title=t("poss_label", lang) + " (%)",
    yaxis_title=t("win_rate", lang) + " (%)",
    template="simple_white", height=480, margin=dict(t=20, b=10),
    showlegend=len(finalist_teams) > 0,
)
st.plotly_chart(fig_s, width="stretch")

st.divider()

# ── 4 PROFILS ─────────────────────────────────────────────────────────────────
st.subheader(t("adn_profiles_title", lang))

clustered, var_ratio, cluster_stats = cluster_teams(tp)
CLUSTER_COLORS = {
    "Champions Techniques": "#00B140",
    "Dominateurs Frustres": "#3b82f6",
    "Pragmatiques Cliniques": "#f59e0b",
    "Defensifs Compteurs": "#ef4444",
}
if clustered is not None:
    cols = st.columns(4)
    for i, (cname, color) in enumerate(CLUSTER_COLORS.items()):
        teams_in = clustered[clustered["cluster_name"] == cname]["team"].tolist()
        finalists_in = [t_n for t_n in teams_in if t_n in finalist_teams]
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"**{cname.replace('Frustres', 'Frustrés').replace('Defensifs', 'Défensifs')}**")
                if cluster_stats is not None and cname in cluster_stats.index:
                    s = cluster_stats.loc[cname]
                    st.metric("Win rate", f"{s.get('win_rate',0):.0f}%")
                    st.caption(f"Poss. {s.get('avg_possession',0):.0f}% · Conv. {s.get('avg_conversion_rate',0):.0f}%")
                if finalists_in:
                    st.markdown(f"⭐ {', '.join(finalists_in)}")
                st.caption(f"{len(teams_in)} " + ("équipes" if lang == "fr" else "teams"))

st.divider()

# ── CE QUE LE MODELE A APPRIS ─────────────────────────────────────────────────
st.subheader(t("adn_ml_title", lang))
st.markdown(t("adn_ml_intro", lang))

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold

@st.cache_data(ttl=3600, show_spinner=False)
def train_model_cached(n):
    ml = build_ml_dataset(pd.read_csv("data/matches_2026.csv"))
    FEATS = ["poss_diff","shots_diff","sot_diff","passes_diff","corners_diff"]
    X, y = ml[FEATS].values, ml["won"].values
    sc = StandardScaler().fit(X)
    lr = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    cv = cross_val_score(lr, sc.transform(X), y, cv=StratifiedKFold(5,shuffle=True,random_state=42))
    lr.fit(sc.transform(X), y)
    return lr, sc, cv.mean(), cv.std(), FEATS

lr, sc, acc, acc_std, FEATS = train_model_cached(meta["n_matches"])

c_acc, c_insight = st.columns([1, 2])
with c_acc:
    st.metric("Accuracy CV 5-fold", f"{acc*100:.1f}%", f"±{acc_std*100:.1f}%")
with c_insight:
    insight_card(t("adn_ml_finding", lang), "#f59e0b")

# Feature importances — le graphique star du projet
feat_labels = (["Diff. Tirs cadrés","Diff. Possession","Diff. Passes","Diff. Tirs","Diff. Corners"]
               if lang == "fr"
               else ["Shots on target diff.","Possession diff.","Passes diff.","Shots diff.","Corners diff."])
coefs = pd.DataFrame({"Feature": feat_labels, "Coefficient": lr.coef_[0]}).sort_values("Coefficient", ascending=True)
fig_c = go.Figure(go.Bar(
    x=coefs["Coefficient"], y=coefs["Feature"],
    orientation="h",
    marker_color=["#00B140" if v > 0 else "#ef4444" for v in coefs["Coefficient"]],
    text=[f"{v:+.2f}" for v in coefs["Coefficient"]],
    textposition="outside",
))
fig_c.add_vline(x=0, line_color="#64748b")
fig_c.update_layout(
    xaxis_title="Coefficient (impact sur P(victoire))" if lang == "fr" else "Coefficient (impact on P(win))",
    template="simple_white", height=280,
    margin=dict(t=10, b=10, l=10, r=60),
)
st.plotly_chart(fig_c, width="stretch")
st.caption(
    "Un coefficient positif = dominer cette stat augmente les chances de gagner. "
    "Tirs bruts négatif = tirer plus sans cadrer = perdre." if lang == "fr"
    else "Positive = dominating this stat increases win probability. "
         "Raw shots negative = shooting more without accuracy = losing."
)

st.divider()

# ── PREDICTEUR INTERACTIF ─────────────────────────────────────────────────────
st.subheader(t("adn_predictor", lang))
st.caption(t("adn_pick_teams", lang))

all_teams = sorted(tp["team"].tolist())
c_a, c_b = st.columns(2)
with c_a:
    team_a = st.selectbox(t("adn_team_a", lang), all_teams,
                          index=all_teams.index("Spain") if "Spain" in all_teams else 0, key="adn_ta")
with c_b:
    team_b = st.selectbox(t("adn_team_b", lang), all_teams,
                          index=all_teams.index("Argentina") if "Argentina" in all_teams else 1, key="adn_tb")

if team_a != team_b:
    ra = tp[tp["team"]==team_a].iloc[0]
    rb = tp[tp["team"]==team_b].iloc[0]
    diffs = np.array([[ra["avg_possession"]-rb["avg_possession"],
                       ra["avg_shots"]-rb["avg_shots"],
                       ra["avg_shots_on_target"]-rb["avg_shots_on_target"],
                       ra["avg_passes"]-rb["avg_passes"],
                       ra["avg_corners"]-rb["avg_corners"]]])
    pa = float(lr.predict_proba(sc.transform(diffs))[0][1])
    pb_raw = float(lr.predict_proba(sc.transform(-diffs))[0][1])
    total = pa + pb_raw; pa /= total; pb = 1 - pa

    c1, cv, c2 = st.columns([2, 1, 2])
    with c1: st.metric(team_a, f"{pa*100:.1f}%"); st.progress(pa)
    with cv: st.markdown("### VS")
    with c2: st.metric(team_b, f"{pb*100:.1f}%"); st.progress(pb)

    # Radar
    la, va = radar_data(ra, tp); lb, vb = radar_data(rb, tp)
    fig_r = go.Figure()
    for name, vals, color in [(team_a, va, "#00B140"), (team_b, vb, "#3b82f6")]:
        vc = vals + [vals[0]]; lc = la + [la[0]]
        fig_r.add_trace(go.Scatterpolar(r=vc, theta=lc, fill="toself", name=name,
                                        line_color=color, fillcolor=color, opacity=0.25))
    fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                        template="simple_white", height=360, margin=dict(t=20, b=10))
    st.plotly_chart(fig_r, width="stretch")

st.caption(t("finale_disclaimer", lang).format(meta["n_matches"]))
