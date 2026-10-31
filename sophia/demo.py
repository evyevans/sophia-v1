"""Three fixed synthetic scenarios. Never used as fallback for supplied evidence."""
import copy
from pathlib import Path
from .contracts import load_json
from .core import evaluate

AS_OF='2026-10-25T00:01:00Z'

def scenarios():
    base=load_json(Path(__file__).resolve().parents[1]/'examples'/'synthetic.json')
    stale=copy.deepcopy(base)
    stale['sources'][0]['observed_at']='2026-10-24T22:00:00Z'
    stale['notes']='Missing/stale evidence: a venue observation is too old.'
    veto=copy.deepcopy(base)
    from .contracts import digest
    security=next(s for s in veto['sources'] if s['id']=='security')
    security['payload']['facts']['active_exploit']=True
    security['content_sha256']=digest(security['payload'])
    veto['notes']='Crypto risk veto: an operator-reported active exploit blocks qualification.'
    return [base,stale,veto]

def run_demo():
    return [evaluate(s,as_of=AS_OF) for s in scenarios()]
