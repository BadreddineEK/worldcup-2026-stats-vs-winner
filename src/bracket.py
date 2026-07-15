"""
src/bracket.py — Visualisation du bracket tournoi CDM 2026 en Plotly.

Genere un arbre arborescent R16 → QF → SF → Finale avec :
- Boites par match (vainqueur colore en vert)
- Lignes de connexion entre les tours
- Support TBD pour les matchs pas encore joues
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


# ─────────────────────────────────────────────────────────────
# STRUCTURE DU BRACKET CDM 2026
# ─────────────────────────────────────────────────────────────
# Mapping fixture_id → position dans le bracket (pair, side)
# pair = 0..3 (4 QF matchups), side = 'top' | 'bot'
# Ordre de lecture: top-half d'abord (France/Spain), bot-half ensuite (Eng/Arg)

R16_BRACKET_MAP = {
    191920: ('France-Paraguay',    0, 'top_a'),   # → feeds QF France-Morocco (top)
    191928: ('Morocco-Canada',     0, 'top_b'),
    191932: ('Spain-Portugal',     1, 'top_a'),   # → feeds QF Spain-Belgium (top)
    191924: ('Belgium-USA',        1, 'top_b'),
    191922: ('Brazil-Norway',      2, 'bot_a'),   # → feeds QF Norway-England (bot)
    191934: ('Mexico-England',     2, 'bot_b'),
    191930: ('Argentina-Egypt',    3, 'bot_a'),   # → feeds QF Argentina-Switzerland (bot)
    191926: ('Switzerland-Colombia', 3, 'bot_b'),
}

# Y-coordinates pour chaque case (center of match box)
# Bracket layout: 16 unites de haut, symetrique
_Y = {
    # Top half
    'r16_0a': 15.0, 'r16_0b': 13.0, 'qf_0': 14.0,
    'r16_1a': 11.0, 'r16_1b':  9.0, 'qf_1': 10.0,
    'sf_top': 12.0,
    # Bot half
    'r16_2a':  7.0, 'r16_2b':  5.0, 'qf_2':  6.0,
    'r16_3a':  3.0, 'r16_3b':  1.0, 'qf_3':  2.0,
    'sf_bot':  4.0,
    # Final
    'final':   8.0,
}

# X-coordinates des colonnes
_X = {'r16': 0.0, 'qf': 5.5, 'sf': 11.0, 'final': 16.5}
BOX_W = 5.0    # largeur d une boite
TEAM_H = 0.65  # demi-hauteur d un slot equipe


def _team_color(is_winner: bool) -> tuple[str, str]:
    """Retourne (text_color, fill_color)."""
    if is_winner:
        return '#00B140', 'rgba(0,177,64,0.12)'
    return '#6b7280', 'rgba(22,27,34,0.6)'


def _add_match(
    fig: go.Figure,
    x: float,
    y_center: float,
    team_home: str,
    score_home,
    team_away: str,
    score_away,
    winner: str,
    status: str = 'FT',
    is_upcoming: bool = False,
) -> None:
    """Ajoute une boite match au figure Plotly."""

    y_top = y_center + TEAM_H + 0.1
    y_bot = y_center - TEAM_H - 0.1

    for team, score, y_team, side_key in [
        (team_home, score_home, y_top, 'home'),
        (team_away, score_away, y_bot, 'away'),
    ]:
        is_winner = (winner == side_key) and not is_upcoming
        txt_col, fill_col = _team_color(is_winner)

        # Rectangle
        fig.add_shape(
            type='rect',
            x0=x, x1=x + BOX_W,
            y0=y_team - TEAM_H + 0.05,
            y1=y_team + TEAM_H - 0.05,
            fillcolor=fill_col,
            line=dict(color='#00B140' if is_winner else '#374151', width=1.5),
            layer='below',
        )

        # Nom equipe
        short = team[:14] if team and len(team) > 14 else (team or 'TBD')
        prefix = '' if not is_winner else '🏆 '
        fig.add_annotation(
            x=x + 0.25, y=y_team,
            text=f'{prefix}{short}',
            xanchor='left', yanchor='middle',
            font=dict(size=10, color=txt_col, family='Arial'),
            showarrow=False,
        )

        # Score
        if is_upcoming or score is None or (isinstance(score, float) and score != score):
            sc_text = '?'
        else:
            sc_text = f'<b>{int(score)}</b>'
        fig.add_annotation(
            x=x + BOX_W - 0.2, y=y_team,
            text=sc_text,
            xanchor='right', yanchor='middle',
            font=dict(size=11, color='#e6edf3' if is_winner else '#9ca3af'),
            showarrow=False,
        )

    # Separateur milieu
    fig.add_shape(
        type='line',
        x0=x + 0.15, x1=x + BOX_W - 0.15,
        y0=y_center, y1=y_center,
        line=dict(color='#374151', width=0.6),
    )

    # Badge status (si pas FT)
    if status and status not in ('FT', '') and not is_upcoming:
        fig.add_annotation(
            x=x + BOX_W / 2, y=y_center,
            text=f'<span style="font-size:8px;color:#9ca3af">  {status}  </span>',
            showarrow=False, bgcolor='rgba(55,65,81,0.8)',
        )
    if is_upcoming:
        fig.add_annotation(
            x=x + BOX_W / 2, y=y_center,
            text='<span style="font-size:9px;color:#f39c12">  À venir  </span>',
            showarrow=False, bgcolor='rgba(55,65,81,0.8)',
        )


def _connector(fig: go.Figure, x0: float, y0: float, x1: float, y1: float) -> None:
    """Trace une ligne de connexion coudee entre deux boites."""
    xm = (x0 + x1) / 2
    fig.add_shape(
        type='path',
        path=f'M {x0} {y0} H {xm} V {y1} H {x1}',
        line=dict(color='#374151', width=1.2),
    )


def build_bracket_figure(df: pd.DataFrame) -> go.Figure:
    """
    Construit le figure Plotly du bracket eliminatoire CDM 2026.
    Gere automatiquement les matchs joues et TBD.
    """
    fig = go.Figure()

    # Extraire les matchs par tour
    r16 = df[df['round'] == 'Round of 16'].set_index('fixture_id')
    qf = df[df['round'] == 'Quarter-finals'].set_index('fixture_id')
    sf = df[df['round'] == 'Semi-finals'].set_index('fixture_id')
    final_df = df[df['round'] == 'Final']

    def get_match(df_round, fid=None, condition=None):
        """Recupere un match par fid ou retourne un dict TBD."""
        if fid is not None and fid in df_round.index:
            r = df_round.loc[fid]
            return r.to_dict(), False
        return {'home_team': 'TBD', 'away_team': 'TBD',
                'home_goals': None, 'away_goals': None,
                'winner': None, 'status': ''}, True

    def add(x_key, y_key, fid=None, df_round=None, ht=None, at=None):
        """Helper pour ajouter un match a partir de la structure."""
        if fid is not None and df_round is not None:
            m, tbd = get_match(df_round, fid)
        elif ht is not None:
            m = {'home_team': ht, 'away_team': at,
                 'home_goals': None, 'away_goals': None,
                 'winner': None, 'status': ''}
            tbd = True
        else:
            return
        _add_match(
            fig, _X[x_key], _Y[y_key],
            m['home_team'], m['home_goals'],
            m['away_team'], m['away_goals'],
            m.get('winner'), m.get('status', ''),
            is_upcoming=tbd,
        )

    # ── R16 matchs ──────────────────────────────────────────
    add('r16', 'r16_0a', 191920, r16)  # France-Paraguay
    add('r16', 'r16_0b', 191928, r16)  # Morocco-Canada
    add('r16', 'r16_1a', 191932, r16)  # Spain-Portugal
    add('r16', 'r16_1b', 191924, r16)  # Belgium-USA
    add('r16', 'r16_2a', 191922, r16)  # Brazil-Norway
    add('r16', 'r16_2b', 191934, r16)  # Mexico-England
    add('r16', 'r16_3a', 191930, r16)  # Argentina-Egypt
    add('r16', 'r16_3b', 191926, r16)  # Switzerland-Colombia

    # ── QF matchs ──────────────────────────────────────────
    add('qf', 'qf_0', 191940, qf)  # France-Morocco
    add('qf', 'qf_1', 191942, qf)  # Spain-Belgium
    add('qf', 'qf_2', 191936, qf)  # Norway-England
    add('qf', 'qf_3', 191938, qf)  # Argentina-Switzerland

    # ── SF matchs ──────────────────────────────────────────
    # SF top (France-Spain)
    add('sf', 'sf_top', 191946, sf)
    # SF bot (TBD: England-Argentina)
    add('sf', 'sf_bot', ht='England', at='Argentina')

    # ── Finale ──────────────────────────────────────────────
    if not final_df.empty:
        add('final', 'final', final_df.iloc[0]['fixture_id'], final_df.set_index('fixture_id'))
    else:
        add('final', 'final', ht='Spain', at='TBD')

    # ── Connecteurs R16 → QF ───────────────────────────────
    rx = _X['r16'] + BOX_W
    qx = _X['qf']
    _connector(fig, rx, _Y['r16_0a'] + TEAM_H*0.5, qx, _Y['qf_0'] + TEAM_H)
    _connector(fig, rx, _Y['r16_0b'] - TEAM_H*0.5, qx, _Y['qf_0'] - TEAM_H)
    _connector(fig, rx, _Y['r16_1a'] + TEAM_H*0.5, qx, _Y['qf_1'] + TEAM_H)
    _connector(fig, rx, _Y['r16_1b'] - TEAM_H*0.5, qx, _Y['qf_1'] - TEAM_H)
    _connector(fig, rx, _Y['r16_2a'] + TEAM_H*0.5, qx, _Y['qf_2'] + TEAM_H)
    _connector(fig, rx, _Y['r16_2b'] - TEAM_H*0.5, qx, _Y['qf_2'] - TEAM_H)
    _connector(fig, rx, _Y['r16_3a'] + TEAM_H*0.5, qx, _Y['qf_3'] + TEAM_H)
    _connector(fig, rx, _Y['r16_3b'] - TEAM_H*0.5, qx, _Y['qf_3'] - TEAM_H)

    # ── Connecteurs QF → SF ────────────────────────────────
    qqx = _X['qf'] + BOX_W
    sfx = _X['sf']
    _connector(fig, qqx, _Y['qf_0'] + TEAM_H, sfx, _Y['sf_top'] + TEAM_H)
    _connector(fig, qqx, _Y['qf_1'] - TEAM_H, sfx, _Y['sf_top'] - TEAM_H)
    _connector(fig, qqx, _Y['qf_2'] + TEAM_H, sfx, _Y['sf_bot'] + TEAM_H)
    _connector(fig, qqx, _Y['qf_3'] - TEAM_H, sfx, _Y['sf_bot'] - TEAM_H)

    # ── Connecteurs SF → Finale ────────────────────────────
    ssx = _X['sf'] + BOX_W
    fx = _X['final']
    _connector(fig, ssx, _Y['sf_top'] + TEAM_H, fx, _Y['final'] + TEAM_H)
    _connector(fig, ssx, _Y['sf_bot'] - TEAM_H, fx, _Y['final'] - TEAM_H)

    # ── Labels des rounds ──────────────────────────────────
    for label, x_key in [
        ('1/16 de finale', 'r16'), ('Quarts', 'qf'),
        ('Demi-finales', 'sf'), ('Finale', 'final'),
    ]:
        fig.add_annotation(
            x=_X[x_key] + BOX_W / 2, y=16.5,
            text=f'<b>{label}</b>',
            showarrow=False,
            font=dict(size=12, color='#e6edf3'),
        )

    # ── Layout ────────────────────────────────────────────
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(14,17,23,1)',
        xaxis=dict(visible=False, range=[-0.5, _X['final'] + BOX_W + 0.5]),
        yaxis=dict(visible=False, range=[-0.2, 17.5]),
        height=680,
        margin=dict(t=40, b=10, l=10, r=10),
        showlegend=False,
    )

    return fig
