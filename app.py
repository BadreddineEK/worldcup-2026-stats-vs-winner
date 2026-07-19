import streamlit as st

pg = st.navigation([
    st.Page("pages/home.py",     title="Vue d'ensemble",           icon=":material/home:",         default=True),
    st.Page("pages/analyse.py",  title="Ce que les stats revelent", icon=":material/analytics:"),
    st.Page("pages/adn_ml.py",   title="ADN et Modele",            icon=":material/insights:"),
    st.Page("pages/finale.py",   title="La Finale",                icon=":material/emoji_events:"),
    st.Page("pages/a_propos.py", title="Transparence",             icon=":material/info:"),
])
pg.run()
