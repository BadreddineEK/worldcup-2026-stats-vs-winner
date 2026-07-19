import streamlit as st

if "lang" not in st.session_state:
    st.session_state["lang"] = "fr"

lang = st.session_state.get("lang", "fr")

_NAMES = {
    "fr": {
        "overview": "Vue d'ensemble",
        "stats":    "Ce que les stats revelent",
        "adn":      "ADN et Modele",
        "finale":   "La Finale",
        "about":    "Transparence",
    },
    "en": {
        "overview": "Overview",
        "stats":    "What stats reveal",
        "adn":      "DNA and Model",
        "finale":   "The Final",
        "about":    "About",
    },
}
n = _NAMES.get(lang, _NAMES["fr"])

pg = st.navigation([
    st.Page("pages/home.py",      title=n["overview"], icon=":material/home:",         default=True),
    st.Page("pages/analyse.py",   title=n["stats"],    icon=":material/analytics:"),
    st.Page("pages/adn_ml.py",    title=n["adn"],      icon=":material/insights:"),
    st.Page("pages/finale.py",    title=n["finale"],   icon=":material/emoji_events:"),
    st.Page("pages/a_propos.py",  title=n["about"],    icon=":material/info:"),
])
pg.run()
