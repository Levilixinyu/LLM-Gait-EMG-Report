"""Check released stroke EMG scaling and Excel averaging; no model calls."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import warnings
import h5py
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.features.figshare_loader import load_stroke_excel, EMG_MUSCLES


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify(root):
    mat = root / 'data/raw/MAT_normalizedData_PostStrokeAdults.mat'
    xlsx = root / 'data/raw/PostStrokeAdults.xlsx'
    before = {str(p.relative_to(root)): digest(p) for p in (mat, xlsx)}
    trials = {(t.subject_id, t.side): t for t in load_stroke_excel(str(xlsx))}
    rows = []
    with h5py.File(mat, 'r') as f:
        for i in range(50):
            sid = f'Sub{i+1:02d}'
            for side, field in [('P', 'PsideSegm_PsideData'), ('N', 'NsideSegm_NsideData')]:
                g = f[f['Sub'][field][i, 0]]
                for muscle in EMG_MUSCLES:
                    raw = np.array(g[muscle]['n'])
                    norm = np.array(g[muscle + 'norm']['n'])
                    excel = trials[(sid, side)].emg_norm[muscle]
                    mask = np.isfinite(raw) & np.isfinite(norm) & (np.abs(norm) > 1e-10)
                    row = dict(subject=sid, side=side, muscle=muscle,
                               shape=list(norm.shape), valid_pairs=int(mask.sum()))
                    if not mask.any():
                        row['status'] = 'no_valid_nonzero_pairs'
                        row['excel_all_missing'] = bool(np.isnan(excel).all())
                        rows.append(row)
                        continue
                    denominator = float(np.median(raw[mask] / norm[mask]))
                    residual = float(np.max(np.abs(raw[mask] - denominator * norm[mask])))
                    relative = residual / max(float(np.max(np.abs(raw[mask]))), 1e-15)
                    with warnings.catch_warnings():
                        warnings.simplefilter('ignore', RuntimeWarning)
                        mean = np.nanmean(norm, axis=0)
                        peaks = np.nanmax(norm, axis=1)
                    scale_ok = relative < 1e-10
                    mean_ok = bool(np.allclose(mean, excel, rtol=1e-10, atol=1e-12, equal_nan=True))
                    peak_ok = bool(np.isclose(denominator, np.nanmax(raw), rtol=1e-10, atol=1e-12))
                    row.update(status='pass' if scale_ok and mean_ok and peak_ok else 'fail',
                               denominator=denominator, raw_max=float(np.nanmax(raw)),
                               denominator_matches_side_muscle_max=peak_ok,
                               scale_relative_residual=relative,
                               normalized_max=float(np.nanmax(norm)),
                               finite_stride_peaks=peaks[np.isfinite(peaks)].tolist(),
                               excel_matches_nanmean=mean_ok,
                               excel_max_absolute_error=float(np.nanmax(np.abs(mean-excel))))
                    rows.append(row)
    valid = [x for x in rows if x['valid_pairs']]
    lookup = {(x['subject'], x['muscle'], x['side']): x for x in valid}
    pairs = []
    for subject, muscle, side in lookup:
        if side != 'P' or (subject, muscle, 'N') not in lookup:
            continue
        p = lookup[(subject, muscle, 'P')]['denominator']
        n = lookup[(subject, muscle, 'N')]['denominator']
        pairs.append(dict(subject=subject, muscle=muscle, paretic=p, nonparetic=n,
                          equal=bool(np.isclose(p, n, rtol=1e-10, atol=1e-12))))
    after = {str(p.relative_to(root)): digest(p) for p in (mat, xlsx)}
    assert before == after, 'Source changed during verification'
    return dict(scope='50 stroke participants; same-side segmentation; 7 EMG muscles per side',
                source_sha256=before, script_sha256=digest(Path(__file__)),
                combinations=len(rows), valid_combinations=len(valid),
                unavailable_combinations=len(rows)-len(valid),
                failed_combinations=sum(x['status']=='fail' for x in rows),
                max_scale_relative_residual=max(x['scale_relative_residual'] for x in valid),
                max_excel_absolute_error=max(x['excel_max_absolute_error'] for x in valid),
                bilateral_pairs=len(pairs), distinct_bilateral_denominators=sum(not x['equal'] for x in pairs),
                combinations_with_stride_peaks_below_one=sum(any(p < 1-1e-10 for p in x['finite_stride_peaks']) for x in valid),
                limitations=['Healthy MAT was not checked.', 'Raw acquisition filtering was not reproduced.',
                             'Cross-side segmentation and author preprocessing code were not audited.',
                             'No clinical normality or diagnostic validity is established.'],
                rows=rows, bilateral_denominators=pairs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Refusing to overwrite an existing verification record')
    result = verify(ROOT)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('rows','bilateral_denominators')}, indent=2))
    raise SystemExit(1 if result['failed_combinations'] else 0)
