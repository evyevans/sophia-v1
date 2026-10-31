"""Pure fail-closed research evaluator. No IO, model calls, orders or dispatch."""
from dataclasses import asdict, dataclass
from datetime import timedelta
from decimal import Decimal, localcontext
from itertools import combinations
from urllib.parse import urlsplit
import ipaddress
import re

from .contracts import InputError, asset_key, bounded_tree, decimal, digest, obj, stamp, text, valid_asset_key
from .lenses import REVIEW_LENSES, reviewed_lens

@dataclass(frozen=True)
class Policy:
    version: str='floatglass-research-0.1'
    market_age_seconds: int=120
    review_age_seconds: int=86400
    source_skew_seconds: int=30
    max_spread_bps: str='50'
    max_price_disagreement_bps: str='100'
    depth_band_bps: str='100'
    minimum_each_side_depth_usd: str='10000'
    daily_bar_grace_seconds: int=300
    minimum_trend_bars: int=30

POLICY=Policy()

def _bars(rows, now, add, *, available_by):
    if not isinstance(rows,list) or not rows: add('TECHNICAL_HISTORY','Closed daily UTC bars are required.'); return None
    previous=None; closes=[]; okay=True
    for row in rows:
        obj(row)
        a,b,available=[stamp(row.get(k)) for k in ('open_at','close_at','available_at')]
        if row.get('complete') is not True: add('BAR_INCOMPLETE','Incomplete candles cannot qualify.'); okay=False
        midnight=lambda t: t.hour==t.minute==t.second==t.microsecond==0
        if b-a!=timedelta(days=1) or not midnight(a) or not midnight(b) or previous is not None and a!=previous or not b<=available<=min(now,available_by):
            add('BAR_TIME','Bars must be consecutive closed UTC days, available at evaluation time.'); okay=False
        o,h,l,c=[decimal(row.get(k)) for k in ('o','h','l','c')]; decimal(row.get('v'),zero=True)
        if not l<=min(o,c)<=max(o,c)<=h: add('BAR_BOUNDS','OHLC bounds are inconsistent.'); okay=False
        closes.append(c); previous=b
    if previous>now or (now-previous).total_seconds()>86400+POLICY.daily_bar_grace_seconds:
        add('BAR_TIME','Latest daily candle is stale or future-dated.'); okay=False
    if len(closes)<POLICY.minimum_trend_bars: add('TECHNICAL_HISTORY','At least 30 consecutive closed daily bars are required.'); return None
    if not okay: return None
    average=sum(closes[-30:])/30
    # Only a regular 365-return daily sample supports this annualization.
    volatility=None
    if len(closes)>=366:
        returns=[b/a-1 for a,b in zip(closes[-366:-1],closes[-365:])]
        mean=sum(returns)/365
        volatility=str((sum((v-mean)**2 for v in returns)/364).sqrt()*Decimal(365).sqrt())
    return dict(last_close=str(closes[-1]),sma30=str(average),trend='above_sma30' if closes[-1]>average else 'at_or_below_sma30',
                annualized_volatility=volatility,annualization='365 regular daily returns only; otherwise unavailable')

def _market(source, asset, key, now, add):
    p=obj(source.get('payload'))
    if p.get('asset_key')!=key or type(p.get('decimals')) is not int or p.get('decimals')!=asset['decimals'] or p.get('representation')!=asset['representation']:
        add('ASSET_IDENTITY','Venue asset identity, representation or decimals do not match the research asset.')
    if p.get('instrument')!='spot': add('INSTRUMENT_EXCLUDED','Only spot instruments are supported.')
    if p.get('status')!='online': add('MARKET_SUSPENDED','The venue/instrument is unavailable or suspended.')
    venue=text(p.get('venue'),64).strip().casefold()
    q=obj(p.get('quote')); rate=decimal(q.get('usd_rate'))
    kind=q.get('kind')
    if kind=='fiat':
        if q.get('asset_key')!='fiat:USD' or q.get('symbol')!='USD' or rate!=1: add('QUOTE_IDENTITY','Only correctly identified USD fiat quotes are supported.')
    elif kind=='stablecoin':
        if not valid_asset_key(q.get('asset_key')) or q.get('asset_key')==key or q.get('symbol') in (None,'USD'):
            add('QUOTE_IDENTITY','Stablecoin quotes require a distinct chain/contract or native identity.')
    else: add('QUOTE_IDENTITY','Unsupported quote identity or currency type.')
    if type(q.get('depeg')) is not bool or q.get('depeg') is True or abs(rate-1)>Decimal('0.01') or q.get('issuer_risk_reviewed') is not True:
        add('QUOTE_RISK','Quote depeg, issuer/custody risk or an unknown quote review blocks qualification.')
    constraints=p.get('constraints'); tick=lot=None
    if not isinstance(constraints,dict) or not all(k in constraints for k in ('price_tick','lot_step','min_notional')):
        add('MARKET_CONSTRAINTS','Venue tick size, lot step and minimum notional are required.')
    else:
        tick,lot,minimum=[decimal(constraints[k]) for k in ('price_tick','lot_step','min_notional')]
        base_unit=Decimal(10)**(-asset['decimals'])
        if lot%base_unit: add('MARKET_CONSTRAINTS','Lot precision must align with the asset base unit.')
    books=[]
    for side in ('bids','asks'):
        rows=p.get(side)
        if not isinstance(rows,list) or not rows: add('BOOK_DEPTH','Both bid and ask depth are required.'); return None
        levels=[]
        for row in rows:
            if not isinstance(row,list) or len(row)!=2: raise InputError('Book levels require price and quantity.')
            price,quantity=decimal(row[0]),decimal(row[1]); levels.append((price,quantity))
            if quantity%(Decimal(10)**(-asset['decimals'])) or tick is not None and (price%tick or quantity%lot): add('MARKET_CONSTRAINTS','Book levels violate the asset base unit or declared price/quantity increments.')
        prices=[v[0] for v in levels]
        if len(set(prices))!=len(prices) or prices!=sorted(prices,reverse=side=='bids'): add('BOOK_ORDER','Book levels must be unique and best-first.')
        books.append(levels)
    bids,asks=books; bid,ask=bids[0][0],asks[0][0]
    if bid>=ask: add('BOOK_ORDER','Crossed or locked books are ineligible.')
    mid=(bid+ask)/2; spread=(ask-bid)/mid*10000
    if spread>decimal(POLICY.max_spread_bps): add('SPREAD','Observed spread exceeds the research policy limit.')
    band=decimal(POLICY.depth_band_bps)/10000
    depths=[sum(price*qty*rate for price,qty in side if abs(price-mid)/mid<=band) for side in books]
    if min(depths)<decimal(POLICY.minimum_each_side_depth_usd): add('BOOK_DEPTH','Insufficient USD-valued depth within 1% of the midpoint on either side.')
    technical=_bars(p.get('bars'),now,add,available_by=stamp(source['retrieved_at']))
    return dict(source_id=source['id'],venue=venue,mid_quote=str(mid),mid_usd=str(mid*rate),spread_bps=str(spread),
                bid_depth_usd=str(depths[0]),ask_depth_usd=str(depths[1]),quote=q,constraints=constraints,technical=technical)

def evaluate(snapshot, *, as_of):
    """Evaluate supplied evidence at an explicit time; hashes prove consistency only."""
    with localcontext() as context:
        context.prec=80
        return _evaluate(snapshot,as_of=as_of)

def _evaluate(snapshot, *, as_of):
    obj(snapshot); bounded_tree(snapshot)
    if set(snapshot)-{'schema_version','synthetic','asset','sources','notes'}: raise InputError('Unknown snapshot field.')
    if type(snapshot.get('schema_version')) is not int or snapshot['schema_version']!=1 or type(snapshot.get('synthetic')) is not bool: raise InputError('Schema version and synthetic flag required.')
    now=stamp(as_of); asset=obj(snapshot.get('asset')); key=asset_key(asset); synthetic=snapshot['synthetic']
    gates=[]
    def add(code,explanation,source_id=None):
        g=dict(code=code,explanation=explanation)
        if source_id is not None: g['source_id']=source_id
        if g not in gates: gates.append(g)
    category=asset.get('category')
    if category not in ('monetary','l1_l2','defi','stablecoin','infrastructure'): add('CATEGORY_EXCLUDED','This asset category is excluded by default.')
    if asset['representation'] in ('bridged','liquid_staked','wrapped'): add('REPRESENTATION_EXCLUDED','Wrapped, bridged and liquid-staked representations require a separate model; excluded in this release.')
    if not synthetic and asset['chain_id'].startswith('demo:'): add('PROVENANCE_LABEL','Demo identity is not real evidence.')
    sources=snapshot.get('sources')
    if not isinstance(sources,list) or len(sources)>40: raise InputError('At most 40 sources are accepted.')
    ids=set(); eligible=[]; evidence=[]
    for source in sources:
        obj(source); sid=text(source.get('id'),64)
        if sid in ids: raise InputError('Duplicate source ID.')
        ids.add(sid); start=len(gates)
        for k in ('publisher','units','coverage','redistribution','method_version'): text(source.get(k),256)
        upstreams=source.get('upstreams')
        if not isinstance(upstreams,list) or not upstreams: raise InputError('Explicit upstream lineage is required.')
        for u in upstreams: text(u,128)
        role=source.get('role')
        if role not in ('market','review'): raise InputError('Unsupported evidence role.')
        label='synthetic' if synthetic else 'operator_attested'
        if source.get('verification')!=label: add('PROVENANCE_LABEL','Source label does not match mode; independent verification cannot be self-declared.',sid)
        url=urlsplit(text(source.get('url'),1000))
        hostname=url.hostname or ''
        try: ipaddress.ip_address(hostname); private_host=True
        except ValueError: private_host=hostname=='localhost' or hostname.endswith(('.localhost','.local'))
        try: port=url.port
        except ValueError: raise InputError('Invalid source URL.') from None
        if url.scheme!='https' or not hostname or url.username or url.password or url.query or url.fragment or port not in (None,443) or private_host:
            raise InputError('Expected a public HTTPS evidence URL without credentials or query.')
        if not synthetic and hostname.endswith(('.invalid','.test')): add('PROVENANCE_LABEL','Synthetic source URL cannot be used as real evidence.',sid)
        payload=obj(source.get('payload'))
        if role=='review' and payload.get('lens') not in REVIEW_LENSES: raise InputError('Unknown research lens.')
        if not re.fullmatch(r'[a-f0-9]{64}',str(source.get('content_sha256',''))) or digest(payload)!=source['content_sha256']:
            add('CONTENT_HASH','Source payload does not match its declared SHA-256.',sid)
        observed,published,available,retrieved=[stamp(source.get(k)) for k in ('observed_at','published_at','available_at','retrieved_at')]
        if any(t>now for t in (observed,published,available,retrieved)): add('FUTURE_EVIDENCE','Evidence includes a timestamp after evaluation time.',sid)
        if not observed<=available<=retrieved or published>available: add('TIME_ORDER','Observation/publication/availability/retrieval order is inconsistent.',sid)
        age_limit=POLICY.market_age_seconds if role=='market' else POLICY.review_age_seconds
        if (now-observed).total_seconds()>age_limit: add('STALE_EVIDENCE','Evidence exceeds the role-specific freshness limit.',sid)
        if payload.get('asset_key')!=key: add('ASSET_IDENTITY','Evidence belongs to a different chain or asset.',sid)
        evidence.append(source)
        if len(gates)==start: eligible.append(source)
    markets=[]; market_sources=[]
    for source in eligible:
        if source['role']=='market':
            start=len(gates)
            m=_market(source,asset,key,now,lambda c,e:add(c,e,source['id']))
            if m: markets.append(m)
            if m and len(gates)==start: market_sources.append(source)
    if len(market_sources)<2: add('MISSING_MARKETS','Two eligible direct spot markets are required.')
    independent=False
    for a,b in combinations(market_sources,2):
        norm=lambda v:v.strip().casefold()
        lineage=lambda s:{norm(s['publisher']),norm(s['payload']['venue'])}|{norm(u) for u in s['upstreams']}
        if not lineage(a)&lineage(b):
            independent=True
    if len(market_sources)>=2 and not independent: add('SOURCE_DEPENDENCE','Declared publisher, venue and upstream lineage must identify at least two disjoint observations.')
    if len(market_sources)>=2:
        times=[stamp(s['observed_at']) for s in market_sources]
        if (max(times)-min(times)).total_seconds()>POLICY.source_skew_seconds: add('CLOCK_SKEW','Price observation skew exceeds 30 seconds.')
    if len(markets)>=2:
        prices=[decimal(m['mid_usd']) for m in markets]
        if (max(prices)-min(prices))/min(prices)*10000>decimal(POLICY.max_price_disagreement_bps): add('PRICE_DISAGREEMENT','USD-valued venue midpoints disagree beyond the policy limit.')
    midpoint=decimal(markets[0]['mid_usd']) if markets else None
    lenses=[]
    for name in REVIEW_LENSES:
        matches=[s for s in eligible if s['role']=='review' and s['payload'].get('lens')==name]
        if len(matches)>1: add('REVIEW_AMBIGUOUS',f'{name}: reconcile conflicting or duplicate reviews explicitly.')
        payload=matches[0]['payload'] if len(matches)==1 else None
        if payload:
            obj(payload.get('facts')); text(payload.get('method'))
            opposing=payload.get('opposing_evidence')
            if not isinstance(opposing,list): raise InputError('Opposing evidence must be an array.')
            for item in opposing: text(item)
        lens,failures=reviewed_lens(name,payload,category,midpoint)
        lens['sources']=[s['id'] for s in matches]
        for failure in failures: add(**failure)
        lenses.append(lens)
    lenses.append(dict(id='market_structure',status='DOCUMENTED' if len(market_sources)>=2 and independent else 'UNKNOWN',sources=[s['id'] for s in market_sources],
                       explanation='Spread, near-midpoint depth, constraints and declared independent venues; no executable fill is simulated.'))
    lenses.append(dict(id='technical',status='DOCUMENTED' if markets and all(m['technical'] for m in markets) else 'UNKNOWN',sources=[m['source_id'] for m in markets],
                       explanation='30-day moving average on consecutive UTC bars; trend is context, not a buy/sell rule.'))
    status='BLOCKED' if gates else 'COMPARISON_ONLY' if category=='stablecoin' else 'QUALIFIED_RESEARCH'
    return dict(version='0.2.0',mode='RESEARCH_ONLY',status=status,synthetic=synthetic,evidence_status='SYNTHETIC' if synthetic else 'OPERATOR_ATTESTED',
                independently_verified=False,execution_enabled=False,dispatch_enabled=False,as_of=now.isoformat(),asset=asset,asset_key=key,
                input_sha256=digest(snapshot),policy_sha256=digest(asdict(POLICY)),policy=asdict(POLICY),gates=gates,markets=markets,lenses=lenses,evidence=evidence,
                notes=snapshot.get('notes',''),limitations=['Qualification only means supplied evidence passed these checks.','Operator facts, identity mapping and source lineage are not independently authenticated.',
                    'No ledger, hypothetical fills, backtest, benchmark returns, portfolio advice, orders, wallet, model calls or dispatch.','Hashes prove payload consistency, not truth or source authorship.'])
