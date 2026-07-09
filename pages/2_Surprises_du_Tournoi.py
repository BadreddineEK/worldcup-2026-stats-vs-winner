"""
pages/2_Surprises_du_Tournoi.py — Quand le résultat défie les statistiques.
"""

import plotly.graph_objects as go
import streamlit as st

from src.analysis import find_surprises
from src.ui import get_data, na, no_data_hint, transparency_banner

st.set_page_config(page_title="Surprises du tournoi", page_icon="🎲", layout="wide")

st.title("🎲 Surprises du tournoi — le foot contre les chiffres")
df, meta = get_data()
transparency_banner(meta)

if meta["n_matches"] == 0:
    no_data_hint()
    st.stop()

st.divider()

surprises = find_surprises(df)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown(
        "Une **surprise** = l'équipe qui a dominé les statistiques du match "
        "(majorité de possession, tirs, tirs cadrés) **n'a pas gagné**. "
        "C'est là que le football raconte une autre histoire que les chiffres."
    )
with col2:
    pct_surprise = round(100 * len(surprises) / max(meta["n_matches"], 1), 1)
    st.metric(
        "Surprises détectées",
        len(surprises),
        delta=f"{pct_surprise} % des matchs",
        delta_color="off",
        help=f"Sur {meta['n_matches']} match(s) joué(s) au {meta['last_updated_str']}.",
    )

if surprises.empty:
    st.success(
        "Aucune surprise pour l'instant : quand une équipe domine les stats, "
        "elle gagne. (Ou pas encore assez de matchs joués pour en voir.)"
    )
    st.stop()

# ─────────────────────────────────────────────────────────────
# SURPRISES PAR PHASE
# ─────────────────────────────────────────────────────────────
if "round" in df.columns:
    all_eval = df[df["dominant_won"].notna()]
    phase_surp = (
        all_eval.groupby("round")
        .agg(total=("dominant_won", "count"), surprises=("is_surprise", "sum"))
        .reset_index()
    )
    phase_surp["taux_surprise"] = (phase_surp["surprises"] / phase_surp["total"] * 100).round(1)
    _order = {
        "Group": 0, "Round of 32": 1, "Round of 16": 2,
        "Quarter": 3, "Semi": 4, "Final": 5,
    }
    phase_surp["_s"] = phase_surp["round"].apply(
        lambda r: next((v for k, v in _order.items() if k.lower() in r.lower()), 9)
    )
    phase_surp = phase_surp.sort_values("_s").drop(columns="_s")
    if len(phase_surp) >= 2:
        st.subheader("Taux de surprise par phase")
        fig_ps = go.Figure(go.Bar(
            x=phase_surp["round"],
            y=phase_surp["taux_surprise"],
            text=[f"{v:.0f}%" for v in phase_surp["taux_surprise"]],
            textposition="outside",
            marker_color=["#e74c3c" if v >= 40 else "#f39c12" if v >= 25 else "#00B140"
                          for v in phase_surp["taux_surprise"]],
            customdata=phase_surp[["surprises", "total"]].values,
            hovertemplate="%{x}<br>%{customdata[0]} surprises / %{customdata[1]} matchs<extra></extra>",
        ))
        fig_ps.add_hline(y=33, line_dash="dot", line_color="#888",
                         annotation_text="1 sur 3 (33 %)")
        fig_ps.update_layout(
            yaxis_range=[0, 100], template="plotly_dark",
            height=320, margin=dict(t=30, b=10),
            yaxis_title="Taux de surprise (%)",
        )
        st.plotly_chart(fig_ps, use_container_width=True)

st.divider()
st.subheader("Les matchs qui ont trahi les statistiques")

for _, row in surprises.iloc[::-1].iterrows():
    dom = row.get("dominant_side")
    dom_team = row["home_team"] if dom == "home" else row["away_team"]
    other_team = row["away_team"] if dom == "home" else row["home_team"]
    result = f"{row['home_team']} {na(row['home_goals'])}–{na(row['away_goals'])} {row['away_team']}"

    with st.container(border=True):
        c_title, c_badge = st.columns([3, 1])
        with c_title:
            st.markdown(f"### {result}")
            st.caption(f"{row.get('round') or 'Phase non disponible'} · {str(row['date'])[:10]}")
        with c_badge:
            st.markdown(f"**Vainqueur surprise :**\n\n{other_team}")
        st.write(
            f"**{dom_team}** dominait les statistiques mais n'a pas su convertir."
        )
        cols = st.columns(3)
        cols[0].metric("Possession",
                       f"{na(row['home_possession'])}% – {na(row['away_possession'])}%")
        cols[1].metric("Tirs",
                       f"{na(row['home_shots'])} – {na(row['away_shots'])}")
        cols[2].metric("Tirs cadrés",
                       f"{na(row['home_shots_on_target'])} – {na(row['away_shots_on_target'])}")

st.divider()

# ─────────────────────────────────────────────────────────────
# MATCHS SERRÉS (faible écart de buts)
# ─────────────────────────────────────────────────────────────
st.subheader("⚔️ Les matchs les plus serrés")
tight = df.copy()
tight = tight[tight["home_goals"].notna() & tight["away_goals"].notna()]
if tight.empty:
    st.info("Pas encore de score complet disponible.")
else:
    tight["ecart"] = (tight["home_goals"] - tight["away_goals"]).abs()
    tight["prolongation"] = tight["status"].isin(["AET", "PEN"])
    tight = tight.sort_values(["ecart", "prolongation"], ascending=[True, False]).head(8)
    show = tight[["date", "round", "home_team", "home_goals",
                  "away_goals", "away_team", "status"]].copy()
    show["date"] = show["date"].astype(str).str[:10]
    show["status"] = show["status"].map(
        {"FT": "Temps réglementaire", "AET": "Prolongation", "PEN": "Tirs au but"}
    ).fillna(show["status"])
    show.columns = ["Date", "Phase", "Domicile", "Buts (D)",
                    "Buts (E)", "Extérieur", "Fin du match"]
    st.dataframe(show, use_container_width=True, hide_index=True)


st.set_page_config(page_title="Surprises du tournoi", page_icon="🎲", layout="wide")

st.title("🎲 Surprises du tournoi — le foot contre les chiffres")
df, meta = get_data()
transparency_banner(meta)

if meta["n_matches"] == 0:
    no_data_hint()
    st.stop()

st.divider()

surprises = find_surprises(df)

st.markdown(
    "Une **surprise** = l'équipe qui a dominé les statistiques du match "
    "(majorité de possession, tirs, tirs cadrés) **n'a pas gagné**. "
    "C'est là que le football raconte une autre histoire que les chiffres."
)

st.metric("Surprises détectées", len(surprises),
          help=f"Sur {meta['n_matches']} match(s) joué(s) au {meta['last_updated_str']}.")

if surprises.empty:
    st.success(
        "Aucune surprise pour l'instant : quand une équipe domine les stats, "
        "elle gagne. (Ou pas encore assez de matchs joués pour en voir.)"
    )
    st.stop()

st.divider()
st.subheader("Les matchs qui ont trahi les statistiques")

for _, row in surprises.iloc[::-1].iterrows():
    dom = row.get("dominant_side")
    dom_team = row["home_team"] if dom == "home" else row["away_team"]
    result = f"{row['home_team']} {na(row['home_goals'])}–{na(row['away_goals'])} {row['away_team']}"

    with st.container(border=True):
        st.markdown(f"### {result}")
        st.caption(f"{row.get('round') or 'Phase non disponible'} · {str(row['date'])[:10]}")
        st.write(
            f"**{dom_team}** dominait les statistiques mais n'a pas su convertir. "
        )
        cols = st.columns(3)
        cols[0].metric("Possession",
                       f"{na(row['home_possession'])}% – {na(row['away_possession'])}%")
        cols[1].metric("Tirs",
                       f"{na(row['home_shots'])} – {na(row['away_shots'])}")
        cols[2].metric("Tirs cadrés",
                       f"{na(row['home_shots_on_target'])} – {na(row['away_shots_on_target'])}")

st.divider()

# ─────────────────────────────────────────────────────────────
# MATCHS SERRÉS (faible écart de buts)
# ─────────────────────────────────────────────────────────────
st.subheader("⚔️ Les matchs les plus serrés")
tight = df.copy()
tight = tight[tight["home_goals"].notna() & tight["away_goals"].notna()]
if tight.empty:
    st.info("Pas encore de score complet disponible.")
else:
    tight["ecart"] = (tight["home_goals"] - tight["away_goals"]).abs()
    tight["prolongation"] = tight["status"].isin(["AET", "PEN"])
    tight = tight.sort_values(["ecart", "prolongation"], ascending=[True, False]).head(6)
    show = tight[["date", "round", "home_team", "home_goals",
                  "away_goals", "away_team", "status"]].copy()
    show["date"] = show["date"].astype(str).str[:10]
    show["status"] = show["status"].map(
        {"FT": "Temps réglementaire", "AET": "Prolongation", "PEN": "Tirs au but"}
    ).fillna(show["status"])
    show.columns = ["Date", "Phase", "Domicile", "Buts (D)",
                    "Buts (E)", "Extérieur", "Fin du match"]
    st.dataframe(show, use_container_width=True, hide_index=True)
    st.caption(
        "Un match nul en temps réglementaire tranché aux tirs au but (comme "
        "peut l'être un Belgique–Sénégal) apparaît ici comme « Tirs au but »."
    )
