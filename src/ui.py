"""
src/ui.py — Briques d'interface partagées par toutes les pages Streamlit.

Centralise :
  - le chargement des données (cache TTL 3 h) ;
  - la sidebar du projet (contexte + navigation) ;
  - la bannière de transparence légère ;
  - helpers de mise en forme.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from .analysis import annotate_matches
from .data_build import load_matches

CACHE_TTL = 20 * 60  # 20 min — phase finale, on veut des donnees tres fraiches
GREEN = "#00B140"
RED   = "#e74c3c"
BLUE  = "#3498db"


# ─────────────────────────────────────────────────────────────
# DONNÉES
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=CACHE_TTL, show_spinner="Chargement des données…")
def get_data():
    df, meta = load_matches()
    return annotate_matches(df), meta


def clear_cache():
    get_data.clear()


# ─────────────────────────────────────────────────────────────
# MISE EN FORME
# ─────────────────────────────────────────────────────────────
def na(value) -> str:
    """Valeur ou 'non disponible'. Jamais inventée."""
    if value is None:
        return "non disponible"
    try:
        if pd.isna(value):
            return "non disponible"
    except Exception:
        pass
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def pct_color(v: float, threshold_good: float = 55, threshold_bad: float = 40) -> str:
    if v >= threshold_good:
        return GREEN
    if v <= threshold_bad:
        return RED
    return "#f39c12"


# ─────────────────────────────────────────────────────────────
# SIDEBAR PARTAGÉE
# ─────────────────────────────────────────────────────────────
def render_sidebar(meta: dict | None = None) -> None:
    """
    Sidebar contextuelle affichée sur toutes les pages.
    Rappelle l'objet du projet + les chiffres clés live.
    """
    # ── CSS responsive mobile (injecté une fois via sidebar, s'applique à toute la page)
    st.markdown("""
    <style>
    /* ── RESPONSIVE MOBILE ─────────────────────────────────────────────── */

    /* Sur téléphone (<= 480px) : empiler toutes les colonnes Streamlit */
    @media (max-width: 480px) {
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        [data-testid="stColumn"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }
        /* Titres plus petits */
        h1 { font-size: 1.4rem !important; }
        h2 { font-size: 1.15rem !important; }
        h3 { font-size: 1.0rem !important; }
        /* Métriques moins encombrantes */
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
        [data-testid="metric-container"] [data-testid="stMetricLabel"] {
            font-size: 0.72rem !important;
        }
        /* Scrollable horizontal pour les graphiques larges */
        [data-testid="stPlotlyChart"] {
            overflow-x: auto !important;
        }
    }

    /* Sur tablette (481-768px) : permettre les colonnes de se replier */
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
        }
        /* 4+ colonnes → 2 par ligne */
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(4))
            > [data-testid="stColumn"] {
            min-width: 45% !important;
            flex: 1 1 45% !important;
        }
        /* 5+ colonnes → 2 par ligne */
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(5))
            > [data-testid="stColumn"] {
            min-width: 45% !important;
            flex: 1 1 45% !important;
        }
        /* 6 colonnes → 2 par ligne */
        [data-testid="stHorizontalBlock"]:has(> div:nth-child(6))
            > [data-testid="stColumn"] {
            min-width: 45% !important;
            flex: 1 1 45% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("## ⚽ CDM 2026 Data Lab")
        n_str = str(meta["n_matches"]) if meta and meta.get("n_matches") else "101"
        st.markdown(
            f"**{n_str} matchs réels · 48 équipes**\n\n"
            "Un Data Lab qui répond à une seule question, "
            "sous toutes ses facettes :\n\n"
            "*Les statistiques de match prédisent-elles vraiment le vainqueur ?*"
        )
        st.divider()
        if meta and meta.get("n_matches"):
            st.caption(f"🕒 Données au **{meta['last_updated_str']}**")
            st.caption(f"📡 Source : **{meta.get('source', '—')}**")
            if st.button("🔄 Rafraîchir les données", use_container_width=True):
                clear_cache()
                st.rerun()
        st.divider()
        st.markdown(
            "**Navigation**\n"
            "- 📊 Stats vs Résultats\n"
            "- 🎲 Surprises du tournoi\n"
            "- 🔴 Bilan live\n"
            "- 🧬 ADN des équipes\n"
            "- 🤖 Modèle IA"
        )
        st.divider()
        st.caption(
            "Données : [The Stats Zone](https://www.thestatszone.com/fwc26/)\n\n"
            "Projet open-source : "
            "[GitHub](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)\n\n"
            "*Badreddine EL KHAMLICHI*"
        )


# ─────────────────────────────────────────────────────────────
# BANNIÈRE DE TRANSPARENCE (version compacte)
# ─────────────────────────────────────────────────────────────
def transparency_banner(meta: dict, compact: bool = False) -> None:
    """
    Rappelle la source, la fraîcheur et le périmètre de l'analyse.
    compact=True : une seule ligne caption (pour les pages internes).
    compact=False : bandeau st.info complet (pour la home).
    """
    n = meta["n_matches"]
    date_ref = meta["last_updated_str"]

    if compact:
        st.caption(
            f"📊 **{n} matchs joués** au {date_ref} · "
            f"Source : {meta['source']} · "
            "L'analyse est bornée aux matchs **terminés** uniquement."
        )
        return

    col_info, col_btn = st.columns([4, 1])
    with col_info:
        if n == 0:
            st.warning(
                "Aucun match exploitable pour l'instant. "
                f"Dernière vérification : {date_ref}."
            )
        else:
            st.info(
                f"📊 Basé sur **{n} matchs joués** au {date_ref} · "
                f"Source : **{meta['source']}** · "
                "Analyse limitée aux matchs **terminés**."
            )
    with col_btn:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            clear_cache()
            st.rerun()


# ─────────────────────────────────────────────────────────────
# MESSAGE VIDE
# ─────────────────────────────────────────────────────────────
def no_data_hint() -> None:
    st.markdown(
        "#### Pas encore de données\n"
        "Revenez après les premiers matchs terminés ⚽"
    )


# ─────────────────────────────────────────────────────────────
# HIGHLIGHT CARD (callout stylisé)
# ─────────────────────────────────────────────────────────────
def insight_card(text: str, color: str = GREEN) -> None:
    """Affiche un encadré 'insight' coloré."""
    st.markdown(
        f"""<div style="border-left:4px solid {color};
        padding:0.6rem 1rem; border-radius:0 6px 6px 0;
        background:rgba(0,0,0,0.15); margin:0.5rem 0;">
        {text}</div>""",
        unsafe_allow_html=True,
    )

