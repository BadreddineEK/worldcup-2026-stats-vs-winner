"""
src/ui.py — Briques d'interface partagées par toutes les pages Streamlit.

Centralise :
  - le chargement des données mis en cache (TTL = tournoi en cours) ;
  - la bannière de transparence (source + date de MAJ + nb de matchs) ;
  - l'affichage "non disponible" pour les stats manquantes.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .analysis import annotate_matches
from .data_build import load_matches

# Cache Streamlit : évite de rappeler l'API à chaque interaction.
# TTL court car le TOURNOI EST EN COURS → données rafraîchies régulièrement.
CACHE_TTL = 3 * 60 * 60  # 3 heures


@st.cache_data(ttl=CACHE_TTL, show_spinner="Récupération des matchs 2026…")
def get_data():
    """Renvoie (df_annoté, meta). Mis en cache pendant CACHE_TTL secondes."""
    df, meta = load_matches()
    return annotate_matches(df), meta


def clear_cache():
    """Force le rechargement (bouton 'Rafraîchir maintenant')."""
    get_data.clear()


def na(value) -> str:
    """Formate une valeur, ou 'non disponible' si absente. Jamais inventée."""
    if value is None or (isinstance(value, float) and pd.isna(value)) or pd.isna(value):
        return "non disponible"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def transparency_banner(meta: dict) -> None:
    """
    Bandeau de transparence affiché en tête de chaque page.
    Rappelle la source, la fraîcheur et le périmètre réel de l'analyse.
    """
    n = meta["n_matches"]
    date_ref = meta["last_updated_str"]

    cols = st.columns([3, 1])
    with cols[0]:
        if n == 0:
            st.warning(
                f"**Aucun match exploitable pour l'instant.** "
                f"Source visée : {meta['source']}. "
                f"Dernière vérification : {date_ref}."
            )
        else:
            st.info(
                f"📊 **Basé sur {n} match(s) joué(s)** au {date_ref} · "
                f"Source : **{meta['source']}** · "
                f"L'analyse ne couvre donc PAS l'intégralité du tournoi (en cours)."
            )
    with cols[1]:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            clear_cache()
            st.rerun()

    if not meta["has_api_key"] and meta["source"] != "API-Football":
        st.caption(
            "ℹ️ Aucune clé API-Football détectée : lecture du CSV de secours. "
            "Ajoutez votre clé dans `.streamlit/secrets.toml` pour des données live."
        )


def no_data_hint() -> None:
    """Message unifié quand il n'y a encore rien à analyser."""
    st.markdown(
        "#### Pas encore de match exploitable\n"
        "- Soit le tournoi n'a pas encore livré de match terminé avec statistiques,\n"
        "- soit la clé API n'est pas configurée (voir le README).\n\n"
        "Revenez après les premiers coups de sifflet finaux ⚽"
    )
