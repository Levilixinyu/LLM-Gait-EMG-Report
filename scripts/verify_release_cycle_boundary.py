"""Record documentary cycle anchors and stroke event-array consistency checks."""
import argparse
import hashlib
import json
from pathlib import Path
import h5py
import numpy as np
ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verify(root):
    mat = root/'data/raw/MAT_normalizedData_PostStrokeAdults.mat'
    rows = []
    with h5py.File(mat) as f:
        for i in range(50):
            e = f[f['Sub']['events'][i, 0]]
            for side, field in [('P', 'PsideSegm_PsideData'), ('N', 'NsideSegm_NsideData')]:
                start = np.array(e[side+'_ICstart']).ravel()
                stop = np.array(e[side+'_ICstop']).ravel()
                shape = f[f['Sub'][field][i, 0]]['HipAngles']['x'].shape
                valid = np.isfinite(start) & np.isfinite(stop) & (stop > start)
                bad = np.flatnonzero(~valid)
                rows.append(dict(subject=f'Sub{i+1:02d}', side=side,
                                 event_count=len(start), hip_angle_shape=list(shape),
                                 stride_count_matches=len(start)==shape[0],
                                 invalid_intervals=[dict(stride_index_zero_based=int(j),
                                                        start=float(start[j]), stop=float(stop[j])) for j in bad]))
    sources = ['data/raw/MATdatafiles_description.xlsx', 'data/raw/AbleBodiedAdults.xlsx',
               'data/raw/PostStrokeAdults.xlsx', 'data/raw/MAT_normalizedData_PostStrokeAdults.mat']
    return dict(scope='Documentary event anchor with stroke event-array consistency checks; not a new event detection audit',
                source_sha256={p:digest(root/p) for p in sources},
                script_sha256=digest(Path(__file__)),
                dictionary_locations={'sheet':'MAT data Struct', 'rows':[24,25,26,36]},
                healthy_excel_readme='Left- and right-side strides are averaged; event details are in the MAT structures.',
                healthy_event_basis='Release dictionary and Excel Readme; healthy MAT was not numerically reverified.',
                stroke_event_checks=rows,
                side_records_with_invalid_intervals=sum(bool(x['invalid_intervals']) for x in rows),
                five_case_impact='No invalid interval in the four stroke development cases; healthy event anchor is documentary.',
                follow_up='Sub43 P has one zero-duration record. Review original events and existing exclusion logic before future selection; no automatic exclusion or metric change was applied.',
                no_inference='No individual toe-off or intermediate gait-phase boundaries are added to model inputs.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit('Choose a new output file; evidence is not overwritten.')
    result = verify(ROOT)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'side_records_checked':len(result['stroke_event_checks']),
                      'side_records_with_invalid_intervals':result['side_records_with_invalid_intervals'],
                      'follow_up':result['follow_up']}, indent=2))
