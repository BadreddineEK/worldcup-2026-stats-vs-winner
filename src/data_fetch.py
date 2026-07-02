"""
src/data_fetch.py — Récupération des données réelles de la Coupe du Monde 2026.

Source principale : API-Football (https://www.api-football.com/).
  - Endpoint direct : https://v3.football.api-sports.io
  - Authentification : header `x-apisports-key` (clé du plan gratuit).
  - Ligue "FIFA World Cup" = id 1, saison 2026.

Ce module ne fait QUE parler à l'API et normaliser la réponse.
Un cache disque avec TTL évite de brûler le quota gratuit (100 req/jour)
tout en gardant les données fraîches pendant un tournoi EN COURS.

Aucune donnée n'est inventée : si l'API ne renvoie rien, on renvoie du vide.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

# ─────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────
API_BASE = "https://v3.football.api-sports.io"
WORLD_CUP_LEAGUE_ID = 1          # FIFA World Cup dans API-Football
SEASON = 2026
REQUEST_TIMEOUT = 20             # secondes

# Cache disque : le tournoi est EN COURS, on veut des données fraîches
# mais sans rappeler l'API à chaque rerun Streamlit.
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / ".cache"
CACHE_TTL_SECONDS = 3 * 60 * 60  # 3 heures


# ─────────────────────────────────────────────────────────────
# CLÉ API
# ─────────────────────────────────────────────────────────────
def get_api_key() -> str | None:
    """
    Récupère la clé API sans jamais la coder en dur.

    Ordre : st.secrets["API_FOOTBALL_KEY"] → variable d'env API_FOOTBALL_KEY.
    Renvoie None si aucune clé n'est configurée (l'app bascule alors sur le CSV
    de secours).
    """
    # 1) Streamlit secrets (Cloud + .streamlit/secrets.toml en local)
    try:
        import streamlit as st  # import local : le module reste utilisable hors Streamlit

        if "API_FOOTBALL_KEY" in st.secrets:
            key = str(st.secrets["API_FOOTBALL_KEY"]).strip()
            if key and key != "collez_votre_cle_ici":
                return key
    except Exception:
        pass

    # 2) Variable d'environnement (scripts, CI, dev)
    key = os.environ.get("API_FOOTBALL_KEY", "").strip()
    if key and key != "collez_votre_cle_ici":
        return key

    return None


# ─────────────────────────────────────────────────────────────
# CACHE DISQUE (TTL)
# ─────────────────────────────────────────────────────────────
def _cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return CACHE_DIR / f"{safe}.json"


def _read_cache(name: str, ttl: int = CACHE_TTL_SECONDS) -> Any | None:
    path = _cache_path(name)
    if not path.exists():
        return None
    if time.time() - path.stat().st_mtime > ttl:
        return None  # périmé : on rappellera l'API
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_cache(name: str, payload: Any) -> None:
    try:
        _cache_path(name).write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )
    except Exception:
        pass  # un cache qui échoue ne doit jamais casser l'app


# ─────────────────────────────────────────────────────────────
# REQUÊTE BAS NIVEAU
# ─────────────────────────────────────────────────────────────
def _request(path: str, params: dict[str, Any], cache_name: str) -> list[dict]:
    """
    Appelle l'API-Football et renvoie la liste `response`.

    - Sert d'abord le cache disque s'il est encore frais.
    - En cas d'erreur réseau/quota, renvoie le dernier cache disponible
      (même périmé) plutôt que de planter — on affichera l'âge de la donnée.
    """
    fresh = _read_cache(cache_name)
    if fresh is not None:
        return fresh

    key = get_api_key()
    if not key:
        return []

    try:
        resp = requests.get(
            f"{API_BASE}/{path}",
            headers={"x-apisports-key": key},
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        response = data.get("response", []) or []
        if response:  # ne cache que des réponses utiles
            _write_cache(cache_name, response)
        return response
    except Exception:
        # Repli : dernier cache connu, même périmé (mieux que rien)
        stale = _read_cache(cache_name, ttl=10**9)
        return stale if stale is not None else []


# ─────────────────────────────────────────────────────────────
# API PUBLIQUE DU MODULE
# ─────────────────────────────────────────────────────────────
def fetch_worldcup_2026_matches() -> list[dict]:
    """
    Renvoie tous les matchs (fixtures) de la Coupe du Monde 2026, normalisés.

    Chaque élément :
        {
          "fixture_id": int,
          "date": "2026-06-11T18:00:00+00:00",
          "round": "Group Stage - 1",
          "status": "FT" | "NS" | "1H" | ...,   # FT = terminé
          "is_finished": bool,
          "home_team": str,
          "away_team": str,
          "home_goals": int | None,
          "away_goals": int | None,
          "winner": "home" | "away" | "draw" | None,
        }
    """
    raw = _request(
        "fixtures",
        {"league": WORLD_CUP_LEAGUE_ID, "season": SEASON},
        cache_name="fixtures_wc2026",
    )

    matches: list[dict] = []
    for item in raw:
        fixture = item.get("fixture", {}) or {}
        teams = item.get("teams", {}) or {}
        goals = item.get("goals", {}) or {}
        league = item.get("league", {}) or {}

        status = (fixture.get("status", {}) or {}).get("short", "NS")
        home = teams.get("home", {}) or {}
        away = teams.get("away", {}) or {}
        hg = goals.get("home")
        ag = goals.get("away")

        # Vainqueur : d'abord le flag API, sinon déduit du score
        winner = None
        if home.get("winner") is True:
            winner = "home"
        elif away.get("winner") is True:
            winner = "away"
        elif hg is not None and ag is not None:
            winner = "home" if hg > ag else "away" if ag > hg else "draw"

        matches.append(
            {
                "fixture_id": fixture.get("id"),
                "date": fixture.get("date"),
                "round": league.get("round"),
                "status": status,
                "is_finished": status in {"FT", "AET", "PEN"},
                "home_team": home.get("name"),
                "away_team": away.get("name"),
                "home_goals": hg,
                "away_goals": ag,
                "winner": winner,
            }
        )
    return matches


# Correspondance des libellés API-Football → nos colonnes
_STAT_MAP = {
    "Ball Possession": "possession",
    "Total Shots": "shots",
    "Shots on Goal": "shots_on_target",
    "Total passes": "passes",
    "Corner Kicks": "corners",
    "Yellow Cards": "yellow_cards",
    "Red Cards": "red_cards",
}


def _parse_stat_value(value: Any) -> float | int | None:
    """'55%' → 55 ; '480' → 480 ; None → None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    s = str(value).strip().replace("%", "")
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None


def fetch_match_statistics(fixture_id: int) -> dict:
    """
    Renvoie les statistiques d'un match TERMINÉ, côté domicile / extérieur.

    Structure :
        {
          "home": {"possession": 55, "shots": 14, "shots_on_target": 6,
                   "passes": 480, "corners": 7, ...},
          "away": {...},
        }
    Toute stat absente vaut None (jamais inventée).
    L'API renvoie 2 blocs : index 0 = domicile, index 1 = extérieur.
    """
    if fixture_id is None:
        return {"home": {}, "away": {}}

    raw = _request(
        "fixtures/statistics",
        {"fixture": int(fixture_id)},
        cache_name=f"stats_{fixture_id}",
    )

    sides = ["home", "away"]
    out: dict[str, dict] = {"home": {}, "away": {}}
    for idx, block in enumerate(raw[:2]):
        side = sides[idx]
        for stat in block.get("statistics", []) or []:
            label = stat.get("type")
            col = _STAT_MAP.get(label)
            if col:
                out[side][col] = _parse_stat_value(stat.get("value"))
    return out


if __name__ == "__main__":
    # Petit test manuel : python -m src.data_fetch
    ms = fetch_worldcup_2026_matches()
    print(f"{len(ms)} matchs récupérés.")
    finished = [m for m in ms if m["is_finished"]]
    print(f"{len(finished)} matchs terminés.")
    if finished:
        first = finished[0]
        print("Exemple :", first["home_team"], "vs", first["away_team"])
        print("Stats :", fetch_match_statistics(first["fixture_id"]))
