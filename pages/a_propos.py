"""
pages/a_propos.py — Ce projet en toute transparence.
Page de meta-narration : choix, limites, adresse a chaque communaute.
"""
import streamlit as st
from src.i18n import t
from src.ui import render_sidebar, get_data

st.set_page_config(page_title="Transparence", page_icon=":material/info:", layout="centered")
df_raw, meta = get_data()
lang = "fr"
render_sidebar(meta)

if lang == "fr":
    st.title("Ce projet en toute transparence")
    st.markdown(
        "Avant de parcourir l'app, voici ce que j'aurais dit a chacun d'entre vous "
        "si on s'etait assis ensemble autour des donnees."
    )
    st.divider()

    with st.expander("Aux statisticiens et data scientists seniors", expanded=True):
        st.markdown("""
Je sais que ce modele est simple. 104 matchs, 5 variables, regression logistique.
C'est un choix assume, pas une ignorance.

Avec 194 observations et des features correlees (possession et passes vont ensemble),
l'intervalle de confiance sur les 79 % d'accuracy est large. Un modele plus complexe
serait moins interpretable et probablement en overfit sur ce volume de donnees.

Ce que j'aurais fait avec plus de donnees et de temps :
regression avec regularisation L2 ajustee, SHAP values, features de position des tirs
(vrai xG depuis StatsBomb ou Opta), donnees historiques sur plusieurs tournois.

Sur le proxy xG : je n'appelle plus ca xG dans l'app exactement parce que ce n'est pas
le vrai Expected Goals. C'est un indicateur proportionnel simplifie : tirs cadres fois
le taux de conversion moyen du tournoi. Utile pour comparer les equipes entre elles,
pas pour predire un match.
        """)

    with st.expander("Aux data analysts et developpeurs"):
        st.markdown("""
Le pipeline de donnees utilise du scraping respectueux (robots.txt verifie, user-agent
identifiable, cache TTL pour ne pas sur-solliciter le site). Source : The Stats Zone,
pages publiques FIFA World Cup 2026.

L'app se met a jour automatiquement (TTL 20 minutes sur Streamlit Cloud). Le CSV est
versionne sur GitHub. Chaque match terminé est cache 30 jours pour eviter les appels
repetitifs une fois les stats stabilisees.

Le code est open source. Si tu vois quelque chose a ameliorer, je suis preneur.
        """)

    with st.expander("Aux passionnes de football"):
        st.markdown("""
Les stats ne capturent pas tout. Pas les blessures en cours de tournoi, pas la
motivation d'une equipe qui joue pour son pays pour la premiere fois en finale,
pas le vent au stade de Dallas au moment d'un penalty decisif.

Ce que les chiffres de ce projet ne voient pas : les coups de pied arretes, les
changements tactiques mi-match, la fatigue cumulative, la dimension psychologique
d'une eliminatoire a tir au but.

Le modele dit que Spain gagne a X %. Ca veut dire que ses statistiques de tournoi
sont plus proches du profil gagnant historique. Ca ne dit pas qui va marquer le but
decisif ce soir.
        """)

    with st.expander("Pourquoi ce projet"):
        st.markdown("""
J'ai construit ce projet pendant le tournoi, en direct, pour plusieurs raisons.

D'abord la curiosite : est-ce que les stats de match sont vraiment predictives ?
La reponse, autour de 63 %, m'a surpris dans les deux sens. C'est suffisant pour que
ca vaille la peine d'y regarder, pas assez pour predire avec certitude.

Ensuite, c'est un terrain d'experimentation pratique. Scraping live, pipeline ETL
avec TTL, modele simple mais honnetement evalue, clustering interprete. Tout ca sur
des vraies donnees qui changent chaque jour.

Enfin, le Mondial 2026 avec 48 equipes et un round supplementaire, c'est une
edition qui n'a pas de precedent direct. Les profils de jeu sont plus varies,
les upsets plus nombreux. Un beau terrain de jeu pour la donnee.

Stack : Python, Streamlit, Plotly, scikit-learn, scraping Requests.
Donnees : The Stats Zone (pages publiques FIFA World Cup 2026).
Duree : environ 3 semaines de travail en paralelle du tournoi.
        """)

    st.divider()
    st.markdown(
        "**Badreddine EL KHAMLICHI** — Ingenieur mathematiques appliquees, Lyon. "
        "[badreddineek.com](https://badreddineek.com)"
    )
    st.caption(
        "Les donnees de ce projet sont extraites de sources publiques. "
        "Le code est open source sous licence MIT. "
        "[GitHub](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)"
    )

else:
    st.title("About this project")
    st.markdown(
        "Before you explore the app, here's what I would have told each of you "
        "if we had sat down together around the data."
    )
    st.divider()

    with st.expander("For statisticians and senior data scientists", expanded=True):
        st.markdown("""
I know the model is simple. 104 matches, 5 variables, logistic regression.
That was a deliberate choice, not a gap in knowledge.

With 194 observations and correlated features (possession and passes move together),
the confidence interval on the 79% accuracy is wide. A more complex model would be
less interpretable and likely overfit on this volume.

What I would have done with more data and time: L2-regularised regression, SHAP
values, shot position features (real xG from StatsBomb or Opta), historical data
across multiple tournaments.

On the xG proxy: I stopped calling it xG in the app precisely because it is not
real Expected Goals. It is a simplified proportional indicator — shots on target
multiplied by average tournament conversion rate. Useful for comparing teams,
not for predicting individual matches.
        """)

    with st.expander("For data analysts and developers"):
        st.markdown("""
The data pipeline uses respectful scraping (robots.txt checked, identifiable
user-agent, TTL cache to avoid hammering the server). Source: The Stats Zone,
public FIFA World Cup 2026 pages.

The app updates automatically (20-minute TTL on Streamlit Cloud). The CSV is
versioned on GitHub. Each completed match is cached for 30 days to avoid
repeated calls once stats are stable.

The code is open source. If you see something to improve, I am open to it.
        """)

    with st.expander("For football fans"):
        st.markdown("""
Stats do not capture everything. Not injuries mid-tournament, not the motivation
of a team playing in their first final, not the wind at a Dallas stadium during
a crucial penalty.

What the numbers in this project do not see: set pieces, tactical changes at
half-time, accumulated fatigue, the psychological weight of a penalty shootout.

When the model says Spain wins at X%, it means their tournament statistics are
closer to the historical winning profile. It does not say who will score the
decisive goal tonight.
        """)

    with st.expander("Why I built this"):
        st.markdown("""
I built this project during the tournament, in real time, for a few reasons.

First, genuine curiosity: are match stats actually predictive? The answer,
around 63%, surprised me in both directions. It is enough to be worth studying,
not enough to predict with confidence.

Second, it is a practical experimentation space. Live scraping, ETL pipeline
with TTL caching, a simple but honestly evaluated model, interpreted clustering.
All on real data changing every day.

Finally, the 2026 World Cup with 48 teams and an extra round has no direct
historical precedent. Playing styles are more varied, upsets more frequent.
A great playground for data.

Stack: Python, Streamlit, Plotly, scikit-learn, Requests scraping.
Data: The Stats Zone (public FIFA World Cup 2026 pages).
Time: roughly 3 weeks of work alongside the tournament.
        """)

    st.divider()
    st.markdown(
        "**Badreddine EL KHAMLICHI** — Applied mathematics engineer, Lyon. "
        "[badreddineek.com](https://badreddineek.com)"
    )
    st.caption(
        "Data in this project is extracted from public sources. "
        "Code is open source under MIT licence. "
        "[GitHub](https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner)"
    )
