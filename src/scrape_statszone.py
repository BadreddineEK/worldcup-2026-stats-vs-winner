"""
src/scrape_statszone.py — Source #2 : scraping respectueux de The Stats Zone.

Utilisé quand API-Football (plan gratuit) ne couvre pas la saison 2026.
Source : pages publiques FIFA World Cup 2026 de https://www.thestatszone.com/fwc26/
  - /fwc26/matches/results  → liste des matchs terminés (équipes, score, statut)
  - /fwc26/matches/<id>     → statistiques détaillées d'un match (Match Centre)

Respect des CGU :
  - robots.txt autorise /fwc26/ (seuls /actions/, /cache/, /search/… sont interdits) ;
  - User-Agent identifiable, délai entre requêtes, cache disque pour ne pas
    marteler le site (les stats d'un match terminé ne changent plus).

Aucune donnée inventée : une stat absente reste None.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://www.thestatszone.com"
RESULTS_URL = f"{BASE}/fwc26/matches/results"
MATCH_URL = f"{BASE}/fwc26/matches/{{}}"
HEADERS = {"User-Agent": "WC2026StatsScout/1.0 (projet perso; contact via badreddineek.com)"}
REQUEST_TIMEOUT = 20
POLITE_DELAY = 0.8  # secondes entre deux fiches match

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / ".cache"
RESULTS_TTL = 60 * 60           # 1 h : la liste évolue pendant le tournoi
MATCH_TTL = 30 * 24 * 60 * 60   # ~30 j : un match terminé ne change plus

# Libellés The Stats Zone → nos colonnes
_STAT_MAP = {
    "Possession": "possession",
    "Shots": "shots",
    "Shots on target": "shots_on_target",
    "Passes": "passes",
    "Corners": "corners",
}


# ─────────────────────────────────────────────────────────────
# CACHE / HTTP
# ─────────────────────────────────────────────────────────────
def _cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"tsz_{name}.html"


def _get(url: str, cache_name: str, ttl: int) -> str:
    path = _cache_path(cache_name)
    if path.exists() and time.time() - path.stat().st_mtime < ttl:
        return path.read_text(encoding="utf-8", errors="ignore")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        path.write_text(resp.text, encoding="utf-8", errors="ignore")
        return resp.text
    except Exception:
        if path.exists():  # repli : dernier cache, même périmé
            return path.read_text(encoding="utf-8", errors="ignore")
        return ""


# ─────────────────────────────────────────────────────────────
# PARSING — LISTE DES RÉSULTATS
# ─────────────────────────────────────────────────────────────
_ITEM_RE = re.compile(
    r'data-local-match-item data-local-kickoff="(?P<kickoff>[^"]+)">'
    r'.*?/fwc26/matches/(?P<id>\d+)"'
    r'.*?text-slate-500[^>]*>\s*(?P<status>[A-Za-z]+)\s*</div>'
    r'.*?<div>(?P<round>[^<]+)</div>'
    r'.*?truncate">(?P<home>[^<]+)</div>\s*'
    r'<div class="text-right[^>]*tabular-nums">(?P<hg>\d+)</div>'
    r'.*?truncate">(?P<away>[^<]+)</div>\s*'
    r'<div class="text-right[^>]*tabular-nums">(?P<ag>\d+)</div>'
    r'(?P<tail>.*?)</a>',
    re.S,
)
_PEN_RE = re.compile(r"PEN\s*·\s*(.+?)\s+won after penalties", re.I)
_TAG_RE = re.compile(r"<[^>]+>")


def _norm_status(raw: str) -> str:
    s = raw.strip().upper()
    return {"PENS": "PEN", "PEN": "PEN", "AET": "AET", "FT": "FT"}.get(s, s)


def parse_results(html: str) -> list[dict]:
    """Extrait la liste des matchs terminés depuis la page results."""
    matches: list[dict] = []
    for m in _ITEM_RE.finditer(html):
        status = _norm_status(m.group("status"))
        hg, ag = int(m.group("hg")), int(m.group("ag"))
        home, away = m.group("home").strip(), m.group("away").strip()

        winner = None
        if status == "PEN":
            tail_text = _TAG_RE.sub(" ", m.group("tail"))
            pen = _PEN_RE.search(tail_text)
            if pen:
                won = pen.group(1).strip().lower()
                winner = "home" if won == home.lower() else "away" if won == away.lower() else "draw"
        elif hg > ag:
            winner = "home"
        elif ag > hg:
            winner = "away"
        else:
            winner = "draw"

        matches.append(
            {
                "fixture_id": int(m.group("id")),
                "date": m.group("kickoff"),
                "round": m.group("round").strip(),
                "status": status,
                "is_finished": status in {"FT", "AET", "PEN"},
                "home_team": home,
                "away_team": away,
                "home_goals": hg,
                "away_goals": ag,
                "winner": winner,
            }
        )
    return matches


def fetch_results_list() -> list[dict]:
    """Récupère la liste des matchs terminés récents (page results)."""
    html = _get(RESULTS_URL, "results", RESULTS_TTL)
    return parse_results(html) if html else []


# ─────────────────────────────────────────────────────────────
# PARSING — STATS D'UN MATCH
# ─────────────────────────────────────────────────────────────
_STAT_ROW_RE = re.compile(
    r'tabular-nums[^>]*>([^<]+)</div>\s*'
    r'<div class="text-center[^>]*>([^<]+)</div>\s*'
    r'<div[^>]*tabular-nums[^>]*>([^<]+)</div>'
)


def _to_num(txt: str):
    s = txt.strip().replace("%", "")
    if s == "":
        return None
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None


def fetch_match_stats(fixture_id: int) -> dict:
    """Renvoie {'home': {...}, 'away': {...}} pour les 5 stats suivies."""
    html = _get(MATCH_URL.format(fixture_id), f"match_{fixture_id}", MATCH_TTL)
    out = {"home": {}, "away": {}}
    if not html:
        return out
    for home_val, label, away_val in _STAT_ROW_RE.findall(html):
        col = _STAT_MAP.get(label.strip())
        if col and col not in out["home"]:  # 1re occurrence = bloc principal
            out["home"][col] = _to_num(home_val)
            out["away"][col] = _to_num(away_val)
    return out


# ─────────────────────────────────────────────────────────────
# ASSEMBLAGE
# ─────────────────────────────────────────────────────────────
def scrape_played_matches(with_stats: bool = True) -> list[dict]:
    """
    Renvoie les matchs terminés récents, enrichis de leurs statistiques.
    Format identique à src.data_fetch (mêmes clés) pour brancher data_build.
    """
    results = [m for m in fetch_results_list() if m["is_finished"]]
    rows = []
    for match in results:
        row = dict(match)
        stats = fetch_match_stats(match["fixture_id"]) if with_stats else {"home": {}, "away": {}}
        for side in ("home", "away"):
            for col, val in stats[side].items():
                row[f"{side}_{col}"] = val
        row["source"] = "TheStatsZone"
        rows.append(row)
        if with_stats:
            time.sleep(POLITE_DELAY)
    return rows


if __name__ == "__main__":
    data = scrape_played_matches()
    print(f"{len(data)} matchs terminés scrappés.")
    if data:
        ex = data[0]
        print(ex["home_team"], ex.get("home_goals"), "-",
              ex.get("away_goals"), ex["away_team"], "|", ex["status"])
        print("possession:", ex.get("home_possession"), "/", ex.get("away_possession"))
        print("tirs:", ex.get("home_shots"), "/", ex.get("away_shots"))
