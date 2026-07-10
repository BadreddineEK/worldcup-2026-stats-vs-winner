"""
pages/5_Modele_IA.py — Un modèle de machine learning entraîné sur les 96 matchs.

Question : peut-on prédire le vainqueur d'un match à partir de ses seules stats ?
Méthode : régression logistique (interprétable, adaptée au petit échantillon).
Features : possession, tirs, tirs cadrés, précision, passes, corners + différentielles.
Transparence totale sur les limites (96 matchs, modèle simple, à titre illustratif).
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.team_analysis import build_ml_dataset
from src.ui import get_data, transparency_banner

st.set_page_config(page_title="Modèle IA", page_icon="🤖", layout="wide")

st.title("🤖 Modèle IA — les stats prédisent-elles vraiment le résultat ?")
st.markdown(
    "Une régression logistique entraînée sur les **96 matchs réels** du tournoi. "
    "Elle apprend quel indicateur statistique est le plus lié à la victoire, "
    "et peut prédire l'issue d'un match hypothétique en temps réel. "
    "— *modèle simple et transparent, conçu pour apprendre, pas pour parier.*"
)

df, meta = get_data()
transparency_banner(meta)

if meta["n_matches"] < 10:
    st.info("Pas assez de matchs pour entraîner un modèle (minimum 10).")
    st.stop()

# ─────────────────────────────────────────────────────────────
# CONSTRUCTION DU MODÈLE
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=3 * 3600, show_spinner="Entraînement du modèle…")
def train_model(n_matches: int):
    """
    Entraîne et évalue la régression logistique.
    Mis en cache — re-entraîne seulement quand les données changent.
    """
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score, StratifiedKFold
    from sklearn.metrics import confusion_matrix, accuracy_score

    ml = build_ml_dataset(pd.read_csv("data/matches_2026.csv"))

    FEATURES_DIFF = ["poss_diff", "shots_diff", "sot_diff", "passes_diff", "corners_diff"]
    FEATURES_ABS  = ["possession", "shots", "shots_on_target", "shot_accuracy", "passes", "corners"]

    X_diff = ml[FEATURES_DIFF].values
    X_abs  = ml[FEATURES_ABS].values
    y      = ml["won"].values

    scaler_diff = StandardScaler().fit(X_diff)
    scaler_abs  = StandardScaler().fit(X_abs)
    Xs_diff = scaler_diff.transform(X_diff)
    Xs_abs  = scaler_abs.transform(X_abs)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # Modèle différentiel (team vs opponent)
    lr_diff = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    cv_scores_diff = cross_val_score(lr_diff, Xs_diff, y, cv=cv, scoring="accuracy")
    lr_diff.fit(Xs_diff, y)

    # Modèle absolu (stats brutes)
    lr_abs = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
    cv_scores_abs = cross_val_score(lr_abs, Xs_abs, y, cv=cv, scoring="accuracy")
    lr_abs.fit(Xs_abs, y)

    # Importance des features (coefficients normalisés)
    coefs_diff = pd.DataFrame({
        "Feature": ["Diff. Possession", "Diff. Tirs", "Diff. Tirs cadrés",
                    "Diff. Passes", "Diff. Corners"],
        "Coefficient": lr_diff.coef_[0],
        "Abs": np.abs(lr_diff.coef_[0]),
    }).sort_values("Abs", ascending=False)

    coefs_abs = pd.DataFrame({
        "Feature": ["Possession", "Tirs", "Tirs cadrés", "Précision tirs",
                    "Passes", "Corners"],
        "Coefficient": lr_abs.coef_[0],
        "Abs": np.abs(lr_abs.coef_[0]),
    }).sort_values("Abs", ascending=False)

    return {
        "lr_diff": lr_diff,
        "lr_abs": lr_abs,
        "scaler_diff": scaler_diff,
        "scaler_abs": scaler_abs,
        "cv_diff": cv_scores_diff,
        "cv_abs": cv_scores_abs,
        "coefs_diff": coefs_diff,
        "coefs_abs": coefs_abs,
        "features_diff": FEATURES_DIFF,
        "features_abs": FEATURES_ABS,
        "n_samples": len(ml),
        "base_rate": float(y.mean()),
    }

model_data = train_model(meta["n_matches"])

st.divider()

# ─────────────────────────────────────────────────────────────
# PERFORMANCE DU MODÈLE
# ─────────────────────────────────────────────────────────────
st.subheader("Performance du modèle")

acc_diff = model_data["cv_diff"].mean()
acc_abs  = model_data["cv_abs"].mean()
base     = model_data["base_rate"]

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Accuracy (modèle différentiel)",
    f"{acc_diff*100:.1f}%",
    f"+{(acc_diff - base)*100:.1f}% vs hasard",
    help="Validé par cross-validation 5-fold. Différence stat A - stat B comme features.",
)
col2.metric(
    "Accuracy (stats absolues)",
    f"{acc_abs*100:.1f}%",
    f"+{(acc_abs - base)*100:.1f}% vs hasard",
    help="Validé par cross-validation 5-fold. Stats brutes comme features.",
)
col3.metric(
    "Baseline hasard",
    f"{base*100:.1f}%",
    help="Proportion de victoires dans le dataset (2 lignes/match).",
)
col4.metric(
    "Données d'entraînement",
    f"{model_data['n_samples']} obs.",
    f"{meta['n_matches']} matchs × 2",
)

st.info(
    "📌 **Honnêteté sur les limites :** avec 192 observations et des features corrélées, "
    "ce modèle est illustratif. L'accuracy en cross-validation mesure la vraie généralisation. "
    "Un modèle utile à titre exploratoire — pas une boule de cristal."
)

st.divider()

# ─────────────────────────────────────────────────────────────
# IMPORTANCE DES FEATURES
# ─────────────────────────────────────────────────────────────
st.subheader("Quels indicateurs influencent le plus le résultat ?")

tab1, tab2 = st.tabs(["Modèle différentiel", "Stats absolues"])

with tab1:
    cd = model_data["coefs_diff"].copy()
    cd["Direction"] = cd["Coefficient"].apply(lambda v: "Favorise la victoire" if v > 0 else "Défavorise")
    fig_c1 = go.Figure(go.Bar(
        x=cd["Feature"],
        y=cd["Coefficient"],
        marker_color=["#00B140" if v > 0 else "#e74c3c" for v in cd["Coefficient"]],
        text=[f"{v:+.3f}" for v in cd["Coefficient"]],
        textposition="outside",
    ))
    fig_c1.add_hline(y=0, line_color="#555")
    fig_c1.update_layout(
        template="plotly_dark", height=380,
        yaxis_title="Coefficient (logistic regression)",
        margin=dict(t=20, b=10),
        title="Coefficient = impact d'un écart +1σ sur la probabilité de victoire",
        title_font_size=12,
    )
    st.plotly_chart(fig_c1, use_container_width=True)
    st.caption(
        "Un coefficient positif signifie que dominer *cet indicateur* est associé à la victoire. "
        "L'ampleur = force du signal. Les features sont standardisées (σ=1) pour comparaison équitable."
    )

with tab2:
    ca = model_data["coefs_abs"].copy()
    fig_c2 = go.Figure(go.Bar(
        x=ca["Feature"],
        y=ca["Coefficient"],
        marker_color=["#00B140" if v > 0 else "#e74c3c" for v in ca["Coefficient"]],
        text=[f"{v:+.3f}" for v in ca["Coefficient"]],
        textposition="outside",
    ))
    fig_c2.add_hline(y=0, line_color="#555")
    fig_c2.update_layout(
        template="plotly_dark", height=380,
        yaxis_title="Coefficient (logistic regression)",
        margin=dict(t=20, b=10),
    )
    st.plotly_chart(fig_c2, use_container_width=True)

st.divider()

# ─────────────────────────────────────────────────────────────
# PROBABILITÉ DE VICTOIRE EN FONCTION DE LA POSSESSION
# ─────────────────────────────────────────────────────────────
st.subheader("Courbe : possession → probabilité de victoire estimée")

poss_range = np.arange(20, 81, 1)
# Simuler "tout le reste = médian adversaire", varier possession uniquement
# Utilise le modèle différentiel : seul poss_diff varie
poss_probs = []
for p in poss_range:
    x = np.array([[p - 50, 0, 0, 0, 0]])  # poss_diff = p - 50 (adversaire 50%)
    xs = model_data["scaler_diff"].transform(x)
    prob = model_data["lr_diff"].predict_proba(xs)[0][1]
    poss_probs.append(prob * 100)

fig_p = go.Figure()
fig_p.add_trace(go.Scatter(
    x=poss_range, y=poss_probs,
    mode="lines", line=dict(color="#00B140", width=3),
    fill="tozeroy", fillcolor="rgba(0,177,64,0.15)",
    hovertemplate="Possession : %{x}%<br>P(victoire) : %{y:.1f}%<extra></extra>",
))
fig_p.add_vline(x=50, line_dash="dot", line_color="#888",
                annotation_text="50% (égalité)")
fig_p.add_hline(y=50, line_dash="dot", line_color="#888")
fig_p.update_layout(
    template="plotly_dark", height=360,
    xaxis_title="Possession (%)",
    yaxis_title="P(victoire) estimée (%)",
    yaxis_range=[0, 100],
    margin=dict(t=20, b=10),
)
st.plotly_chart(fig_p, use_container_width=True)
st.caption(
    "Probabilité estimée par le modèle différentiel quand *seule* la possession varie "
    "(toutes les autres stats au niveau de l'adversaire = médiane). "
    "Honnêteté : les autres variables confondantes ne sont pas contrôlées."
)

st.divider()

# ─────────────────────────────────────────────────────────────
# PRÉDICTEUR INTERACTIF
# ─────────────────────────────────────────────────────────────
st.subheader("Prédicteur interactif — entrez des stats de match")
st.markdown(
    "Simulez un match hypothétique. Le modèle estime la probabilité de victoire "
    "de l'**Équipe A** face à l'**Équipe B** en fonction des stats saisies."
)

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Équipe A**")
    poss_a = st.slider("Possession A (%)", 20, 80, 60, key="pa")
    shots_a = st.slider("Tirs A", 1, 30, 14, key="sha")
    sot_a = st.slider("Tirs cadrés A", 0, 15, 6, key="sota")
    passes_a = st.slider("Passes A", 100, 800, 500, step=20, key="pasa")
    corners_a = st.slider("Corners A", 0, 15, 5, key="cora")

with col_b:
    st.markdown("**Équipe B**")
    poss_b = 100 - poss_a
    st.metric("Possession B (%)", poss_b, help="Automatiquement complémentaire à A.")
    shots_b = st.slider("Tirs B", 1, 30, 10, key="shb")
    sot_b = st.slider("Tirs cadrés B", 0, 15, 4, key="sotb")
    passes_b = st.slider("Passes B", 100, 800, 400, step=20, key="pasb")
    corners_b = st.slider("Corners B", 0, 15, 3, key="corb")

# Prédiction avec le modèle différentiel
x_pred = np.array([[
    poss_a - poss_b,
    shots_a - shots_b,
    sot_a - sot_b,
    passes_a - passes_b,
    corners_a - corners_b,
]])
xs_pred = model_data["scaler_diff"].transform(x_pred)
prob_a = model_data["lr_diff"].predict_proba(xs_pred)[0][1]
prob_b = 1 - prob_a

col_pred1, col_pred2, col_pred3 = st.columns([2, 1, 2])
with col_pred1:
    st.metric("P(victoire Équipe A)", f"{prob_a*100:.1f}%")
    st.progress(prob_a)
with col_pred2:
    st.markdown("### VS")
with col_pred3:
    st.metric("P(victoire Équipe B)", f"{prob_b*100:.1f}%")
    st.progress(prob_b)

if prob_a > 0.65:
    st.success(f"Le modèle favorise **Équipe A** avec {prob_a*100:.1f}% de probabilité.")
elif prob_b > 0.65:
    st.warning(f"Le modèle favorise **Équipe B** avec {prob_b*100:.1f}% de probabilité.")
else:
    st.info("Pronostic incertain — le modèle ne dégage pas de favori clair (< 65%).")

st.caption(
    "⚠️ Simulation basée sur un modèle entraîné sur 96 matchs. "
    "À titre pédagogique uniquement. Le football reste imprévisible par nature."
)
