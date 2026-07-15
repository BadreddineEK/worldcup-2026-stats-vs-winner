"""
src/clustering.py — Clustering de styles de jeu (PCA + K-Means).

Groupe les equipes en 4 profils : Champions Techniques, Dominateurs Frustres,
Pragmatiques Cliniques, Defensifs Compteurs.

Inclut aussi le profil des champions historiques de la Coupe du Monde
pour contextualiser les equipes 2026.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

CLUSTER_FEATURES = [
    "avg_possession",
    "avg_shots",
    "avg_shot_accuracy",
    "avg_conversion_rate",
    "avg_passes",
]

CLUSTER_COLORS = {
    "Champions Techniques": "#00B140",
    "Dominateurs Frustres": "#3498db",
    "Pragmatiques Cliniques": "#f39c12",
    "Defensifs Compteurs": "#e74c3c",
}


def cluster_teams(
    tp: pd.DataFrame,
    n_clusters: int = 4,
    min_matches: int = 3,
) -> tuple[pd.DataFrame | None, np.ndarray | None, pd.DataFrame | None]:
    """
    Retourne (clustered_df, explained_variance, cluster_stats) ou (None,None,None).
    """
    valid = tp[tp["matches"] >= min_matches].dropna(subset=CLUSTER_FEATURES).copy()
    if len(valid) < n_clusters * 3:
        return None, None, None

    X = valid[CLUSTER_FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
    labels = km.fit_predict(X_scaled)

    valid = valid.copy()
    valid["cluster"] = labels
    valid["pca_x"] = X_pca[:, 0]
    valid["pca_y"] = X_pca[:, 1]

    cluster_names = _name_clusters(valid)
    valid["cluster_name"] = valid["cluster"].map(cluster_names)
    valid["cluster_color"] = valid["cluster_name"].map(CLUSTER_COLORS)

    cluster_stats = (
        valid.groupby("cluster_name")[CLUSTER_FEATURES + ["win_rate"]]
        .mean()
        .round(1)
    )

    return valid, pca.explained_variance_ratio_, cluster_stats


def _name_clusters(df: pd.DataFrame) -> dict[int, str]:
    """Nomme les clusters automatiquement a partir de leur centroide."""
    centroids = df.groupby("cluster")[CLUSTER_FEATURES].mean()
    poss_med = centroids["avg_possession"].median()
    conv_med = centroids["avg_conversion_rate"].median()

    names: dict[int, str] = {}
    for c, row in centroids.iterrows():
        high_poss = row["avg_possession"] >= poss_med
        high_conv = row["avg_conversion_rate"] >= conv_med
        if high_poss and high_conv:
            names[int(c)] = "Champions Techniques"
        elif high_poss:
            names[int(c)] = "Dominateurs Frustres"
        elif high_conv:
            names[int(c)] = "Pragmatiques Cliniques"
        else:
            names[int(c)] = "Defensifs Compteurs"
    return names


def get_historical_champions() -> pd.DataFrame:
    """
    Profil statistique des vainqueurs des 5 dernieres Coupes du Monde.
    Source : donnees publiques FIFA / Wikipedia (phases a elimination directe).
    Stats approximees pour les editions anterieures a 2018 (possession non officielle).
    """
    return pd.DataFrame(
        [
            {
                "year": 2022,
                "champion": "Argentina",
                "avg_possession": 52,
                "avg_shots": 13.4,
                "avg_conversion_rate": 28,
                "avg_shot_accuracy": 42,
                "win_rate": 71,
                "note": "Pragmatiques, finalistes les plus efficaces",
            },
            {
                "year": 2018,
                "champion": "France",
                "avg_possession": 51,
                "avg_shots": 12.8,
                "avg_conversion_rate": 32,
                "avg_shot_accuracy": 44,
                "win_rate": 71,
                "note": "Solides defensivement, redoutablement cliniques",
            },
            {
                "year": 2014,
                "champion": "Germany",
                "avg_possession": 58,
                "avg_shots": 16.1,
                "avg_conversion_rate": 26,
                "avg_shot_accuracy": 40,
                "win_rate": 86,
                "note": "Volume + domination, seule equipe invincible",
            },
            {
                "year": 2010,
                "champion": "Spain",
                "avg_possession": 63,
                "avg_shots": 10.9,
                "avg_conversion_rate": 23,
                "avg_shot_accuracy": 38,
                "win_rate": 71,
                "note": "La domination du ballon portee a son paroxysme",
            },
            {
                "year": 2006,
                "champion": "Italy",
                "avg_possession": 52,
                "avg_shots": 11.3,
                "avg_conversion_rate": 30,
                "avg_shot_accuracy": 43,
                "win_rate": 57,
                "note": "Defense d acier, efficacite maximale",
            },
        ]
    )


def champion_similarity(
    team_row: pd.Series,
    hist: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcule la similarite cosinus entre le profil d une equipe et chaque champion historique.
    """
    features = ["avg_possession", "avg_shots", "avg_conversion_rate", "avg_shot_accuracy"]
    hist_valid = hist.dropna(subset=features).copy()

    team_vec = np.array([team_row.get(f, np.nan) for f in features], dtype=float)
    if np.any(np.isnan(team_vec)):
        return pd.DataFrame()

    sims = []
    for _, hr in hist_valid.iterrows():
        hist_vec = np.array([hr[f] for f in features], dtype=float)
        # Similarite cosinus
        denom = np.linalg.norm(team_vec) * np.linalg.norm(hist_vec)
        cos_sim = float(np.dot(team_vec, hist_vec) / denom) if denom > 0 else 0
        sims.append(
            {
                "year": hr["year"],
                "champion": hr["champion"],
                "similarity": round(cos_sim * 100, 1),
                "note": hr["note"],
            }
        )

    return (
        pd.DataFrame(sims)
        .sort_values("similarity", ascending=False)
        .reset_index(drop=True)
    )
