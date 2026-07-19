import streamlit as st

# Initialiser la langue avant la navigation
if "lang" not in st.session_state:
    st.session_state["lang"] = "fr"

lang = st.session_state.get("lang", "fr")

_NAMES = {
    "fr": {"overview": "Vue d'ensemble", "stats": "Ce que les stats revelent",
           "adn": "ADN & Modele", "finale": "La Finale"},
    "en": {"overview": "Overview", "stats": "What stats reveal",
           "adn": "DNA & Model", "finale": "The Final"},
}
n = _NAMES.get(lang, _NAMES["fr"])

pg = st.navigation([
    st.Page("pages/home.py",    title=n["overview"], icon=":material/home:",         default=True),
    st.Page("pages/analyse.py", title=n["stats"],    icon=":material/analytics:"),
    st.Page("pages/adn_ml.py",  title=n["adn"],      icon=":material/insights:"),
    st.Page("pages/finale.py",  title=n["finale"],   icon=":material/emoji_events:"),
])
pg.run()
