"""Run the exact authorized repeated-generation supplement; never the original batch."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.llm.repeatability_batch_v2 import PACKAGE,LIVE_ROOT,run


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--live',action='store_true');args=p.parse_args()
    if not args.live:p.error('Use explicit --live for the separately authorized 150-slot amendment')
    read=lambda name:json.loads((PACKAGE/name).read_text())
    result=run(LIVE_ROOT,read('EXECUTION_PLAN.json'),mode='live',authorization=read('EXECUTION_AUTHORIZATION.json'),
               progress=lambda row:print(json.dumps(row),flush=True))
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
