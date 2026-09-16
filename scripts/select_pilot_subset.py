"""Selects the pilot subset: paretic-side stroke subjects stratified across the 3
Perry (1995) ambulation categories (household / limited-community / full-community),
prioritizing subjects with complete 7-muscle EMG data but deliberately including one
incomplete-EMG case per category where available -- an edge-case check for how the
pipeline/LLM handles missing muscle data (see the "no valid EMG data" branch in
pipeline.to_prompt_text()).

Fixed random seed (42) for reproducibility. Writes data/pilot_subset.json. Re-run
any time to regenerate the same 18-subject list.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.figshare_loader import load_stroke_excel
from src.features.mat_spatiotemporal import build_spatiotemporal_lookup, load_stroke_spatiotemporal
from src.features.spatiotemporal import classify_ambulation

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
N_PER_CATEGORY = 6  # -> 18 total across 3 categories


def main() -> None:
    stroke = load_stroke_excel(str(ROOT / "data" / "raw" / "PostStrokeAdults.xlsx"))
    st_lookup = build_spatiotemporal_lookup(
        load_stroke_spatiotemporal(str(ROOT / "data" / "raw" / "MAT_normalizedData_PostStrokeAdults.mat"))
    )

    paretic_trials = [t for t in stroke if t.side == "P"]
    rows = []
    for t in paretic_trials:
        n_valid_muscles = sum(1 for c in t.emg_norm.values() if not np.isnan(c).all())
        st = st_lookup.get((t.subject_id, "P"))
        if st is None or st["gait_speed_m_s"] is None:
            continue
        speed = st["gait_speed_m_s"]
        rows.append(
            {
                "subject_id": t.subject_id,
                "side": "P",
                "gait_speed_m_s": speed,
                "category": classify_ambulation(speed),
                "n_valid_muscles": n_valid_muscles,
            }
        )

    rng = random.Random(SEED)
    pilot = []
    for cat in [
        "household ambulator (<0.4 m/s)",
        "limited community ambulator (0.4-0.8 m/s)",
        "full community ambulator (>0.8 m/s)",
    ]:
        items = [r for r in rows if r["category"] == cat]
        complete = [r for r in items if r["n_valid_muscles"] == 7]
        incomplete = [r for r in items if r["n_valid_muscles"] < 7]
        rng.shuffle(complete)
        rng.shuffle(incomplete)
        n_complete = N_PER_CATEGORY - 1 if incomplete else N_PER_CATEGORY
        pilot.extend(complete[:n_complete] + incomplete[:1])

    pilot.sort(key=lambda r: r["gait_speed_m_s"])

    out_path = ROOT / "data" / "pilot_subset.json"
    out_path.write_text(json.dumps(pilot, indent=2))
    print(f"Wrote {len(pilot)} subjects to {out_path}")
    for p in pilot:
        print(f"  {p['subject_id']}: {p['gait_speed_m_s']:.2f} m/s, {p['category']}, "
              f"{p['n_valid_muscles']}/7 muscles valid")


if __name__ == "__main__":
    main()
