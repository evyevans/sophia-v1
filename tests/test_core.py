"""Each mutation catches an unsafe qualification or a false verification claim."""
import copy
import unittest
from support import AS_OF, KEY, snapshot, market, review, reseal

try:
    from sophia.core import evaluate, InputError
except ImportError:
    evaluate = None
    class InputError(ValueError): pass

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(evaluate), 'The crypto evidence evaluator is not implemented.')
        self.s=snapshot()
    def result(self): return evaluate(reseal(self.s), as_of=AS_OF)
    def blocked(self, code):
        r=self.result(); self.assertEqual(r['status'],'BLOCKED'); self.assertIn(code,[g['code'] for g in r['gates']])
    def test_synthetic_qualification_is_never_execution(self):
        r=self.result(); self.assertEqual(r['status'],'QUALIFIED_RESEARCH'); self.assertEqual(r['evidence_status'],'SYNTHETIC')
        self.assertFalse(r['execution_enabled']); self.assertFalse(r['dispatch_enabled']); self.assertEqual(len(r['lenses']),7)
    def test_prices_are_decimal_and_midpoint_is_exact(self):
        market(self.s)['bids'][0][0]='99.98'; r=self.result()
        self.assertEqual(r['markets'][0]['mid_quote'],'99.995')
    def test_float_prices_are_rejected(self):
        market(self.s)['bids'][0][0]=99.99
        with self.assertRaises(InputError): self.result()
    def test_nonfinite_and_huge_decimal_are_rejected(self):
        for bad in ('NaN','Infinity','1e999999','-1','0',True):
            with self.subTest(bad=bad):
                s=snapshot(); market(s)['bids'][0][0]=bad
                with self.assertRaises(InputError): evaluate(reseal(s),as_of=AS_OF)
    def test_chain_collision_does_not_join_on_symbol(self):
        market(self.s,1)['asset_key']='demo:2/native:glass'; self.blocked('ASSET_IDENTITY')
    def test_representation_collision_blocks(self):
        market(self.s,1)['representation']='bridged'; self.blocked('ASSET_IDENTITY')
    def test_decimal_identity_collision_blocks(self):
        market(self.s,1)['decimals']=18; self.blocked('ASSET_IDENTITY')
    def test_same_upstream_is_not_independent(self):
        for s in self.s['sources'][:2]: s['upstreams']=['shared-feed']
        self.blocked('SOURCE_DEPENDENCE')
    def test_overlapping_upstream_sets_are_not_independent(self):
        self.s['sources'][0]['upstreams']=['a','shared']; self.s['sources'][1]['upstreams']=['b','shared']; self.blocked('SOURCE_DEPENDENCE')
    def test_same_publisher_is_not_independent(self):
        self.s['sources'][1]['publisher']='market-a'; self.blocked('SOURCE_DEPENDENCE')
    def test_same_venue_is_not_independent(self):
        market(self.s,1)['venue']='demo-a'; self.blocked('SOURCE_DEPENDENCE')
    def test_absent_prices_block(self):
        self.s['sources']=self.s['sources'][2:]; self.blocked('MISSING_MARKETS')
    def test_stale_price_blocks(self):
        self.s['sources'][0]['observed_at']='2026-10-24T23:00:00Z'; self.blocked('STALE_EVIDENCE')
    def test_future_source_blocks(self):
        self.s['sources'][0]['retrieved_at']='2026-10-25T00:02:00Z'; self.blocked('FUTURE_EVIDENCE')
    def test_out_of_order_availability_blocks(self):
        self.s['sources'][0]['available_at']='2026-10-25T00:00:29Z'; self.blocked('TIME_ORDER')
    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(InputError): evaluate(self.s,as_of='2026-10-25T00:01:00')
    def test_clock_skew_blocks(self):
        self.s['sources'][1]['observed_at']='2026-10-24T23:59:40Z'; self.blocked('CLOCK_SKEW')
    def test_disagreeing_usd_prices_block(self):
        market(self.s,1)['bids']=[['109.99','1000']]; market(self.s,1)['asks']=[['110.01','1000']]; self.blocked('PRICE_DISAGREEMENT')
    def test_missing_constraints_block(self):
        market(self.s)['constraints']={}; self.blocked('MARKET_CONSTRAINTS')
    def test_off_tick_book_blocks(self):
        market(self.s)['bids'][0][0]='99.991'; self.blocked('MARKET_CONSTRAINTS')
    def test_book_depth_required(self):
        market(self.s)['asks']=[]; self.blocked('BOOK_DEPTH')
    def test_far_away_depth_does_not_count(self):
        market(self.s)['bids']=[['99.99','0.01'],['50','1000000']]; self.blocked('BOOK_DEPTH')
    def test_wide_spread_blocks(self):
        market(self.s)['bids']=[['98','1000']]; market(self.s)['asks']=[['102','1000']]; self.blocked('SPREAD')
    def test_crossed_book_blocks(self):
        market(self.s)['bids']=[['100.02','1000']]; self.blocked('BOOK_ORDER')
    def test_unsorted_book_blocks(self):
        market(self.s)['bids'].reverse(); self.blocked('BOOK_ORDER')
    def test_quote_depeg_blocks_even_if_not_flagged(self):
        market(self.s)['quote'].update(kind='stablecoin',symbol='USDX',asset_key='demo:1/erc20:usdx',usd_rate='0.95'); self.blocked('QUOTE_RISK')
    def test_quote_issuer_risk_is_not_ignored(self):
        market(self.s)['quote'].update(kind='stablecoin',symbol='USDX',asset_key='demo:1/erc20:usdx',issuer_risk_reviewed=False); self.blocked('QUOTE_RISK')
    def test_fiat_usd_cannot_hide_a_stablecoin(self):
        market(self.s)['quote']['symbol']='USDT'; self.blocked('QUOTE_IDENTITY')
    def test_incomplete_bar_blocks(self):
        market(self.s)['bars'][-1]['complete']=False; self.blocked('BAR_INCOMPLETE')
    def test_future_bar_blocks(self):
        market(self.s)['bars'][-1]['available_at']='2026-10-26T00:00:00Z'; self.blocked('BAR_TIME')
    def test_out_of_order_bars_block(self):
        market(self.s)['bars'].reverse(); self.blocked('BAR_TIME')
    def test_missing_daily_bar_blocks(self):
        del market(self.s)['bars'][4]; self.blocked('BAR_TIME')
    def test_utc_weekends_are_valid(self): self.assertEqual(self.result()['status'],'QUALIFIED_RESEARCH')
    def test_short_history_abstains(self):
        market(self.s)['bars']=market(self.s)['bars'][-4:]; self.blocked('TECHNICAL_HISTORY')
    def test_security_exploit_veto(self):
        review(self.s,'security')['payload']['facts']['active_exploit']=True; self.blocked('SECURITY_VETO')
    def test_unknown_admin_controls_block(self):
        review(self.s,'security')['payload']['facts']['upgrade_controls']='unknown'; self.blocked('SECURITY_UNKNOWN')
    def test_security_missing_review_blocks(self):
        self.s['sources']=[s for s in self.s['sources'] if s['id']!='security']; self.blocked('REVIEW_MISSING')
    def test_exchange_suspension_blocks(self):
        market(self.s)['status']='suspended'; self.blocked('MARKET_SUSPENDED')
    def test_bot_adjustment_unknown_blocks(self):
        review(self.s,'adoption')['payload']['facts']['sybil_reviewed']=False; self.blocked('ADOPTION_UNKNOWN')
    def test_circulating_supply_cannot_exceed_total(self):
        review(self.s,'supply')['payload']['facts']['circulating']='2000000'; self.blocked('SUPPLY_INVALID')
    def test_holder_revenue_cannot_exceed_protocol_revenue(self):
        self.s['asset']['category']='defi'; f=review(self.s,'economics')['payload']['facts']; f.update(protocol_fees_usd='10',protocol_revenue_usd='5',holder_revenue_usd='8'); self.blocked('ECONOMICS_INVALID')
    def test_unreviewed_high_risk_category_excluded(self):
        self.s['asset']['category']='meme'; self.blocked('CATEGORY_EXCLUDED')
    def test_stablecoins_are_comparison_exposure(self):
        self.s['asset']['category']='stablecoin'; self.assertEqual(self.result()['status'],'COMPARISON_ONLY')
    def test_unknown_critical_assessment_blocks(self):
        review(self.s,'macro')['payload']['assessment']='unknown'; self.blocked('REVIEW_UNKNOWN')
    def test_payload_hash_tamper_blocks(self):
        self.s['sources'][0]['payload']['venue']='other'
        r=evaluate(self.s,as_of=AS_OF); self.assertEqual(r['status'],'BLOCKED'); self.assertIn('CONTENT_HASH',[g['code'] for g in r['gates']])
    def test_real_mode_cannot_relabel_synthetic_sources(self):
        self.s['synthetic']=False; self.blocked('PROVENANCE_LABEL')
    def test_operator_attestation_never_becomes_verification(self):
        self.s['synthetic']=False; self.s['asset']['chain_id']='example:1'
        for s in self.s['sources']:
            s['verification']='operator_attested'; s['url']='https://evidence.example.org/'+s['id']; s['payload']['asset_key']='example:1/native:glass'
        r=self.result(); self.assertEqual(r['evidence_status'],'OPERATOR_ATTESTED'); self.assertFalse(r['independently_verified'])
    def test_claimed_independent_verification_blocks(self):
        self.s['sources'][0]['verification']='independently_verified'; self.blocked('PROVENANCE_LABEL')
    def test_duplicate_source_ids_rejected(self):
        self.s['sources'][1]['id']='market-a'
        with self.assertRaises(InputError): self.result()
    def test_no_snapshot_can_enable_execution(self):
        self.s['execution_enabled']=True
        with self.assertRaises(InputError): self.result()
    def test_repeat_evaluation_is_identical(self):
        self.assertEqual(self.result(),self.result())
    def test_opposing_evidence_preserved(self):
        self.assertIn('Synthetic data establishes no real-world quality.',str(self.result()['lenses']))
    def test_stablecoin_requires_own_peg_and_reserve_review(self):
        self.s['asset']['category']='stablecoin'; review(self.s,'economics')['payload']['facts']['reserve_reviewed']=False
        self.blocked('STABLECOIN_UNKNOWN')
    def test_stablecoin_asset_depeg_blocks(self):
        self.s['asset']['category']='stablecoin'; review(self.s,'economics')['payload']['facts']['peg_usd']='0.95'
        self.blocked('STABLECOIN_DEPEG')
    def test_unresolved_migration_blocks(self):
        review(self.s,'security')['payload']['facts']['lifecycle_status']='migration_pending'; self.blocked('LIFECYCLE_RISK')
    def test_reorganization_alert_blocks(self):
        review(self.s,'security')['payload']['facts']['reorg_alert']=True; self.blocked('SECURITY_VETO')
    def test_unsupported_review_lens_rejected(self):
        review(self.s,'macro')['payload']['lens']='Buffett'
        with self.assertRaises(InputError): self.result()
    def test_non_boolean_market_decimals_rejected_as_identity(self):
        market(self.s)['decimals']=True; self.blocked('ASSET_IDENTITY')
    def test_empty_source_array_is_blocked(self):
        self.s['sources']=[]; self.blocked('MISSING_MARKETS')
    def test_malformed_stablecoin_quote_key_blocks(self):
        for n in (0,1): market(self.s,n)['quote'].update(kind='stablecoin',symbol='USDX',asset_key='/')
        self.blocked('QUOTE_IDENTITY')
    def test_asset_cannot_be_its_own_quote(self):
        market(self.s)['quote'].update(kind='stablecoin',symbol='USDX',asset_key=KEY); self.blocked('QUOTE_IDENTITY')
    def test_invalid_evm_quote_contract_blocks(self):
        market(self.s)['quote'].update(kind='stablecoin',symbol='USDX',asset_key='eip155:1/erc20:fake'); self.blocked('QUOTE_IDENTITY')
    def test_fractional_base_unit_lot_and_quantity_block(self):
        market(self.s)['constraints']['lot_step']='0.000000015'
        for side in ('bids','asks'):
            for row in market(self.s)[side]: row[1]='1000.000000005'
        self.blocked('MARKET_CONSTRAINTS')
    def test_upstream_cannot_name_other_publishers_or_venues(self):
        self.s['sources'][0].update(publisher='venue-a',upstreams=['venue-a-raw-feed'])
        self.s['sources'][1].update(publisher='aggregator-b',upstreams=['venue-a'])
        self.blocked('SOURCE_DEPENDENCE')
    def test_upstream_cannot_hide_other_venue(self):
        self.s['sources'][1]['upstreams']=[' Demo-A ']; self.blocked('SOURCE_DEPENDENCE')
    def test_bar_cannot_be_available_after_its_source_was_retrieved(self):
        market(self.s)['bars'][-1]['available_at']='2026-10-25T00:00:50Z'; self.blocked('BAR_TIME')
    def test_bar_freshness_uses_evaluation_time_not_retrieval(self):
        for source in self.s['sources']:
            for k in ('observed_at','published_at','available_at','retrieved_at'): source[k]='2026-10-25T00:04:01Z'
        for n in (0,1): market(self.s,n)['bars'].pop()
        r=evaluate(reseal(self.s),as_of='2026-10-25T00:06:00Z')
        self.assertEqual(r['status'],'BLOCKED'); self.assertIn('BAR_TIME',[g['code'] for g in r['gates']])

if __name__=='__main__': unittest.main()
