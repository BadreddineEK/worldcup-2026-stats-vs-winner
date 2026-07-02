"""
src/data_build.py — Assemble les données réelles en une table exploitable.

Pipeline :
  1. fetch_worldcup_2026_matches()  → tous les matchs (fixtures + résultats)
  2. pour chaque match TERMINÉ : fetch_match_statistics(fixture_id)
  3. → DataFrame `matches_2026`, UNE ligne par match joué, écrit dans
       data/matches_2026.csv

Tournoi EN COURS : le dataset se reconstruit à chaque exécution, borné par
le cache TTL de src.data_fetch (données rafraîchies toutes les ~3 h).

Repli : si aucune clé API / aucune donnée en ligne, on charge
data/matches_2026_manual.csv (scores officiels FIFA saisis à la main).
Aucune donnée n'est jamais inventée : une stat absente reste vide (NaN).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data_fetch import fetch_match_statistics, fetch_worldcup_2026_matches, get_api_key
from .scrape_statszone import scrape_played_matches

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_CSV = DATA_DIR / "matches_2026.csv"
MANUAL_CSV = DATA_DIR / "matches_2026_manual.csv"

# Colonnes de la table finale (ordre stable)
COLUMNS = [
    "fixture_id", "date", "round", "status",
    "home_team", "away_team", "home_goals", "away_goals", "winner",
    "home_possession", "away_possession",
    "home_shots", "away_shots",
    "home_shots_on_target", "away_shots_on_target",
    "home_passes", "away_passes",
    "home_corners", "away_corners",
    "source",
]


def _row_from_match(match: dict, stats: dict) -> dict:
    """Fusionne un match terminé et ses statistiques en une ligne de table."""
    home = stats.get("home", {}) or {}
    away = stats.get("away", {}) or {}
    return {
        "fixture_id": match.get("fixture_id"),
        "date": match.get("date"),
        "round": match.get("round"),
        "status": match.get("status"),
        "home_team": match.get("home_team"),
        "away_team": match.get("away_team"),
        "home_goals": match.get("home_goals"),
        "away_goals": match.get("away_goals"),
        "winner": match.get("winner"),
        "home_possession": home.get("possession"),
        "away_possession": away.get("possession"),
        "home_shots": home.get("shots"),
        "away_shots": away.get("shots"),
        "home_shots_on_target": home.get("shots_on_target"),
        "away_shots_on_target": away.get("shots_on_target"),
        "home_passes": home.get("passes"),
        "away_passes": away.get("passes"),
        "home_corners": home.get("corners"),
        "away_corners": away.get("corners"),
        "source": "API-Football",
    }


def _rows_to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """Convertit une liste de dicts (API ou scraper) en table normalisée."""
    df = pd.DataFrame(rows)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[COLUMNS]
    if not df.empty:
        df = df.sort_values("date").reset_index(drop=True)
    return df


def build_from_scraper() -> pd.DataFrame:
    """Source #2 : scraping The Stats Zone (quand l'API ne couvre pas 2026)."""
    rows = scrape_played_matches(with_stats=True)
    return _rows_to_dataframe(rows)


def _merge_history(new_df: pd.DataFrame) -> pd.DataFrame:
    """
    Fusionne les nouveaux matchs avec le CSV déjà versionné (data/matches_2026.csv).
    Accumule l'historique : un match déjà connu est mis à jour, les anciens sont
    conservés même s'ils sortent de la liste des « résultats récents » scrappée.
    """
    frames = []
    if OUTPUT_CSV.exists():
        try:
            frames.append(pd.read_csv(OUTPUT_CSV))
        except Exception:
            pass
    if not new_df.empty:
        frames.append(new_df)
    if not frames:
        return new_df

    merged = pd.concat(frames, ignore_index=True)
    for col in COLUMNS:
        if col not in merged.columns:
            merged[col] = pd.NA
    merged = merged[COLUMNS]
    # dernière occurrence = donnée la plus fraîche pour un même match
    merged = merged.drop_duplicates(subset="fixture_id", keep="last")
    return merged.sort_values("date").reset_index(drop=True)


def build_matches_dataframe() -> pd.DataFrame:
    """
    Interroge l'API et construit la table des matchs JOUÉS, avec leurs stats.
    Renvoie un DataFrame vide (colonnes présentes) si l'API ne répond pas.
    """
    matches = fetch_worldcup_2026_matches()
    finished = [m for m in matches if m.get("is_finished")]

    rows = [_row_from_match(m, fetch_match_statistics(m["fixture_id"])) for m in finished]

    df = pd.DataFrame(rows, columns=COLUMNS)
    if not df.empty:
        df = df.sort_values("date").reset_index(drop=True)
    return df


def _load_manual_fallback() -> pd.DataFrame:
    """Charge le CSV saisi à la main (scores officiels FIFA). Peut être vide."""
    if not MANUAL_CSV.exists():
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(MANUAL_CSV)
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[COLUMNS]
    if "source" in df.columns:
        df["source"] = df["source"].fillna("CSV manuel (FIFA officiel)")
    return df


def load_matches(force_refresh: bool = False) -> tuple[pd.DataFrame, dict]:
    """
    Point d'entrée unique utilisé par l'app.

    Renvoie (df, meta) :
        df   : table des matchs joués (peut être vide)
        meta : {
            "source": "API-Football" | "CSV manuel (FIFA officiel)" | "aucune",
            "n_matches": int,
            "last_updated": datetime (UTC),
            "last_updated_str": "02/07/2026 14:30 UTC",
            "has_api_key": bool,
            "last_match": "Belgique 2 - 2 Sénégal (2026-07-01)" | None,
        }
    """
    now = datetime.now(timezone.utc)
    has_key = get_api_key() is not None

    # Source #1 : API-Football (si une clé est configurée ET couvre 2026)
    df = build_matches_dataframe() if has_key else pd.DataFrame(columns=COLUMNS)
    source = "API-Football"

    # Source #2 : scraping The Stats Zone (le plan gratuit API ne couvre pas 2026)
    if df.empty:
        try:
            df = build_from_scraper()
        except Exception:
            df = pd.DataFrame(columns=COLUMNS)
        source = "TheStatsZone" if not df.empty else source

    # Accumule l'historique déjà collecté (matchs sortis de la liste récente)
    if not df.empty:
        df = _merge_history(df)

    # Source #3 : CSV saisi à la main (dernier recours)
    if df.empty:
        df = _load_manual_fallback()
        source = "CSV manuel (FIFA officiel)" if not df.empty else "aucune"

    # Persiste le dernier état connu (versionnable pour un déploiement rapide)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if not df.empty:
            df.to_csv(OUTPUT_CSV, index=False)
    except Exception:
        pass

    last_match = None
    if not df.empty:
        last = df.iloc[-1]
        date_only = str(last["date"])[:10]
        last_match = (
            f"{last['home_team']} {last['home_goals']} - "
            f"{last['away_goals']} {last['away_team']} ({date_only})"
        )

    meta = {
        "source": source,
        "n_matches": int(len(df)),
        "last_updated": now,
        "last_updated_str": now.strftime("%d/%m/%Y %H:%M UTC"),
        "has_api_key": has_key,
        "last_match": last_match,
    }
    return df, meta


if __name__ == "__main__":
    data, info = load_matches()
    print(info)
    print(data.head())
