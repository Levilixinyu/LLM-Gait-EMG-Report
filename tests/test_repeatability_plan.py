from collections import Counter
from copy import deepcopy
import pytest
from scripts.prepare_repeatability_supplement import create_tasks, digest, make_schedule, PROVIDERS


def original_fixture():
    return {'tasks':[{'case_id':f'stroke_Sub{i:02d}_P','provider':p,'group':'stroke',
            'slot_id':f'old_{i}_{p}','system_prompt':'system','user_prompt':f'input {i}',
            'input_pair_sha256':digest(['system',f'input {i}']),
            'model':p+'-fixture','parameters':{'cap':16000}}
        for i in range(1,26) for p in PROVIDERS]}


def test_balanced_complete_repeats_without_historical_id_collisions():
    old=original_fixture();saved=deepcopy(old)
    rows=create_tasks(old)
    assert old==saved
    assert len(rows)==225
    assert len({r['slot_id'] for r in rows})==225
    assert not {r['slot_id'] for r in rows}&{r['slot_id'] for r in old['tasks']}
    for i in range(1,26):
        case=f'stroke_Sub{i:02d}_P'
        for p in PROVIDERS:
            block=[r for r in rows if r['case_id']==case and r['provider']==p]
            assert {r['repeat'] for r in block}=={1,2,3}
            assert {r['provider_position_within_case'] for r in block}=={1,2,3}
    assert Counter(r['repeat'] for r in rows)=={1:75,2:75,3:75}
    for p in PROVIDERS:
        assert Counter(r['provider_position_within_case'] for r in rows if r['provider']==p)=={1:25,2:25,3:25}
    rows[0]['parameters']['cap']=1
    assert old==saved


def test_schedule_does_not_depend_on_input_order():
    cases=[f'stroke_Sub{i:02d}_P' for i in range(1,26)]
    assert make_schedule(cases)==make_schedule(list(reversed(cases)))


@pytest.mark.parametrize('problem',['missing','duplicate','altered_input'])
def test_rejects_invalid_historical_roster_or_input(problem):
    old=original_fixture()
    if problem=='missing':old['tasks'].pop()
    elif problem=='duplicate':old['tasks'][0]=deepcopy(old['tasks'][1])
    else:old['tasks'][0]['user_prompt']='changed'
    with pytest.raises(ValueError):create_tasks(old)


def test_no_extra_case_or_partial_roster():
    with pytest.raises(ValueError):make_schedule([f'case{i}' for i in range(24)])
    with pytest.raises(ValueError):make_schedule(['same']*25)
