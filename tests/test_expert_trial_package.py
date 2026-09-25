"""Checks for the draft cards' information and provenance boundaries."""
import hashlib
from pathlib import Path
import numpy as np
import pytest
from scripts.build_expert_trial_package import verified_bytes, reference_for, checklist, build
from src.features.data_types import NormalizedTrialData
from src.features.pipeline import extract_summary_from_normalized


def control(name, offset):
    return NormalizedTrialData(name, 'control', 'avg',
                               {'AnkleAngles':np.linspace(offset,offset+20,101)},
                               {'TA':np.linspace(.1+offset*.01,.8,101)})


def test_modified_audit_cache_is_rejected(tmp_path):
    p=tmp_path/'cache.json';p.write_bytes(b'original')
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    assert verified_bytes(tmp_path,'cache.json',h)==b'original'
    p.write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash mismatch'):
        verified_bytes(tmp_path,'cache.json',h)


def test_healthy_reference_excludes_self_but_stroke_same_id_does_not():
    controls=[control('Sub49',9),control('C02',2),control('C03',3)]
    members,norm=reference_for(controls[0],controls)
    assert [c.subject_id for c in members]==['C02','C03']
    np.testing.assert_allclose(norm['joint_angles']['AnkleAngles'],np.linspace(2.5,22.5,101))
    assert norm['meta']['excluded_subjects']==['Sub49']
    stroke=NormalizedTrialData('Sub49','stroke','P',controls[0].joint_angles,controls[0].emg_norm)
    members,norm=reference_for(stroke,controls)
    assert len(members)==3 and norm['meta']['excluded_subjects']==[]


def test_missing_emg_gets_scope_limit_not_zero_activity():
    controls=[control('C01',1),control('C02',2)]
    trial=NormalizedTrialData('Sub47','stroke','P',{'AnkleAngles':np.linspace(2,22,101)},
                              {'TA':np.full(101,np.nan)})
    _,norm=reference_for(trial,controls)
    summary=extract_summary_from_normalized(trial,norm)
    items=checklist(summary)
    assert all(x['expert_decision']=='PENDING' for x in items)
    assert any('missing EMG must not be described as no muscle activity' in x['draft_statement'] for x in items)
    assert not any('.intervals' in x['evidence'] for x in items)


def test_existing_expert_edits_are_not_overwritten(tmp_path):
    out=tmp_path/'cards';out.mkdir();p=out/'expert.csv';p.write_text('reviewer edits')
    with pytest.raises(FileExistsError):build(tmp_path,out,cached=True)
    assert p.read_text()=='reviewer edits'
