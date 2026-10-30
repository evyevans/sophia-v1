import unittest
from datetime import datetime,timezone
try:
    from floatglass.live import collect, normalize, URLS
except ImportError:
    collect=normalize=None; URLS={}

class LiveTests(unittest.TestCase):
    def setUp(self): self.assertTrue(callable(collect),'Read-only collector missing')
    def test_failure_never_substitutes_synthetic(self):
        def fail(_): raise OSError('offline')
        snap,receipts,failures=collect(fetch=fail)
        self.assertFalse(snap['synthetic']); self.assertEqual(snap['sources'],[])
        self.assertEqual(len(failures),2)
    def test_fixed_urls_only_public_market_resources(self):
        self.assertEqual(len(URLS),6)
        self.assertTrue(all(u.startswith(('https://api.exchange.coinbase.com/products/BTC-USD','https://api.kraken.com/0/public/')) for u in URLS.values()))
    def test_coinbase_normalization_retains_exact_strings(self):
        now=datetime(2026,10,30,tzinfo=timezone.utc)
        p=normalize('coinbase',{'base_currency':'BTC','quote_currency':'USD','status':'online','base_increment':'0.00000001','quote_increment':'0.01','min_market_funds':'1'},
                    {'bids':[['100.01','1.23456789',1]],'asks':[['100.02','2',1]]},[],now)
        self.assertEqual(p['bids'],[['100.01','1.23456789']]); self.assertEqual(p['constraints']['lot_step'],'0.00000001')
    def test_wrong_pair_metadata_is_rejected(self):
        with self.assertRaises(ValueError): normalize('coinbase',{'base_currency':'ETH','quote_currency':'USD'}, {},[],datetime.now(timezone.utc))
    def test_current_candle_is_excluded(self):
        now=datetime(2026,10,30,tzinfo=timezone.utc); ts=int(now.timestamp())
        meta={'base_currency':'BTC','quote_currency':'USD','status':'online','base_increment':'0.00000001','quote_increment':'0.01','min_market_funds':'1'}
        p=normalize('coinbase',meta,{'bids':[],'asks':[]},[[ts,1,2,1,2,1],[ts-86400,1,2,1,2,1]],now)
        self.assertEqual(len(p['bars']),1); self.assertEqual(p['bars'][0]['close_at'],now.isoformat())
    def test_large_book_is_explicitly_limited_to_best_100(self):
        meta={'base_currency':'BTC','quote_currency':'USD','status':'online'}
        p=normalize('coinbase',meta,{'bids':[['1','1',1]]*5000,'asks':[['2','1',1]]*5000},[],datetime.now(timezone.utc))
        self.assertEqual(len(p['bids']),100); self.assertEqual(p['book_coverage'],'best 100 levels per side; full response retained in capture receipt')
    def test_unknown_endpoint_rejected_before_network(self):
        from floatglass.live import fetch_public
        from unittest.mock import patch
        with patch('urllib.request.build_opener',side_effect=AssertionError('Network attempted')):
            with self.assertRaises(KeyError): fetch_public('https://untrusted.invalid/')
    def test_redirects_cannot_escape_allowlist(self):
        from floatglass.live import NoRedirect
        with self.assertRaises(ValueError): NoRedirect().redirect_request(None,None,302,'Found',{},'https://untrusted.invalid/')
    def test_two_venue_capture_reaches_research_without_fabricating_reviews(self):
        from support import snapshot, AS_OF
        from floatglass.core import evaluate
        from floatglass.contracts import stamp
        from datetime import timedelta
        bars=snapshot()['sources'][0]['payload']['bars']
        coinbase_rows=[[int(stamp(b['open_at']).timestamp()),b['l'],b['h'],b['o'],b['c'],b['v']] for b in bars]
        kraken_rows=[[int(stamp(b['open_at']).timestamp()),b['o'],b['h'],b['l'],b['c'],'100',b['v'],10] for b in bars]
        meta={'base_currency':'BTC','quote_currency':'USD','status':'online','base_increment':'0.00000001','quote_increment':'0.01','min_market_funds':'1'}
        kmeta={'base':'XXBT','quote':'ZUSD','status':'online','tick_size':'0.01','lot_decimals':8,'costmin':'1'}
        book={'bids':[['99.99','1000',1]],'asks':[['100.01','1000',1]]}
        responses={'coinbase-meta':meta,'coinbase-bars':coinbase_rows,'coinbase-book':book,
                   'kraken-meta':{'result':{'XXBTZUSD':kmeta}},'kraken-bars':{'result':{'XXBTZUSD':kraken_rows,'last':0}},
                   'kraken-book':{'result':{'XXBTZUSD':book}}}
        now=stamp(AS_OF)-timedelta(seconds=10)
        def fake(name): return responses[name],{'retrieved_at':now.isoformat(),'observed_at':now.isoformat()}
        snap,receipts,failures=collect(fetch=fake)
        r=evaluate(snap,as_of=AS_OF)
        self.assertEqual(failures,[]); self.assertEqual(len(receipts),6); self.assertEqual(len(r['markets']),2)
        codes=[g['code'] for g in r['gates']]
        self.assertEqual(codes.count('REVIEW_MISSING'),5)
        self.assertEqual(codes.count('QUOTE_RISK'),2)
        self.assertEqual(r['status'],'BLOCKED'); self.assertFalse(r['synthetic']); self.assertFalse(r['execution_enabled'])
    def test_quote_does_not_invent_custody_review(self):
        meta={'base_currency':'BTC','quote_currency':'USD','status':'online'}
        p=normalize('coinbase',meta,{'bids':[],'asks':[]},[],datetime.now(timezone.utc))
        self.assertFalse(p['quote']['issuer_risk_reviewed'])
    def test_component_receipt_future_or_stale_is_rejected(self):
        from floatglass.live import validate_receipts
        good={'observed_at':'2026-10-30T17:58:40Z','retrieved_at':'2026-10-30T17:58:41Z'}
        for bad in ('2099-01-01T00:00:00Z','2020-01-01T00:00:00Z'):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_receipts([dict(good,observed_at=bad),good])
    def test_malformed_provider_shapes_are_recorded_as_failures(self):
        def malformed(name): return [],{'observed_at':'2026-10-30T17:58:40Z','retrieved_at':'2026-10-30T17:58:41Z'}
        snap,receipts,failures=collect(fetch=malformed)
        self.assertEqual(len(failures),2);self.assertEqual(snap['sources'],[]);self.assertEqual(len(receipts),6)
