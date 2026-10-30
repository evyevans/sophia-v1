"""Opt-in native BTC/USD public GET collector. No keys, orders or arbitrary URLs."""
from datetime import datetime,timezone,timedelta
from email.utils import parsedate_to_datetime
import hashlib,json
import urllib.request
from .contracts import digest, stamp

KEY='bip122:000000000019d6689c085ae165831e93/native:btc'
URLS={
 'coinbase-meta':'https://api.exchange.coinbase.com/products/BTC-USD',
 'coinbase-bars':'https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400',
 'coinbase-book':'https://api.exchange.coinbase.com/products/BTC-USD/book?level=2',
 'kraken-meta':'https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD',
 'kraken-bars':'https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440',
 'kraken-book':'https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=100'}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('Redirect refused')

def validate_receipts(receipts):
    cutoff=stamp(receipts[-1]['retrieved_at'])
    for receipt in receipts:
        observed,retrieved=stamp(receipt['observed_at']),stamp(receipt['retrieved_at'])
        if not observed<=retrieved<=cutoff or (cutoff-observed).total_seconds()>120:
            raise ValueError('Component timestamp is future, stale or out of order')

def fetch_public(name):
    url=URLS[name]  # Exact allowlist; no supplied URLs or authentication headers.
    request=urllib.request.Request(url,method='GET',headers={'User-Agent':'Floatglass-Research/0.2 public-market-research','Accept':'application/json','Cache-Control':'no-cache'})
    with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(request,timeout=15) as response:
        raw=response.read(4_000_001)
        if len(raw)>4_000_000: raise ValueError('Response too large')
        retrieved=datetime.now(timezone.utc)
        observed=parsedate_to_datetime(response.headers['Date']).astimezone(timezone.utc)
        data=json.loads(raw,parse_float=str)
        if name.startswith('kraken') and data.get('error'): raise ValueError('Provider error')
        return data,dict(endpoint=url,retrieved_at=retrieved.isoformat(),observed_at=observed.isoformat(),
                         raw_sha256=hashlib.sha256(raw).hexdigest(),raw_json=raw.decode(),timestamp_basis='HTTP Date; not an exchange-signed snapshot timestamp')

def normalize(venue,meta,book,rows,retrieved):
    constraints={}
    if venue=='coinbase':
        if meta.get('base_currency')!='BTC' or meta.get('quote_currency')!='USD': raise ValueError('Unexpected product identity')
        status=meta.get('status') if not any(meta.get(k) for k in ('trading_disabled','cancel_only','post_only','limit_only')) else 'restricted'
        for dest,src in [('price_tick','quote_increment'),('lot_step','base_increment'),('min_notional','min_market_funds')]:
            if meta.get(src) is not None: constraints[dest]=str(meta[src])
        candles=[(r[0],r[3],r[2],r[1],r[4],r[5]) for r in rows]
    else:
        if meta.get('base')!='XXBT' or meta.get('quote')!='ZUSD': raise ValueError('Unexpected product identity')
        status='online' if meta.get('status')=='online' else 'restricted'
        if 'tick_size' in meta: constraints['price_tick']=str(meta['tick_size'])
        if 'lot_decimals' in meta: constraints['lot_step']=format(10**(-int(meta['lot_decimals'])),'.'+str(meta['lot_decimals'])+'f')
        if 'costmin' in meta: constraints['min_notional']=str(meta['costmin'])
        candles=[(r[0],r[1],r[2],r[3],r[4],r[6]) for r in rows]
    bars=[]
    for ts,o,h,l,c,v in sorted(candles,key=lambda r:int(r[0])):
        start=datetime.fromtimestamp(int(ts),timezone.utc); end=start+timedelta(days=1)
        if end>retrieved: continue
        bars.append(dict(open_at=start.isoformat(),close_at=end.isoformat(),available_at=retrieved.isoformat(),complete=True,
                         o=str(o),h=str(h),l=str(l),c=str(c),v=str(v)))
    return dict(asset_key=KEY,decimals=8,representation='native',venue=venue,instrument='spot',status=status,
                quote=dict(asset_key='fiat:USD',symbol='USD',kind='fiat',usd_rate='1',depeg=False,issuer_risk_reviewed=False),
                constraints=constraints,bids=[[str(r[0]),str(r[1])] for r in book['bids'][:100]],asks=[[str(r[0]),str(r[1])] for r in book['asks'][:100]],bars=bars[-366:],
                book_coverage='best 100 levels per side; full response retained in capture receipt')

def collect(*,fetch=fetch_public):
    sources=[]; receipts=[]; failures=[]
    for venue in ('coinbase','kraken'):
        try:
            fetched={}
            for kind in ('meta','bars','book'):
                data,receipt=fetch(venue+'-'+kind); receipts.append(receipt); fetched[kind]=(data,receipt)
            components=[fetched[k][1] for k in ('meta','bars','book')]
            validate_receipts(components)
            meta=fetched['meta'][0]; bars=fetched['bars'][0]; book,receipt=fetched['book']
            if venue=='kraken':
                meta=next(iter(meta['result'].values()))
                bars=next(v for k,v in bars['result'].items() if k!='last')
                book=next(iter(book['result'].values()))
            payload=normalize(venue,meta,book,bars,stamp(fetched['bars'][1]['retrieved_at']))
            payload['component_provenance']=[{k:r[k] for k in ('endpoint','observed_at','retrieved_at','raw_sha256') if k in r} for r in components]
            observed=min((r['observed_at'] for r in components),key=stamp); retrieved=receipt['retrieved_at']
            sources.append(dict(id=venue+'-btc-usd',role='market',publisher=venue,upstreams=[venue],
                url=URLS[venue+'-book'].split('?')[0],observed_at=observed,published_at=observed,available_at=observed,retrieved_at=retrieved,
                verification='operator_attested',units='BTC base / USD quote; daily UTC bars',coverage='Native BTC/USD spot only',
                redistribution='Provider market-data terms apply; local research capture only',method_version='public-get-btc-0.2',payload=payload,content_sha256=digest(payload)))
        except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration) as error:
            failures.append(dict(venue=venue,error_type=type(error).__name__,message='Collection failed; no fallback data used.'))
    return dict(schema_version=1,synthetic=False,asset=dict(chain_id=KEY.split('/')[0],asset_id='native:btc',symbol='BTC',decimals=8,
        representation='native',category='monetary',provider_ids={'coinbase':'BTC-USD','kraken':'XXBTZUSD'}),sources=sources,
        notes='Read-only public venue capture. HTTP Date freshness is not signed provenance. Protocol reviews are absent; qualification must remain blocked. USD cash quote convention does not remove venue custody risk.'),receipts,failures
