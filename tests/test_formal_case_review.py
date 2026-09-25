"""Input-boundary checks for new expert requirement candidates."""
from scripts.build_formal_case_review import candidate_items


def visible_input(speed='0.80', index='-0.0', control=False):
    lines=[f'Gait speed: {"not provided" if control else speed+" m/s"}',
           'Composite kinematic deviation score (GPS-like): 5.00',
           'Step length symmetry index: not applicable' if control else
           f'Step length symmetry index: {index}% (step-length definition: successive_footfall)',
           '- AnkleAngles: range of motion 10.0 deg, Gait Variable Score 7.00',
           '- KneeAngles: range of motion 30.0 deg, Gait Variable Score 6.00',
           '- HipAngles: range of motion 20.0 deg, Gait Variable Score 6.00',
           '- PelvisAngles: range of motion 5.0 deg, Gait Variable Score 2.00']
    for m,z,d in [('GAS',8.0,'below'),('RF',8.0,'above'),('VL',3.0,'above'),
                  ('BF',2.0,'below'),('ST',2.0,'above'),('TA',1.0,'above'),('ERS',1.0,'below')]:
        lines.append(f'- {m}: above-threshold interval(s) 0%-100%, 100% of cycle above threshold, max |z| vs healthy reference: {z:.1f} ({d} reference, at 33% of cycle)')
    return '\n'.join(lines)


def test_displayed_reference_boundary_and_negative_zero_are_not_overinterpreted():
    rows={r['item_id']:r for r in candidate_items(visible_input(),'stroke')}
    assert 'within the stated reference speed range' in rows['N01']['draft_statement']
    assert 'rounds to zero' in rows['N06']['draft_statement']
    assert 'paretic step is shorter' not in rows['N06']['draft_statement']


def test_displayed_joint_tie_preserved_and_mean_relative_direction_kept():
    rows={r['item_id']:r for r in candidate_items(visible_input(),'stroke')}
    assert all(j in rows['N02']['draft_statement'] for j in ['Ankle','Knee','Hip'])
    assert 'below the phase-specific reference mean' in rows['N03']['draft_statement']
    assert 'above the phase-specific reference mean' in rows['N04']['draft_statement']
    assert 'clinical severity' in rows['N02']['draft_statement']


def test_controls_do_not_acquire_stroke_speed_or_step_index_requirements():
    user=visible_input(control=True)
    rows=candidate_items(user,'control')
    assert len(rows)==5
    assert 'N06' not in {r['item_id'] for r in rows}
    assert 'GPS-like' in rows[0]['draft_statement']
    assert all(r['expert_decision']=='PENDING' for r in rows)
    assert all(line in user for r in rows for line in r['evidence'].splitlines())
