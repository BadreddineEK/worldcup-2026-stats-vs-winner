"""
src/i18n.py — Internationalisation FR / EN.

Usage dans les pages :
    from src.i18n import t, lang_key
    lang = st.session_state.get("lang", "fr")
    st.title(t("home_title", lang))
"""

from __future__ import annotations

_T: dict[str, dict[str, str]] = {
    # ── Navigation ──────────────────────────────────────────────
    "nav_overview":  {"fr": "Vue d'ensemble",              "en": "Overview"},
    "nav_stats":     {"fr": "Ce que les stats révèlent",  "en": "What stats reveal"},
    "nav_adn":       {"fr": "ADN & Modèle",               "en": "DNA & Model"},
    "nav_finale":    {"fr": "La Finale",                   "en": "The Final"},
    "lang_label":    {"fr": "Langue",                      "en": "Language"},

    # ── Home ────────────────────────────────────────────────────
    "home_title":       {"fr": "CDM 2026 — Le Bilan en données",
                          "en": "WC 2026 — The Data Recap"},
    "home_subtitle":    {"fr": "Ce que 104 matchs de données réelles révèlent",
                          "en": "What 104 real matches reveal"},
    "home_desc":        {"fr": "La Coupe du Monde 2026 est terminée. **104 matchs · 48 équipes · 5 stats par match.** Voici ce que les chiffres disent vraiment.",
                          "en": "The 2026 World Cup is over. **104 matches · 48 teams · 5 stats per game.** Here's what the numbers really say."},
    "home_insight_key": {"fr": "L'équipe dominante a gagné",
                          "en": "The dominant team won"},
    "home_matches":     {"fr": "Matchs analysés",          "en": "Matches analysed"},
    "home_surprises":   {"fr": "Surprises",                "en": "Upsets"},
    "home_model_acc":   {"fr": "Précision modèle IA",     "en": "AI model accuracy"},
    "home_records":     {"fr": "Les chiffres qui ont marqué ce Mondial",
                          "en": "Numbers that defined this World Cup"},
    "home_final_clash": {"fr": "Le choc final",            "en": "The Final showdown"},
    "home_champion":    {"fr": "Champion",                  "en": "Champion"},
    "home_top6":        {"fr": "Les 6 équipes les plus efficaces du tournoi",
                          "en": "The 6 most efficient teams of the tournament"},
    "home_eff_caption": {"fr": "Efficiency = victoires / possession — qui a fait le plus avec le moins ?",
                          "en": "Efficiency = wins / possession — who did the most with the least?"},
    "home_wins_label":  {"fr": "Victoires",                "en": "Wins"},
    "home_poss_label":  {"fr": "Poss.",                    "en": "Poss."},
    "home_conv_label":  {"fr": "Conv.",                    "en": "Conv."},
    "home_portrait":    {"fr": "Portrait des 48 équipes",  "en": "Portrait of all 48 teams"},
    "home_portrait_cap":{"fr": "Possession vs buts par match. Taille = matchs gagnés. Finalistes en étoile.",
                          "en": "Possession vs goals per match. Size = matches won. Finalists as stars."},
    "home_bilan":       {"fr": "Bilan du tournoi",         "en": "Tournament overview"},
    "home_key_results": {"fr": "Résultats clés",           "en": "Key results"},
    "home_source":      {"fr": "Source : The Stats Zone (pages publiques FIFA World Cup 2026) ·",
                          "en": "Source: The Stats Zone (public FIFA World Cup 2026 pages) ·"},
    "home_code":        {"fr": "Code source",              "en": "Source code"},

    # ── Analyse ─────────────────────────────────────────────────
    "analyse_title":     {"fr": "Ce que les stats révèlent",
                           "en": "What the stats reveal"},
    "analyse_intro":     {"fr": "L'équipe qui domine les statistiques gagne **62,9 %** du temps. Mais ce n'est pas la stat la plus intéressante.",
                           "en": "The statistically dominant team wins **62.9%** of the time. But that's not the most interesting stat."},
    "analyse_dom_pct":   {"fr": "Le dominant gagne",      "en": "Dominant team wins"},
    "analyse_on_N":      {"fr": "sur {} matchs analysables", "en": "out of {} analysable matches"},
    "analyse_surprises": {"fr": "Top 5 — Les plus grands upsets du tournoi",
                           "en": "Top 5 — Biggest upsets of the tournament"},
    "analyse_upsets_intro": {"fr": "L'équipe qui dominait les stats n'a pas gagné. Le football contre les chiffres.",
                              "en": "The statistically dominant team lost. Football defying data."},
    "analyse_dominated": {"fr": "Dominait",               "en": "Dominated"},
    "analyse_winner":    {"fr": "Vainqueur surprise",     "en": "Surprise winner"},
    "analyse_poss_adv":  {"fr": "avantage possession",    "en": "possession advantage"},
    "analyse_xg_title":  {"fr": "Facteur chance — qui a sur-performé ?",
                           "en": "Luck factor — who over-performed?"},
    "analyse_xg_intro":  {"fr": "Buts marqués vs buts attendus (proxy). Au-dessus = chanceux, en dessous = malchanceux.",
                           "en": "Goals scored vs expected (proxy). Above line = lucky, below = unlucky."},
    "analyse_by_phase":  {"fr": "Quand le dominant gagne-t-il le plus ?",
                           "en": "When does the dominant team win most?"},
    "analyse_phase_intro": {"fr": "Le taux de victoire du dominant varie selon la phase du tournoi.",
                             "en": "The dominant team's win rate varies by tournament phase."},

    # ── ADN & ML ────────────────────────────────────────────────
    "adn_title":         {"fr": "ADN des équipes & Modèle IA",
                           "en": "Team DNA & AI Model"},
    "adn_intro":         {"fr": "48 équipes, 4 profils de jeu. Et un modèle qui prédit le vainqueur à 79%.",
                           "en": "48 teams, 4 playing styles. And a model that predicts the winner at 79%."},
    "adn_scatter_title": {"fr": "Le choc des styles — 48 équipes",
                           "en": "Battle of styles — 48 teams"},
    "adn_scatter_cap":   {"fr": "Possession vs win rate. Taille = buts marqués. À droite et en haut = domine ET gagne.",
                           "en": "Possession vs win rate. Size = goals scored. Top-right = dominates AND wins."},
    "adn_profiles_title":{"fr": "Les 4 profils du Mondial",
                           "en": "The 4 profiles of the World Cup"},
    "adn_ml_title":      {"fr": "Ce que le modèle a appris",
                           "en": "What the model learned"},
    "adn_ml_intro":      {"fr": "Régression logistique entraînée sur 104 matchs réels. **79% d'accuracy** en cross-validation.",
                           "en": "Logistic regression trained on 104 real matches. **79% accuracy** via cross-validation."},
    "adn_ml_key":        {"fr": "Le résultat contre-intuitif",
                           "en": "The counter-intuitive finding"},
    "adn_ml_finding":    {"fr": "Les **tirs bruts** ont un coefficient négatif dans le modèle. Tirer plus = moins de chances de gagner. Ce qui compte : la **précision**.",
                           "en": "**Raw shots** have a negative coefficient in the model. Shooting more = lower win probability. What matters: **accuracy**."},
    "adn_predictor":     {"fr": "Prédicteur interactif",  "en": "Interactive predictor"},
    "adn_pick_teams":    {"fr": "Choisir deux équipes pour simuler leur probabilité en finale.",
                           "en": "Pick two teams to simulate their final probability."},
    "adn_team_a":        {"fr": "Équipe A",               "en": "Team A"},
    "adn_team_b":        {"fr": "Équipe B",               "en": "Team B"},

    # ── Finale ──────────────────────────────────────────────────
    "finale_title":      {"fr": "La Finale — Spain vs Argentina",
                           "en": "The Final — Spain vs Argentina"},
    "finale_intro":      {"fr": "Le choc ultime : le dominant technique contre le pragmatique clinique. Que disent les données du tournoi ?",
                           "en": "The ultimate clash: the technical dominant vs the clinical pragmatist. What does the tournament data say?"},
    "finale_model_pred": {"fr": "Prédiction du modèle",  "en": "Model prediction"},
    "finale_bracket":    {"fr": "Parcours vers la finale","en": "Road to the final"},
    "finale_simulated":  {"fr": "Et si les stats décidaient ?",
                           "en": "What if stats always decided?"},
    "finale_champion_badge": {"fr": "Champion CDM 2026", "en": "WC 2026 Champion"},
    "finale_historic":   {"fr": "Contexte historique",   "en": "Historical context"},
    "finale_similar_to": {"fr": "ressemble le plus au champion",
                           "en": "closest match to champion"},
    "finale_disclaimer": {"fr": "Modèle entraîné sur {} matchs réels. À titre analytique.",
                           "en": "Model trained on {} real matches. For analytical purposes only."},
    "finale_tbd":        {"fr": "La finale se joue ! Résultat auto-mis à jour.",
                           "en": "The final is live! Result updates automatically."},

    # ── Records ─────────────────────────────────────────────────
    "rec_biggest_win":   {"fr": "Plus grande victoire",   "en": "Biggest win"},
    "rec_most_goals":    {"fr": "Match le plus prolifique","en": "Highest scoring match"},
    "rec_best_def":      {"fr": "Défense hermétique",     "en": "Best defence"},
    "rec_best_conv":     {"fr": "Conversion clinique",    "en": "Best conversion"},
    "rec_top_scorer":    {"fr": "Attaque prolifique",     "en": "Top scoring team"},
    "rec_biggest_upset": {"fr": "Plus grand upset",       "en": "Biggest upset"},

    # ── Metrics / Labels ────────────────────────────────────────
    "poss_label":        {"fr": "Possession",             "en": "Possession"},
    "shots_label":       {"fr": "Tirs / match",           "en": "Shots / match"},
    "sot_label":         {"fr": "Tirs cadrés / match",   "en": "On target / match"},
    "conv_label":        {"fr": "Conversion",             "en": "Conversion"},
    "goals_pm":          {"fr": "Buts / match",           "en": "Goals / match"},
    "conc_pm":           {"fr": "Concédés / m",           "en": "Conceded / m"},
    "win_rate":          {"fr": "Taux de victoire",       "en": "Win rate"},
    "matches":           {"fr": "Matchs",                 "en": "Matches"},
    "wins":              {"fr": "Victoires",              "en": "Wins"},
    "goals":             {"fr": "Buts",                   "en": "Goals"},
    "refresh":           {"fr": "Rafraîchir",             "en": "Refresh"},
    "source_label":      {"fr": "Source",                 "en": "Source"},
    "data_at":           {"fr": "Données au",             "en": "Data at"},
    "total_matches":     {"fr": "matchs joués au total",  "en": "total matches played"},
}


def t(key: str, lang: str = "fr") -> str:
    """Retourne la traduction d'une clé pour la langue donnée."""
    entry = _T.get(key)
    if entry is None:
        return key  # clé non traduite = retourner la clé telle quelle
    return entry.get(lang, entry.get("fr", key))
