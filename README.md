# ⚽ Coupe du Monde 2026 — les stats prédisent-elles le vainqueur ?

> *« Pendant que la Coupe du Monde 2026 se joue, je me suis posé une question simple : l'équipe qui domine le match dans les chiffres — possession, tirs, tirs cadrés — gagne-t-elle vraiment ? J'ai branché de **vraies données du tournoi en cours** et laissé les résultats répondre, match après match. »*

Un dashboard **Streamlit** qui confronte, en temps réel, les **statistiques de chaque match terminé** au **résultat final** de la Coupe du Monde 2026 (11 juin → 19 juillet 2026, USA · Mexique · Canada).

Le projet assume une contrainte honnête : le **tournoi est en cours**. L'analyse ne prétend jamais être complète — elle affiche toujours *« basé sur X matchs joués au [date] »* et se met à jour à chaque exécution.

## 🎯 L'idée

Une seule question, prise au sérieux :

> **L'équipe qui domine les statistiques d'un match gagne-t-elle le match ?**

Pour chaque rencontre terminée, on regarde qui mène sur trois indicateurs — **possession**, **tirs**, **tirs cadrés** — on en déduit une équipe « dominante », puis on vérifie si elle a gagné. On en tire :

- un **taux global** : « le dominant l'emporte X % du temps » ;
- un **classement des stats** les plus prédictives ;
- la liste des **surprises** : ces matchs où le foot a défié les chiffres.

## 🗂️ Les données (réelles, tournoi en cours)

Les données proviennent, **par ordre de priorité** :

1. **[API-Football](https://www.api-football.com/)** *(source principale)* — plan gratuit, couvre la *FIFA World Cup 2026* (ligue `id = 1`, saison `2026`). On y lit les *fixtures*, scores et l'endpoint *statistics* (possession, tirs, tirs cadrés, passes, corners, cartons) pour chaque match **terminé**.
2. **Scraping respectueux** *(repli, optionnel)* — les pages *Match Centre* de [thestatszone.com/fwc26](https://www.thestatszone.com/fwc26/matches/results) fournissent des stats détaillées une fois le match fini. À n'utiliser **que** si le quota API est épuisé et **dans le respect des CGU du site** (vérifier `robots.txt`, limiter la fréquence).
3. **Saisie manuelle** *(dernier recours)* — [`data/matches_2026_manual.csv`](data/matches_2026_manual.csv) : scores officiels FIFA + stats disponibles publiquement, saisis à la main, avec la source documentée dans la colonne `source`.

> 🔒 **Transparence** — aucune donnée n'est inventée. Une statistique absente est affichée **« non disponible »**, jamais estimée. Chaque page rappelle la **source** et l'**heure de dernière mise à jour**.

## 🔬 Ce que montre le dashboard

| Page | Question posée |
|------|----------------|
| **Accueil** (`app.py`) | Où en est le tournoi ? Combien de matchs joués, quelle phase, quel dernier résultat ? |
| **Score vs Stats** | L'équipe qui domine les stats a-t-elle gagné ? Quelle stat prédit le mieux ? |
| **Surprises du tournoi** | Quels matchs contredisent les stats dominantes ? Quels sont les plus serrés (prolongation, tirs au but) ? |
| **Bilan live** | Les tout derniers résultats, remis à jour à chaque lancement, exportables en CSV. |

## 🧠 La lecture data

- **Dominer n'est pas gagner** : au football, un fort volume de possession ou de tirs ne se convertit pas mécaniquement en victoire. Le dashboard chiffre cet écart.
- **Petit échantillon = prudence** : sur un tournoi en cours, quelques matchs ne font pas une loi. D'où l'affichage systématique du nombre de matchs et de la date.
- **Honnêteté sur la donnée** : on visualise ce que disent des stats officielles de matchs terminés — pas une prédiction, pas une preuve causale.

## 🛠️ Stack technique

- Python 3.11+
- Streamlit (dashboard multi-pages)
- Requests (appels API + cache disque TTL)
- Pandas (assemblage et analyse)
- Plotly (visualisations)

## 🔑 Obtenir une clé API gratuite (API-Football)

1. Créez un compte sur **https://www.api-football.com/** (plan **Free**, ~100 requêtes/jour).
2. Dans le **Dashboard**, ouvrez l'onglet **« API Keys »** (ou *My Access*) et copiez votre clé.
3. En local, créez le fichier `.streamlit/secrets.toml` à partir du modèle fourni :

   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

   puis collez votre clé :

   ```toml
   API_FOOTBALL_KEY = "votre_cle_ici"
   ```

   > `.streamlit/secrets.toml` est **ignoré par git** (voir `.gitignore`) : votre clé n'est jamais publiée.

   Alternative sans Streamlit (scripts) : variable d'environnement `API_FOOTBALL_KEY`.

Sans clé configurée, l'app fonctionne quand même : elle bascule sur le CSV de secours et l'indique clairement.

## 🚀 Lancer l'app en local

```bash
git clone https://github.com/BadreddineEK/worldcup-2026-stats-vs-winner
cd worldcup-2026-stats-vs-winner
pip install -r requirements.txt
# (optionnel mais recommandé) configurer la clé API — voir ci-dessus
streamlit run app.py
```

L'app s'ouvre sur http://localhost:8501.

## 🔄 Régénérer le dataset à la main

Le pipeline se reconstruit tout seul à chaque exécution (cache TTL de 3 h, adapté à un tournoi en cours). Pour forcer une reconstruction depuis la ligne de commande :

```bash
python -m src.data_build      # écrit data/matches_2026.csv
python -m src.data_fetch      # test rapide de connexion à l'API
```

## 📁 Structure du projet

```
├── app.py                          # Accueil : vue d'ensemble du tournoi
├── pages/
│   ├── 1_Score_vs_Stats.py         # Le dominant a-t-il gagné ?
│   ├── 2_Surprises_du_Tournoi.py   # Quand le résultat défie les stats
│   └── 3_Bilan_Live.py             # Derniers résultats, MAJ à chaque lancement
├── src/
│   ├── data_fetch.py               # Appels API-Football + cache TTL
│   ├── data_build.py               # Assemble matches_2026.csv (1 ligne / match joué)
│   ├── analysis.py                 # Domination stats vs résultat, surprises
│   └── ui.py                       # Briques Streamlit partagées (transparence)
├── data/
│   ├── matches_2026_manual.csv     # Repli : scores officiels FIFA saisis à la main
│   └── .cache/                     # Cache disque des réponses API (non versionné)
├── .streamlit/
│   ├── config.toml                 # Thème
│   └── secrets.toml.example        # Modèle de clé API (à copier, jamais commité)
├── requirements.txt
├── LICENSE
└── README.md
```

## ☁️ Déploiement sur Streamlit Community Cloud

1. Poussez le repo sur GitHub (voir plus bas).
2. Allez sur **https://share.streamlit.io** → **New app**.
3. Sélectionnez le repo `BadreddineEK/worldcup-2026-stats-vs-winner`, branche `main`, fichier principal `app.py`.
4. Ouvrez **Advanced settings ▸ Secrets** et collez :

   ```toml
   API_FOOTBALL_KEY = "votre_cle_ici"
   ```

   C'est l'équivalent Cloud de `.streamlit/secrets.toml` : la clé est lue via `st.secrets["API_FOOTBALL_KEY"]`, jamais écrite dans le code.
5. **Deploy**. À chaque `git push`, l'app se redéploie ; les données se rafraîchissent selon le cache TTL.

## 📄 Licence

MIT — voir [LICENSE](LICENSE).
Données de match : **API-Football** (© les fournisseurs respectifs) pour les rencontres terminées ; scores officiels **FIFA** pour le repli manuel. Respectez les CGU de chaque source avant toute réutilisation.

---

*Badreddine EL KHAMLICHI · Ingénieur en mathématiques appliquées · Lyon · [badreddineek.com](https://badreddineek.com)*
