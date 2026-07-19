"""
src/i18n.py — Internationalisation FR / EN.
Voix naturelle, ton direct, pas de liste a tirets en milieu de phrase.
"""

from __future__ import annotations

_T: dict[str, dict[str, str]] = {
    "nav_overview":  {"fr": "Vue d'ensemble",              "en": "Overview"},
    "nav_stats":     {"fr": "Ce que les stats revelent",    "en": "What stats reveal"},
    "nav_adn":       {"fr": "ADN et Modele",                "en": "DNA and Model"},
    "nav_finale":    {"fr": "La Finale",                    "en": "The Final"},
    "nav_about":     {"fr": "Transparence",                 "en": "About"},
    "lang_label":    {"fr": "Langue",                       "en": "Language"},

    # ── Home ────────────────────────────────────────────────────
    "home_title":    {"fr": "CDM 2026 : le bilan en donnees",
                       "en": "WC 2026: the data recap"},
    "home_subtitle": {"fr": "104 matchs. 48 equipes. Qu'est-ce que ca dit vraiment ?",
                       "en": "104 matches. 48 teams. What does it actually tell us?"},
    "home_desc":     {"fr": "La Coupe du Monde 2026 est terminee. 104 matchs, 48 equipes, 5 statistiques par match. J'ai cherche ce que les chiffres disent vraiment du football.",
                       "en": "The 2026 World Cup is over. 104 matches, 48 teams, 5 stats per game. I wanted to know what the numbers actually say about football."},
    "home_insight_key": {"fr": "L'equipe dominante a gagne",
                          "en": "Dominant team won"},
    "home_matches":  {"fr": "Matchs analyses",              "en": "Matches analysed"},
    "home_surprises":{"fr": "Surprises",                    "en": "Upsets"},
    "home_model_acc":{"fr": "Precision modele IA",          "en": "AI model accuracy"},
    "home_records":  {"fr": "Ce Mondial en chiffres",
                       "en": "This World Cup in numbers"},
    "home_final_clash": {"fr": "La finale",                 "en": "The Final"},
    "home_champion": {"fr": "Champion",                     "en": "Champion"},
    "home_top6":     {"fr": "Les 6 equipes les plus efficaces",
                       "en": "The 6 most efficient teams"},
    "home_eff_caption": {"fr": "Efficiency = victoires / possession. Qui a fait le plus avec le moins ?",
                          "en": "Efficiency = wins / possession. Who did the most with the least?"},
    "home_wins_label":  {"fr": "Victoires",                 "en": "Wins"},
    "home_portrait": {"fr": "48 equipes, un seul graphique",
                       "en": "48 teams, one chart"},
    "home_portrait_cap":{"fr": "Possession vs buts par match. Taille = matchs gagnes. Finalistes en etoile.",
                          "en": "Possession vs goals per match. Size = matches won. Finalists as stars."},
    "home_bilan":    {"fr": "Bilan du tournoi",             "en": "Tournament recap"},
    "home_key_results": {"fr": "Resultats cles",            "en": "Key results"},
    "home_source":   {"fr": "Source : The Stats Zone (pages publiques FIFA World Cup 2026).",
                       "en": "Source: The Stats Zone (public FIFA World Cup 2026 pages)."},
    "home_code":     {"fr": "Code source",                  "en": "Source code"},

    # ── Analyse ─────────────────────────────────────────────────
    "analyse_title": {"fr": "Ce que les stats revelent",
                       "en": "What the stats reveal"},
    "analyse_intro": {"fr": "L'equipe qui domine les statistiques gagne un peu moins de deux fois sur trois. Pas toujours, donc. Et c'est la tout l'interet.",
                       "en": "The statistically dominant team wins a little less than two times out of three. Not always. That's exactly what makes this interesting."},
    "analyse_dom_pct": {"fr": "Le dominant gagne",          "en": "Dominant team wins"},
    "analyse_on_N": {"fr": "sur {} matchs analysables",     "en": "out of {} analysable matches"},
    "analyse_surprises": {"fr": "Les 5 plus grands upsets du tournoi",
                           "en": "The 5 biggest upsets of the tournament"},
    "analyse_upsets_intro": {"fr": "Ces matchs ou l'equipe qui controlait le jeu n'a pas gagne.",
                              "en": "Matches where the team in control of the game did not win."},
    "analyse_dominated": {"fr": "Dominait",                 "en": "Dominated"},
    "analyse_winner":    {"fr": "Vainqueur",                "en": "Winner"},
    "analyse_poss_adv":  {"fr": "d'avantage possession",  "en": "possession advantage"},
    "analyse_xg_title":  {"fr": "Facteur chance : qui a marque plus que prevu ?",
                           "en": "Luck factor: who scored more than expected?"},
    "analyse_xg_intro":  {"fr": "Buts marques vs buts attendus (indicateur simplifie, voir page Transparence). Au-dessus de la diagonale : sur-performance.",
                           "en": "Goals scored vs expected goals (simplified proxy, see About page). Above diagonal: over-performance."},
    "analyse_by_phase":  {"fr": "Le dominant gagne-t-il plus en eliminatoires ?",
                           "en": "Does the dominant team win more in knockouts?"},
    "analyse_phase_intro": {"fr": "Le taux varie selon la phase. Les eliminatoires sont-elles plus previsibles ?",
                             "en": "The rate varies by phase. Are knockouts more predictable?"},

    # ── ADN & ML ────────────────────────────────────────────────
    "adn_title":     {"fr": "ADN des equipes et modele IA",
                       "en": "Team DNA and AI model"},
    "adn_intro":     {"fr": "48 equipes avec des styles tres differents. Et un modele entraine sur ces matchs qui arrive a predire le bon resultat dans 79 % des cas.",
                       "en": "48 teams with very different styles. A model trained on these matches predicts the right result 79% of the time."},
    "adn_scatter_title": {"fr": "48 equipes, styles de jeu",
                           "en": "48 teams, playing styles"},
    "adn_scatter_cap": {"fr": "Possession vs taux de victoire. Taille = buts marques. En haut a droite : domine et gagne.",
                         "en": "Possession vs win rate. Size = goals scored. Top right: dominates and wins."},
    "adn_profiles_title":{"fr": "4 profils qui ressortent des donnees",
                           "en": "4 profiles that emerge from the data"},
    "adn_ml_title":  {"fr": "Ce que le modele a appris",
                       "en": "What the model learned"},
    "adn_ml_intro":  {"fr": "Regression logistique entrainee sur 104 matchs reels, 79 % d'accuracy en cross-validation (5 folds).",
                       "en": "Logistic regression trained on 104 real matches, 79% accuracy via 5-fold cross-validation."},
    "adn_ml_key":    {"fr": "Le resultat contre-intuitif",  "en": "The counter-intuitive result"},
    "adn_ml_finding":{"fr": "Les tirs bruts ont un coefficient negatif dans le modele. Tirer beaucoup sans cadrer est associe a la defaite, pas a la victoire. Ce qui predit vraiment : la precision.",
                       "en": "Raw shots have a negative coefficient in the model. Shooting a lot without hitting the target is associated with losing. What actually predicts: accuracy."},
    "adn_predictor": {"fr": "Simulateur",                   "en": "Simulator"},
    "adn_pick_teams":{"fr": "Choisissez deux equipes pour estimer leurs chances respectives.",
                       "en": "Pick two teams to estimate their respective probabilities."},
    "adn_team_a":    {"fr": "Equipe A",                     "en": "Team A"},
    "adn_team_b":    {"fr": "Equipe B",                     "en": "Team B"},

    # ── Finale ──────────────────────────────────────────────────
    "finale_title":  {"fr": "La Finale : Spain vs Argentina",
                       "en": "The Final: Spain vs Argentina"},
    "finale_intro":  {"fr": "Spain : la meilleure defense du tournoi. Argentina : l'attaque la plus prolifique. Les donnees ne pouvaient pas rever mieux comme finale.",
                       "en": "Spain: the best defence of the tournament. Argentina: the most prolific attack. Data-wise, this is the perfect final matchup."},
    "finale_model_pred": {"fr": "Ce que le modele dit de cette finale",
                           "en": "What the model says about this final"},
    "finale_bracket":{"fr": "Le parcours",                  "en": "The road here"},
    "finale_simulated":{"fr": "Et si les stats avaient toujours decide ?",
                         "en": "What if stats had always decided?"},
    "finale_champion_badge": {"fr": "Champion CDM 2026",    "en": "WC 2026 Champion"},
    "finale_historic":{"fr": "Comparaison avec les champions precedents",
                        "en": "Comparison with previous champions"},
    "finale_similar_to": {"fr": "ressemble le plus au champion",
                           "en": "closest match to champion"},
    "finale_disclaimer": {"fr": "Modele entraine sur {} matchs reels. A titre analytique uniquement.",
                           "en": "Model trained on {} real matches. For analytical purposes only."},
    "finale_tbd":    {"fr": "La finale se joue. Le resultat se mettra a jour automatiquement.",
                       "en": "The final is being played. The result will update automatically."},

    # ── Records ─────────────────────────────────────────────────
    "rec_biggest_win": {"fr": "Plus grande victoire",       "en": "Biggest win"},
    "rec_most_goals":  {"fr": "Match le plus prolifique",   "en": "Highest-scoring match"},
    "rec_best_def":    {"fr": "Defense hermétique",         "en": "Best defence"},
    "rec_best_conv":   {"fr": "Conversion clinique",        "en": "Best conversion"},
    "rec_top_scorer":  {"fr": "Attaque prolifique",         "en": "Top scoring team"},
    "rec_biggest_upset":{"fr": "Plus grand upset",          "en": "Biggest upset"},

    # ── Metrics ─────────────────────────────────────────────────
    "poss_label":    {"fr": "Possession",                   "en": "Possession"},
    "shots_label":   {"fr": "Tirs par match",               "en": "Shots per match"},
    "sot_label":     {"fr": "Tirs cadres par match",        "en": "On target per match"},
    "conv_label":    {"fr": "Conversion",                   "en": "Conversion"},
    "goals_pm":      {"fr": "Buts par match",               "en": "Goals per match"},
    "conc_pm":       {"fr": "Concedes par match",           "en": "Conceded per match"},
    "win_rate":      {"fr": "Taux de victoire",             "en": "Win rate"},
    "matches":       {"fr": "Matchs",                       "en": "Matches"},
    "wins":          {"fr": "Victoires",                    "en": "Wins"},
    "goals":         {"fr": "Buts",                         "en": "Goals"},
    "refresh":       {"fr": "Rafraichir",                   "en": "Refresh"},
    "source_label":  {"fr": "Source",                       "en": "Source"},
    "data_at":       {"fr": "Donnees au",                   "en": "Data at"},
    "total_matches": {"fr": "matchs joues au total",        "en": "total matches played"},

    # ── A propos ─────────────────────────────────────────────────
    "about_title":   {"fr": "Ce projet en toute transparence",
                       "en": "About this project"},
    "about_nav":     {"fr": "Transparence",                 "en": "About"},
}


def t(key: str, lang: str = "fr") -> str:
    """Retourne la traduction d'une cle pour la langue donnee."""
    entry = _T.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("fr", key))
