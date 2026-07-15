import streamlit as st

pg = st.navigation([
    st.Page("pages/home.py",                   title="Tableau de bord",  icon=":material/home:",      default=True),
    st.Page("pages/1_Score_vs_Stats.py",       title="Stats vs Resultats", icon=":material/bar_chart:"),
    st.Page("pages/2_Surprises_du_Tournoi.py", title="Surprises",         icon=":material/casino:"),
    st.Page("pages/3_Bilan_Live.py",           title="Bilan live",        icon=":material/circle:",),
    st.Page("pages/4_ADN_des_Equipes.py",      title="ADN des Equipes",   icon=":material/genetics:"),
    st.Page("pages/5_Modele_IA.py",            title="Modele IA",         icon=":material/smart_toy:"),
])
pg.run()
