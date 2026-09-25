"""Render a paired-contrast figure from the completed, hash-verified estimates."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT/'data/rating_packets_formal_v1/private/three_rater_model_analysis_v1'
PUBLIC = ROOT/'docs/formal_study/model_comparison_v1'


def main():
    path=PRIVATE/'final_outcomes.json';raw=path.read_bytes()
    record=json.loads((PRIVATE/'ANALYSIS_BUILD_RECORD.json').read_text())
    assert hashlib.sha256(raw).hexdigest()==record['output_sha256'][str(path.relative_to(ROOT))]
    result=json.loads(raw)['estimates']['primary_stroke']
    names={'anthropic':'Claude Opus 5','gemini':'Gemini 3.1 Pro preview','openai':'GPT-6-astra'}
    fig,ax=plt.subplots(figsize=(10,4.4))
    labels=[]
    for y,(contrast,row) in enumerate(result['contrasts'].items()):
        a,b=contrast.split(' - ');labels.append(names[a]+' minus '+names[b])
        wide=row['family_adjusted_98_3333']['interval'];narrow=row['descriptive_95']['interval']
        if wide:ax.plot(wide,[y,y],color='#8393a1',lw=2,zorder=1)
        if narrow:ax.plot(narrow,[y,y],color='#1e5676',lw=6,solid_capstyle='butt',zorder=2)
        ax.scatter(row['mean_difference_percentage_points'],y,color='#102e41',s=48,zorder=3)
    ax.axvline(0,color='#777777',lw=1,linestyle='--')
    ax.set_yticks(range(len(labels)),labels);ax.invert_yaxis()
    ax.set_xlim(-27,29);ax.set_ylim(2.65,-.65)
    ax.set_xlabel('Difference in mean full coverage (percentage points)')
    ax.set_title('Stroke reports: paired coverage contrasts',loc='left',fontweight='bold',pad=16)
    ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    ax.legend(handles=[Line2D([0],[0],color='#1e5676',lw=6,label='Descriptive 95% BCa'),Line2D([0],[0],color='#8393a1',lw=2,label='Family-adjusted 98.3333% BCa')],loc='upper center',bbox_to_anchor=(.5,-.22),ncol=2,frameon=False)
    fig.text(.02,.025,'25 paired participants; 20,000 shared resamples; seed 20260918. Selected internal sample.',fontsize=9,color='#444444')
    fig.subplots_adjust(left=.39,right=.98,top=.84,bottom=.29)
    outputs=[]
    for suffix in ('png','svg'):
        p=PUBLIC/f'Paired_stroke_coverage.{suffix}';assert not p.exists();fig.savefig(p,dpi=300,facecolor='white');outputs.append(p)
    plt.close(fig)
    (PUBLIC/'FIGURE_RECORD.json').write_text(json.dumps({'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(raw).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'output_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}},indent=2)+'\n')
    print('Paired contrast figure exported as PNG and SVG.')


if __name__=='__main__':main()
