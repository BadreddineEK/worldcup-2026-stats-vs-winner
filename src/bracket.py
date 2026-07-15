"""
src/bracket.py — Visualisation du bracket tournoi CDM 2026 + historique.

Modes :
  - vainqueurs reels (vert)
  - vainqueur simule selon stats dominantes (orange = surprise)

Support des editions 2026 (live) et 2022, 2018, 2014 (historique).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

BOX_W  = 5.0
TEAM_H = 0.50

_Y = {
    "r16_0a": 17.0, "r16_0b": 14.0, "qf_0": 15.5,
    "r16_1a": 11.0, "r16_1b":  8.0, "qf_1":  9.5,
    "sf_top": 12.5,
    "r16_2a":  5.0, "r16_2b":  2.0, "qf_2":  3.5,
    "r16_3a": -1.0, "r16_3b": -4.0, "qf_3": -2.5,
    "sf_bot":  0.5,
    "final":   6.5,
}
_X = {"r16": 0.0, "qf": 6.5, "sf": 13.0, "final": 19.5}


def _match(fid, rnd, ht, at, hg, ag, winner, status="FT"):
    return {"fixture_id": fid, "round": rnd, "home_team": ht, "away_team": at,
            "home_goals": hg, "away_goals": ag, "winner": winner, "status": status}


HISTORICAL_BRACKETS = {
    2022: pd.DataFrame([
        _match(-2201, "Round of 16", "Netherlands", "USA",         3, 1, "home"),
        _match(-2202, "Round of 16", "Argentina",   "Australia",   2, 1, "home"),
        _match(-2203, "Round of 16", "France",      "Poland",      3, 1, "home"),
        _match(-2204, "Round of 16", "England",     "Senegal",     3, 0, "home"),
        _match(-2205, "Round of 16", "Japan",       "Croatia",     1, 1, "away", "PEN"),
        _match(-2206, "Round of 16", "Brazil",      "South Korea", 4, 1, "home"),
        _match(-2207, "Round of 16", "Morocco",     "Spain",       0, 0, "home", "PEN"),
        _match(-2208, "Round of 16", "Portugal",    "Switzerland", 6, 1, "home"),
        _match(-2209, "Quarter-finals", "Netherlands", "Argentina",  2, 2, "away", "PEN"),
        _match(-2210, "Quarter-finals", "Croatia",     "Brazil",     1, 1, "home", "PEN"),
        _match(-2211, "Quarter-finals", "Morocco",     "Portugal",   1, 0, "home"),
        _match(-2212, "Quarter-finals", "England",     "France",     1, 2, "away"),
        _match(-2213, "Semi-finals",    "Argentina",   "Croatia",    3, 0, "home"),
        _match(-2214, "Semi-finals",    "France",      "Morocco",    2, 0, "home"),
        _match(-2215, "Final",          "Argentina",   "France",     3, 3, "home", "PEN"),
    ]),
    2018: pd.DataFrame([
        _match(-1801, "Round of 16", "France",    "Argentina",   4, 3, "home"),
        _match(-1802, "Round of 16", "Uruguay",   "Portugal",    2, 1, "home"),
        _match(-1803, "Round of 16", "Spain",     "Russia",      1, 1, "away", "PEN"),
        _match(-1804, "Round of 16", "Croatia",   "Denmark",     1, 1, "home", "PEN"),
        _match(-1805, "Round of 16", "Brazil",    "Mexico",      2, 0, "home"),
        _match(-1806, "Round of 16", "Belgium",   "Japan",       3, 2, "home"),
        _match(-1807, "Round of 16", "Sweden",    "Switzerland", 1, 0, "home"),
        _match(-1808, "Round of 16", "Colombia",  "England",     1, 1, "away", "PEN"),
        _match(-1809, "Quarter-finals", "Uruguay",  "France",    0, 2, "away"),
        _match(-1810, "Quarter-finals", "Brazil",   "Belgium",   1, 2, "away"),
        _match(-1811, "Quarter-finals", "Sweden",   "England",   0, 2, "away"),
        _match(-1812, "Quarter-finals", "Russia",   "Croatia",   2, 2, "away", "PEN"),
        _match(-1813, "Semi-finals",    "France",   "Belgium",   1, 0, "home"),
        _match(-1814, "Semi-finals",    "Croatia",  "England",   2, 1, "home"),
        _match(-1815, "Final",          "France",   "Croatia",   4, 2, "home"),
    ]),
    2014: pd.DataFrame([
        _match(-1401, "Round of 16", "Brazil",      "Chile",       1, 1, "home", "PEN"),
        _match(-1402, "Round of 16", "Colombia",    "Uruguay",     2, 0, "home"),
        _match(-1403, "Round of 16", "France",      "Nigeria",     2, 0, "home"),
        _match(-1404, "Round of 16", "Germany",     "Algeria",     2, 1, "home", "AET"),
        _match(-1405, "Round of 16", "Argentina",   "Switzerland", 1, 0, "home", "AET"),
        _match(-1406, "Round of 16", "Belgium",     "USA",         2, 1, "home", "AET"),
        _match(-1407, "Round of 16", "Netherlands", "Mexico",      2, 1, "home"),
        _match(-1408, "Round of 16", "Costa Rica",  "Greece",      1, 1, "home", "PEN"),
        _match(-1409, "Quarter-finals", "France",      "Germany",    0, 1, "away"),
        _match(-1410, "Quarter-finals", "Brazil",      "Colombia",   2, 1, "home"),
        _match(-1411, "Quarter-finals", "Argentina",   "Belgium",    1, 0, "home"),
        _match(-1412, "Quarter-finals", "Netherlands", "Costa Rica", 0, 0, "home", "PEN"),
        _match(-1413, "Semi-finals",    "Germany",    "Brazil",     7, 1, "home"),
        _match(-1414, "Semi-finals",    "Netherlands","Argentina",  0, 0, "away", "PEN"),
        _match(-1415, "Final",          "Germany",   "Argentina",  1, 0, "home", "AET"),
    ]),
}

BRACKET_STRUCTURES = {
    2026: {
        "r16": {"r16_0a": 191920, "r16_0b": 191928, "r16_1a": 191932, "r16_1b": 191924,
                "r16_2a": 191922, "r16_2b": 191934, "r16_3a": 191930, "r16_3b": 191926},
        "qf":  {"qf_0": 191940, "qf_1": 191942, "qf_2": 191936, "qf_3": 191938},
        "sf":  {"sf_top": 191946, "sf_bot": None},
        "final": {"final": None},
    },
    2022: {
        "r16": {"r16_0a": -2201, "r16_0b": -2206, "r16_1a": -2203, "r16_1b": -2204,
                "r16_2a": -2202, "r16_2b": -2208, "r16_3a": -2205, "r16_3b": -2207},
        "qf":  {"qf_0": -2210, "qf_1": -2212, "qf_2": -2209, "qf_3": -2211},
        "sf":  {"sf_top": -2213, "sf_bot": -2214},
        "final": {"final": -2215},
    },
    2018: {
        "r16": {"r16_0a": -1801, "r16_0b": -1805, "r16_1a": -1807, "r16_1b": -1808,
                "r16_2a": -1802, "r16_2b": -1806, "r16_3a": -1803, "r16_3b": -1804},
        "qf":  {"qf_0": -1810, "qf_1": -1811, "qf_2": -1809, "qf_3": -1812},
        "sf":  {"sf_top": -1813, "sf_bot": -1814},
        "final": {"final": -1815},
    },
    2014: {
        "r16": {"r16_0a": -1401, "r16_0b": -1402, "r16_1a": -1403, "r16_1b": -1404,
                "r16_2a": -1405, "r16_2b": -1406, "r16_3a": -1407, "r16_3b": -1408},
        "qf":  {"qf_0": -1410, "qf_1": -1409, "qf_2": -1411, "qf_3": -1412},
        "sf":  {"sf_top": -1413, "sf_bot": -1414},
        "final": {"final": -1415},
    },
}


def _team_colors(is_winner, is_surprise):
    if is_surprise:
        return "#f39c12", "rgba(243,156,18,0.12)"
    if is_winner:
        return "#00B140", "rgba(0,177,64,0.12)"
    return "#6b7280", "rgba(22,27,34,0.5)"


def _add_match(fig, x, y_center, team_home, score_home, team_away, score_away,
               winner, status="FT", is_upcoming=False, simulated_winner=None):
    y_top = y_center + TEAM_H + 0.12
    y_bot = y_center - TEAM_H - 0.12

    for team, score, y_team, side_key in [
        (team_home, score_home, y_top, "home"),
        (team_away, score_away, y_bot, "away"),
    ]:
        is_actual_winner = (winner == side_key) and not is_upcoming
        is_sim_surprise  = (simulated_winner == side_key and simulated_winner != winner
                            and not is_upcoming and simulated_winner is not None)
        txt_col, fill_col = _team_colors(is_actual_winner, is_sim_surprise)

        fig.add_shape(
            type="rect", x0=x, x1=x + BOX_W,
            y0=y_team - TEAM_H + 0.06, y1=y_team + TEAM_H - 0.06,
            fillcolor=fill_col,
            line=dict(color="#00B140" if is_actual_winner else "#f39c12" if is_sim_surprise else "#374151",
                      width=1.5 if (is_actual_winner or is_sim_surprise) else 0.8),
            layer="below",
        )
        short  = (team[:13] + ".") if team and len(team) > 14 else (team or "TBD")
        prefix = "T " if is_actual_winner else "S " if is_sim_surprise else ""
        fig.add_annotation(x=x + 0.22, y=y_team, text=f"{prefix}{short}",
                           xanchor="left", yanchor="middle",
                           font=dict(size=9.5, color=txt_col, family="Arial"), showarrow=False)
        sc = "?" if (is_upcoming or score is None or (isinstance(score, float) and score != score)) else f"<b>{int(score)}</b>"
        fig.add_annotation(x=x + BOX_W - 0.18, y=y_team, text=sc,
                           xanchor="right", yanchor="middle",
                           font=dict(size=11, color="#e6edf3" if is_actual_winner else "#9ca3af"), showarrow=False)

    fig.add_shape(type="line", x0=x + 0.12, x1=x + BOX_W - 0.12,
                  y0=y_center, y1=y_center, line=dict(color="#374151", width=0.5))

    if not is_upcoming and status and status not in ("FT", ""):
        fig.add_annotation(x=x + BOX_W / 2, y=y_center + 0.02,
                           text=f'<span style="font-size:8px;color:#9ca3af"> {status} </span>',
                           showarrow=False, bgcolor="rgba(55,65,81,0.7)")
    if is_upcoming:
        fig.add_annotation(x=x + BOX_W / 2, y=y_center + 0.02,
                           text='<span style="font-size:8px;color:#f39c12"> A venir </span>',
                           showarrow=False, bgcolor="rgba(55,65,81,0.8)")


def _connector(fig, x0, y0, x1, y1):
    xm = (x0 + x1) / 2
    fig.add_shape(type="path", path=f"M {x0} {y0} H {xm} V {y1} H {x1}",
                  line=dict(color="#4b5563", width=1.0))


def build_bracket_figure(df: pd.DataFrame, year: int = 2026,
                         simulated_winners: dict | None = None) -> go.Figure:
    """Construit le figure Plotly du bracket eliminatoire."""
    df_src = HISTORICAL_BRACKETS.get(year, df) if year != 2026 else df
    structure = BRACKET_STRUCTURES.get(year, BRACKET_STRUCTURES[2026])
    all_m = df_src.set_index("fixture_id") if "fixture_id" in df_src.columns else pd.DataFrame()
    sim = simulated_winners or {}

    fig = go.Figure()

    def get_m(fid):
        if fid is not None and fid in all_m.index:
            return all_m.loc[fid].to_dict(), False
        return {"home_team": "TBD", "away_team": "TBD", "home_goals": None,
                "away_goals": None, "winner": None, "status": ""}, True

    def add(x_key, y_key, fid):
        m, tbd = get_m(fid)
        _add_match(fig, _X[x_key], _Y[y_key],
                   m["home_team"], m.get("home_goals"),
                   m["away_team"], m.get("away_goals"),
                   m.get("winner"), m.get("status", ""),
                   is_upcoming=tbd, simulated_winner=sim.get(fid))

    for key, fid in structure["r16"].items():
        add("r16", key, fid)
    for key, fid in structure["qf"].items():
        add("qf", key, fid)
    for key, fid in structure["sf"].items():
        if fid is not None:
            add("sf", key, fid)
        else:
            _add_match(fig, _X["sf"], _Y[key], "TBD", None, "TBD", None,
                       None, "", is_upcoming=True)
    fin_fid = structure["final"].get("final")
    if fin_fid is not None:
        add("final", "final", fin_fid)
    else:
        sf_top_m, _ = get_m(structure["sf"].get("sf_top"))
        sf_bot_m, _ = get_m(structure["sf"].get("sf_bot"))
        def winner_of(m):
            w = m.get("winner")
            return m.get("home_team", "TBD") if w == "home" else m.get("away_team", "TBD")
        ft = winner_of(sf_top_m)
        fb = winner_of(sf_bot_m)
        _add_match(fig, _X["final"], _Y["final"], ft, None, fb, None, None, "", is_upcoming=True)

    rx = _X["r16"] + BOX_W; qx = _X["qf"]
    for (a, b), q in [(("r16_0a","r16_0b"),"qf_0"),(("r16_1a","r16_1b"),"qf_1"),
                      (("r16_2a","r16_2b"),"qf_2"),(("r16_3a","r16_3b"),"qf_3")]:
        _connector(fig, rx, _Y[a] + TEAM_H, qx, _Y[q] + TEAM_H)
        _connector(fig, rx, _Y[b] - TEAM_H, qx, _Y[q] - TEAM_H)

    qqx = _X["qf"] + BOX_W; sfx = _X["sf"]
    _connector(fig, qqx, _Y["qf_0"] + TEAM_H, sfx, _Y["sf_top"] + TEAM_H)
    _connector(fig, qqx, _Y["qf_1"] - TEAM_H, sfx, _Y["sf_top"] - TEAM_H)
    _connector(fig, qqx, _Y["qf_2"] + TEAM_H, sfx, _Y["sf_bot"] + TEAM_H)
    _connector(fig, qqx, _Y["qf_3"] - TEAM_H, sfx, _Y["sf_bot"] - TEAM_H)

    ssx = _X["sf"] + BOX_W; fx = _X["final"]
    _connector(fig, ssx, _Y["sf_top"] + TEAM_H, fx, _Y["final"] + TEAM_H)
    _connector(fig, ssx, _Y["sf_bot"] - TEAM_H, fx, _Y["final"] - TEAM_H)

    y_max = max(_Y.values()) + 1.8
    y_min = min(_Y.values()) - 2.2
    for label, x_key in [("1/16 de finale","r16"),("Quarts","qf"),("Demi-finales","sf"),("Finale","final")]:
        fig.add_annotation(x=_X[x_key] + BOX_W/2, y=y_max, text=f"<b>{label}</b>",
                           showarrow=False, font=dict(size=12, color="#e6edf3"))

    if simulated_winners:
        fig.add_annotation(x=0, y=y_min + 0.6,
            text='T = vainqueur reel  |  S = simule selon stats (orange = surprise)',
            xanchor="left", showarrow=False, font=dict(size=9, color="#9ca3af"))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[-0.5, _X["final"] + BOX_W + 0.5]),
        yaxis=dict(visible=False, range=[y_min, y_max + 0.5]),
        height=700, margin=dict(t=40, b=20, l=10, r=10), showlegend=False,
    )
    return fig


def compute_simulated_winners(df: pd.DataFrame) -> dict:
    """Determine le vainqueur simule (dominant stats) pour chaque match."""
    from src.analysis import annotate_matches
    annotated = annotate_matches(df)
    sim = {}
    for _, r in annotated.iterrows():
        dom = r.get("dominant_side")
        if dom in ("home", "away"):
            sim[int(r["fixture_id"])] = dom
    return sim
