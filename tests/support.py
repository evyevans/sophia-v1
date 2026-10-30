"""Authored synthetic evidence; no market dataset or real asset."""
import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone

AS_OF = '2026-10-25T00:01:00Z'
KEY = 'demo:1/native:glass'

def seal(source):
    source['content_sha256'] = hashlib.sha256(json.dumps(source['payload'], sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()).hexdigest()
    return source

def snapshot():
    asset = dict(chain_id='demo:1', asset_id='native:glass', symbol='GLASS', decimals=8,
                 representation='native', category='monetary', provider_ids={'demo':'glass'})
    def source(sid, role, payload, publisher=None):
        return seal(dict(id=sid, role=role, publisher=publisher or sid, upstreams=[publisher or sid],
            url='https://' + sid + '.invalid/evidence', observed_at='2026-10-25T00:00:30Z',
            available_at='2026-10-25T00:00:31Z', published_at='2026-10-25T00:00:30Z',
            retrieved_at='2026-10-25T00:00:32Z', verification='synthetic', units='declared in payload',
            coverage='synthetic local scenario', redistribution='synthetic; MIT', method_version='demo-1', payload=payload))
    bars=[]
    start=datetime(2026,9,23,tzinfo=timezone.utc)
    for i in range(32):
        a=start+timedelta(days=i); b=a+timedelta(days=1); c=str(69+i)
        bars.append(dict(open_at=a.isoformat(),close_at=b.isoformat(),available_at=b.isoformat(),
                         complete=True,o=c,h=str(70+i),l=str(68+i),c=c,v='100000'))
    def market(venue):
        return dict(asset_key=KEY, decimals=8, representation='native', venue=venue, instrument='spot', status='online',
            quote=dict(asset_key='fiat:USD',symbol='USD',kind='fiat',usd_rate='1',depeg=False,issuer_risk_reviewed=True),
            bids=[['99.99','1000'],['99.90','1000']], asks=[['100.01','1000'],['100.10','1000']],
            constraints=dict(price_tick='0.01',lot_step='0.00000001',min_notional='1'), bars=copy.deepcopy(bars))
    facts={
      'economics':dict(token_holder_rights='no claim on issuer cash flow',value_capture='native monetary use; no revenue claim',protocol_fees_usd=None,protocol_revenue_usd=None,holder_revenue_usd=None,peg_usd='1',reserve_reviewed=True,redemption_controls='synthetic comparison only'),
      'supply':dict(circulating='1000000',total='1200000',max_supply='2000000',unlocks_30d='0',emissions_30d='10',burn_30d='0',insider_fraction='0.10',treasury_controls='documented consensus',vesting_controls='no private allocation'),
      'security':dict(controls_reviewed=True,active_exploit=False,suspended=False,reorg_alert=False,lifecycle_status='active',upgrade_controls='documented consensus',oracle_dependencies='none',bridge_dependencies='none',sequencer_dependencies='none',finality='documented probabilistic',counterparty_concentration='venue exposure reviewed'),
      'adoption':dict(adjustment_method='exclude known synthetic bot clusters; illustrative only',adjusted_activity='1200',wash_activity_reviewed=True,sybil_reviewed=True),
      'macro':dict(regime='synthetic neutral scenario',quote_custody_reviewed=True,cycle_risks='liquidity can reverse; no prediction')}
    sources=[source('market-a','market',market('demo-a')),source('market-b','market',market('demo-b'))]
    for kind, data in facts.items():
        sources.append(source(kind,'review',dict(asset_key=KEY,lens=kind,assessment='documented',method='authored synthetic checklist v1',facts=data,opposing_evidence=['Synthetic data establishes no real-world quality.'])))
    return dict(schema_version=1,synthetic=True,asset=asset,sources=sources,notes='Synthetic demonstration. Research only.')

def market(s, n=0):
    return s['sources'][n]['payload']

def review(s, name):
    return next(x for x in s['sources'] if x['role']=='review' and x['payload']['lens']==name)

def reseal(s):
    for source in s['sources']: seal(source)
    return s
