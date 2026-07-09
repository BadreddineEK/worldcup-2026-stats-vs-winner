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

import html as html_lib
import re
import time
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
# PARSING — LISTE DES RÉSULTATS (item-level, sans fuite inter-items)
# ─────────────────────────────────────────────────────────────
# Chaque item est découpé AVANT le parsing → plus de capture cross-item.
_KICKOFF_RE = re.compile(r'data-local-kickoff="([^"]+)"')
_HREF_ID_RE = re.compile(r'/fwc26/matches/(\d+)"')
_STATUS_RE  = re.compile(r'text-slate-500[^>]*>\s*([A-Za-z]+)\s*</div>', re.S)
_ROUND_RE   = re.compile(r'<div>([^<]{2,})</div>')
# Layout standard : team dans <div ...truncate">
_TEAM_DIV_RE   = re.compile(r'truncate">([^<]+)</div>', re.S)
# Layout "featured" (MATCH 96 etc.) : team dans <span ...sm:inline truncate">
_TEAM_SPAN_RE  = re.compile(r'sm:inline truncate[^"]*">([^<]+)</span>', re.S)
# Layout standard : goals séparés dans deux divs tabular-nums
_GOALS_RE   = re.compile(r'text-right[^>]*tabular-nums[^>]*>(\d+)</div>', re.S)
# Layout featured : score combiné "X-Y" dans un seul div tabular-nums
_SCORE_COMB_RE = re.compile(r'tabular-nums[^>]*>(\d+)-(\d+)</div>', re.S)
# Round pour layout featured : <div class="inline-block ...">Round of 16</div>
_ROUND_FEATURED_RE = re.compile(
    r'inline-block[^>]*>([^<]*(?:Round of \d+|Group [A-L]|Quarter|Semi|Final)[^<]*)</div>',
    re.I,
)
_TAG_RE     = re.compile(r"<[^>]+>")
_PEN_RE     = re.compile(r"PEN\s*[·•]\s*(.+?)\s+won after penalties", re.I)
_AET_RE     = re.compile(r"(?:AET|EXTRA[\s\-]TIME)[^·•]*[·•]\s*(.+?)\s+WON", re.I)


def _norm_status(raw: str) -> str:
    s = raw.strip().upper()
    return {"PENS": "PEN", "PEN": "PEN", "AET": "AET", "FT": "FT"}.get(s, s)


def _unescape(s: str) -> str:
    return html_lib.unescape(s.strip())


def _parse_one_item(chunk: str) -> dict | None:
    """Parse un seul bloc `data-local-match-item ... </a>` en dict ou None.
    Gère deux layouts HTML :
      - Standard : teams dans <div truncate>, goals séparés
      - Featured (ex: "MATCH 96") : teams dans <span sm:inline truncate>, score "X-Y"
    """
    kickoff_m = _KICKOFF_RE.search(chunk)
    id_m      = _HREF_ID_RE.search(chunk)
    status_m  = _STATUS_RE.search(chunk)

    if not all([kickoff_m, id_m, status_m]):
        return None

    status = _norm_status(status_m.group(1))

    # ── Récupération des équipes ──────────────────────────────────────
    teams = [_unescape(t) for t in _TEAM_DIV_RE.findall(chunk)]
    # Featured layout (span au lieu de div pour le nom complet)
    if len(teams) < 2:
        teams = [_unescape(t) for t in _TEAM_SPAN_RE.findall(chunk)]
    teams = [t for t in teams if 1 <= len(t) <= 50 and not t[0].isdigit()]
    if len(teams) < 2:
        return None
    home, away = teams[0], teams[1]

    # ── Récupération du score ──────────────────────────────────────────
    # Layout standard : deux divs séparés "text-right tabular-nums"
    goals = _GOALS_RE.findall(chunk)
    if len(goals) >= 2:
        hg, ag = int(goals[0]), int(goals[1])
    else:
        # Layout featured : score combiné "X-Y" dans un div tabular-nums
        comb = _SCORE_COMB_RE.search(chunk)
        if comb:
            hg, ag = int(comb.group(1)), int(comb.group(2))
        else:
            return None

    # ── Round ──────────────────────────────────────────────────────────
    # Layout standard : <div>Round of 16</div>
    round_str = None
    for candidate in _ROUND_RE.findall(chunk):
        c = candidate.strip()
        if len(c) >= 4 and re.search(r"[A-Za-z]", c) and "match" not in c.lower():
            round_str = c
            break
    # Layout featured : <div class="inline-block ...">Round of 16</div>
    if not round_str:
        fm = _ROUND_FEATURED_RE.search(chunk)
        round_str = fm.group(1).strip() if fm else "Unknown"

    # ── Vainqueur ──────────────────────────────────────────────────────
    plain = _TAG_RE.sub(" ", chunk)
    winner: str | None = None
    if status == "PEN":
        pen = _PEN_RE.search(plain)
        if pen:
            won = _unescape(pen.group(1)).lower()
            winner = "home" if won == home.lower() else "away" if won == away.lower() else None
        # Pour les tirs au but, chercher aussi le score PEN "X-Y PEN"
        if winner is None:
            pen_score = re.search(r'(\d+)-(\d+)\s+PEN', chunk)
            if pen_score:
                ph, pa = int(pen_score.group(1)), int(pen_score.group(2))
                winner = "home" if ph > pa else "away" if pa > ph else None
    elif hg > ag:
        winner = "home"
    elif ag > hg:
        winner = "away"
    else:
        winner = "draw"

    return {
        "fixture_id": int(id_m.group(1)),
        "date":       kickoff_m.group(1),
        "round":      round_str,
        "status":     status,
        "is_finished": status in {"FT", "AET", "PEN"},
        "home_team":  home,
        "away_team":  away,
        "home_goals": hg,
        "away_goals": ag,
        "winner":     winner,
    }


def parse_results(htm: str) -> list[dict]:
    """
    Découpe le HTML en items individuels puis parse chacun indépendamment.
    Split sur le wrapper <div data-local-match-item> pour éviter tout cross-item.
    """
    # Chaque item est un <div data-local-match-item ...>...<a>...</a>...</div>
    # On split sur le tag d'ouverture du wrapper pour isoler chaque item.
    raw_chunks = htm.split("<div data-local-match-item")
    matches: list[dict] = []
    seen_ids: set[int] = set()
    for chunk in raw_chunks[1:]:           # [0] = contenu avant le premier item
        # Tronquer au premier </a> pour ne travailler que sur le bloc de l'item
        # Note : on cherche </a> en FORWARD — si le chunk contient des <a>
        # imbriqués (ex: badge "MATCH 96"), on prend le dernier </a> avant
        # le prochain data-local-match-item.
        end = chunk.rfind("</a>")
        if end != -1:
            chunk = chunk[:end + 4]
        result = _parse_one_item(chunk)
        if result and result["fixture_id"] not in seen_ids:
            matches.append(result)
            seen_ids.add(result["fixture_id"])
    return matches


def fetch_results_list() -> list[dict]:
    """Récupère la liste des matchs terminés récents (page results, ~24 derniers)."""
    htm = _get(RESULTS_URL, "results", RESULTS_TTL)
    return parse_results(htm) if htm else []


# ─────────────────────────────────────────────────────────────
# PARSING — FICHE INDIVIDUELLE D'UN MATCH (score + statut)
# ─────────────────────────────────────────────────────────────
# Utilisé pour scraper les matchs hors des 24 visibles (phase de groupes complète).
_PAGE_TITLE_RE = re.compile(r"<title>([^<]+)</title>")
_PAGE_SCORE_RE = re.compile(r">\s*(\d)\s*-\s*(\d)\s*<")
_PAGE_STATUS_RE = re.compile(
    r'(?:text-slate-500|badge)[^>]*>\s*(FT|AET|Pens?)\s*<', re.I
)
_PAGE_ROUND_RE = re.compile(
    r'(?:ROUND OF \d+|GROUP [A-Z]|QUARTER.FINAL|SEMI.FINAL|FINAL)',
    re.I,
)
_PAGE_DATE_RE  = re.compile(r'datetime="([^"]+)"')
_PAGE_TEAMS_RE = re.compile(r'truncate[^"]*">([^<]+)</div>', re.S)


def parse_match_header(htm: str, fixture_id: int) -> dict | None:
    """
    Extrait depuis la page d'un match individuel :
    home/away team, score, status, round, date.
    Renvoie None si la page ne correspond pas à un match WC2026 terminé.

    Les pages individuelles utilisent le même layout "featured card" que les
    entrées MATCH-96 dans la liste de résultats (équipes dans <span sm:inline
    truncate>, score combiné "X-Y" dans tabular-nums).
    """
    if not htm or "FIFA WORLD CUP" not in htm.upper():
        return None

    # Status (peut être loin dans la page - on cherche sur tout le HTML)
    status_m = re.search(
        r'text-slate-500[^>]*text-center[^>]*>\s*(FT|AET|Pens?)\s*</div>',
        htm, re.S | re.I,
    )
    if not status_m:
        # Essai alternatif : badge simple
        status_m = re.search(r'>\s*(FT|AET|Pens?)\s*</div>', htm[:30000], re.S | re.I)
    if not status_m:
        return None
    status = _norm_status(status_m.group(1))
    if status not in {"FT", "AET", "PEN"}:
        return None

    # Zone de travail : ~3000 chars autour du status pour équipes et score
    pos = status_m.start()
    zone = htm[max(0, pos - 200): pos + 2000]

    # Équipes dans <span ...sm:inline truncate...>TEAM</span>
    teams = [_unescape(t) for t in _TEAM_SPAN_RE.findall(zone)]
    if len(teams) < 2:
        # Fallback : chercher dans une fenêtre plus large
        teams = [_unescape(t) for t in _TEAM_SPAN_RE.findall(htm[:30000])]
    teams = [t for t in teams if 2 <= len(t) <= 50 and not t[0].isdigit()]
    if len(teams) < 2:
        return None
    home, away = teams[0], teams[1]

    # Score de base "X-Y" (temps réglementaire)
    comb = _SCORE_COMB_RE.search(zone)
    if comb:
        hg, ag = int(comb.group(1)), int(comb.group(2))
    else:
        return None

    # Score final (AET ou PEN prend le dessus)
    aet_score = re.search(r'(\d+)-(\d+)\s+AET', zone)
    pen_score  = re.search(r'(\d+)-(\d+)\s+PEN', zone)
    if aet_score:
        hg, ag = int(aet_score.group(1)), int(aet_score.group(2))
    # Pour PEN, on garde le score de règlement (0-0 ou égal)

    # Round
    round_m = _ROUND_FEATURED_RE.search(htm[:30000])
    round_str = round_m.group(1).strip() if round_m else "Unknown"

    # Date
    date_m = _PAGE_DATE_RE.search(htm[:20000])
    date_str = date_m.group(1) if date_m else ""

    # Vainqueur
    winner: str | None = None
    if status == "PEN":
        plain = _TAG_RE.sub(" ", zone + htm[max(0, pos - 2000): pos])
        pen = _PEN_RE.search(plain)
        if pen:
            won = _unescape(pen.group(1)).lower()
            winner = "home" if won == home.lower() else "away" if won == away.lower() else None
        if winner is None and pen_score:
            ph, pa = int(pen_score.group(1)), int(pen_score.group(2))
            winner = "home" if ph > pa else "away" if pa > ph else None
    elif hg > ag:
        winner = "home"
    elif ag > hg:
        winner = "away"
    else:
        winner = "draw"

    return {
        "fixture_id": fixture_id,
        "date":       date_str,
        "round":      round_str,
        "status":     status,
        "is_finished": True,
        "home_team":  home,
        "away_team":  away,
        "home_goals": hg,
        "away_goals": ag,
        "winner":     winner,
    }


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
    htm = _get(MATCH_URL.format(fixture_id), f"match_{fixture_id}", MATCH_TTL)
    out: dict = {"home": {}, "away": {}}
    if not htm:
        return out
    for home_val, label, away_val in _STAT_ROW_RE.findall(htm):
        col = _STAT_MAP.get(label.strip())
        if col and col not in out["home"]:  # 1re occurrence = bloc principal
            out["home"][col] = _to_num(home_val)
            out["away"][col] = _to_num(away_val)
    return out


# ─────────────────────────────────────────────────────────────
# ASSEMBLAGE — 24 DERNIERS MATCHS (résultats page)
# ─────────────────────────────────────────────────────────────
def scrape_played_matches(with_stats: bool = True) -> list[dict]:
    """
    Renvoie les matchs terminés récents, enrichis de leurs statistiques.
    Format identique à src.data_fetch (mêmes clés) pour brancher data_build.
    """
    results = [m for m in fetch_results_list() if m["is_finished"]]
    rows: list[dict] = []
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


# ─────────────────────────────────────────────────────────────
# SCRAPING D'UN SEUL MATCH (pour build_history)
# ─────────────────────────────────────────────────────────────
def scrape_single_match(fixture_id: int) -> dict | None:
    """
    Télécharge la fiche d'un match et renvoie un dict complet (header + stats).
    Renvoie None si le match n'est pas WC2026 terminé.
    """
    htm = _get(MATCH_URL.format(fixture_id), f"match_{fixture_id}", MATCH_TTL)
    header = parse_match_header(htm, fixture_id)
    if header is None:
        return None
    stats = fetch_match_stats(fixture_id)
    row = dict(header)
    for side in ("home", "away"):
        for col, val in stats[side].items():
            row[f"{side}_{col}"] = val
    row["source"] = "TheStatsZone"
    row["is_finished"] = True
    return row


if __name__ == "__main__":
    data = scrape_played_matches()
    print(f"{len(data)} matchs terminés scrappés.")
    if data:
        ex = data[0]
        print(ex["home_team"], ex.get("home_goals"), "-",
              ex.get("away_goals"), ex["away_team"], "|", ex["status"])
        print("possession:", ex.get("home_possession"), "/", ex.get("away_possession"))
        print("tirs:", ex.get("home_shots"), "/", ex.get("away_possession"))
