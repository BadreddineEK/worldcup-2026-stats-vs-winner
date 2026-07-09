"""
src/build_history.py — Peuple le CSV avec TOUS les matchs joués (phase de groupes incluse).

La page /fwc26/matches/results ne montre que les ~24 derniers matchs en HTML
statique (le reste = bouton JS "SHOW MORE"). Pour avoir l'historique complet,
on itère directement les pages de match individuelles sur une plage d'IDs connus.

Usage (une seule fois avant le déploiement, ou pour mettre à jour) :
    python -m src.build_history

Résultat : data/matches_2026.csv mis à jour avec tous les matchs terminés.

Politesse :
  - Délai 0.8s entre chaque nouvelle requête HTTP.
  - Cache 30 jours par fiche (les stats d'un match terminé ne changent plus).
  - ~200 IDs à vérifier ; avec le cache, le 2ème run est quasi-instantané.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

# Assurer que le répertoire racine est dans le path quand on lance en -m
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.data_build import COLUMNS, DATA_DIR, OUTPUT_CSV, _merge_history
from src.scrape_statszone import (
    POLITE_DELAY,
    fetch_match_stats,
    scrape_single_match,
)

# Plage d'IDs à explorer.
# Les matchs CDM 2026 utilisent des IDs autour de 191828 à ~191960.
# Le step n'est pas uniforme (certains IDs sont absents), on essaie tous.
ID_START = 191700
ID_END   = 191960   # à adapter si le tournoi va au-delà des quarts/demis


def _existing_ids(df: pd.DataFrame) -> set[int]:
    if df.empty or "fixture_id" not in df.columns:
        return set()
    return set(df["fixture_id"].dropna().astype(int))


def build_full_history(verbose: bool = True) -> pd.DataFrame:
    """
    Itère les IDs de ID_START à ID_END, scrape chaque match terminé,
    et renvoie un DataFrame complet fusionné avec l'historique existant.
    """
    # Charge l'existant pour n'ajouter que ce qui manque
    existing = pd.read_csv(OUTPUT_CSV) if OUTPUT_CSV.exists() else pd.DataFrame(columns=COLUMNS)
    known_ids = _existing_ids(existing)
    rows_new: list[dict] = []
    skipped = 0
    fetched = 0

    if verbose:
        total = ID_END - ID_START + 1
        print(f"Exploration de {total} IDs ({ID_START}->{ID_END}), "
              f"{len(known_ids)} deja en cache CSV.")

    for fid in range(ID_START, ID_END + 1):
        if fid in known_ids:
            skipped += 1
            continue

        row = scrape_single_match(fid)
        if row:
            rows_new.append(row)
            fetched += 1
            if verbose:
                print(f"  + {row['home_team']} {row['home_goals']}-{row['away_goals']} "
                      f"{row['away_team']} [{row['round']}] (id={fid})")
            time.sleep(POLITE_DELAY)

    if verbose:
        print(f"\nTerminé : {fetched} nouveaux matchs, {skipped} déjà connus, "
              f"{total - fetched - skipped} IDs sans match CDM 2026.")

    if rows_new:
        new_df = pd.DataFrame(rows_new)
        for col in COLUMNS:
            if col not in new_df.columns:
                new_df[col] = pd.NA
        new_df = new_df[COLUMNS]
        combined = _merge_history(new_df) if not existing.empty else new_df
    else:
        combined = existing

    # Enrichit les matchs sans stats (scrape_single_match donne stats via fetch_match_stats)
    # Cas edge : si stats absentes dans CSV existant, on re-tente ici
    if not combined.empty:
        needs_stats = combined[
            combined["home_possession"].isna() &
            combined["status"].isin(["FT", "AET", "PEN"])
        ]
        if verbose and len(needs_stats):
            print(f"\nRecuperation stats manquantes pour {len(needs_stats)} match(s)...")
        for _, row_s in needs_stats.iterrows():
            fid = int(row_s["fixture_id"])
            stats = fetch_match_stats(fid)
            if stats["home"]:
                for side in ("home", "away"):
                    for col, val in stats[side].items():
                        combined.loc[combined["fixture_id"] == fid, f"{side}_{col}"] = val
                if verbose:
                    print(f"  stats ok pour {row_s['home_team']} vs {row_s['away_team']}")
                time.sleep(POLITE_DELAY)

    # Persiste
    if not combined.empty:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        combined.to_csv(OUTPUT_CSV, index=False)
        if verbose:
            print(f"\nCSV mis a jour : {len(combined)} matchs dans {OUTPUT_CSV}")

    return combined


if __name__ == "__main__":
    df = build_full_history(verbose=True)
    if not df.empty:
        from src.analysis import annotate_matches, agreement_summary
        a = annotate_matches(df)
        s = agreement_summary(a)
        print(f"\n== BILAN ==")
        print(f"  Matchs totaux : {s['n_matches']}")
        print(f"  Dominant gagne : {s['pct_dominant_won']} %")
        print(f"  Surprises : {s['n_surprises']}")
