"""Neutral checklists, not personalities, scores, forecasts or security audits."""
from .contracts import decimal, text

REVIEW_LENSES=('economics','supply','security','adoption','macro')

def reviewed_lens(name, payload, category, midpoint_usd):
    """Return (structured lens, gates). Facts are operator assertions."""
    gates=[]
    def block(code, explanation): gates.append(dict(code=code,explanation=explanation))
    if payload is None:
        block('REVIEW_MISSING',f'{name}: a dated source-linked review is required.')
        return dict(id=name,status='UNKNOWN',explanation='Review missing.',sources=[],opposing_evidence=[]),gates
    facts=payload.get('facts',{})
    assessment=payload.get('assessment')
    explanation=payload.get('method','Method missing.')
    if assessment!='documented': block('REVIEW_UNKNOWN',f'{name}: assessment is unknown or adverse.')
    metrics={}
    def known(key):
        v=facts.get(key)
        return isinstance(v,str) and bool(v.strip()) and v.strip().casefold() not in ('unknown','n/a','none known','unreviewed')
    if name=='economics':
        if not all(known(k) for k in ('token_holder_rights','value_capture')): block('ECONOMICS_UNKNOWN','Token-holder rights and value capture must be documented.')
        amounts=[facts.get(k) for k in ('protocol_fees_usd','protocol_revenue_usd','holder_revenue_usd')]
        if all(v is not None for v in amounts):
            fees,revenue,holders=[decimal(v,zero=True) for v in amounts]
            if not holders<=revenue<=fees: block('ECONOMICS_INVALID','Holder revenue cannot exceed protocol revenue or user fees.')
        elif category not in ('monetary','stablecoin'): block('ECONOMICS_UNKNOWN','This category requires separate fees, protocol revenue and holder revenue.')
        metrics={'facts':facts,'caveat':'Protocol TVL, fees, revenue and token-holder distributions are distinct; no claim on treasury is implied.'}
        if category=='stablecoin':
            if facts.get('reserve_reviewed') is not True or not known('redemption_controls') or facts.get('peg_usd') is None:
                block('STABLECOIN_UNKNOWN','A stablecoin needs its own reserve, redemption and peg review; it is comparison exposure only.')
            elif abs(decimal(facts['peg_usd'])-1)>decimal('0.01'):
                block('STABLECOIN_DEPEG','The asset itself has deviated from its stated USD peg.')
    elif name=='supply':
        required=('circulating','total','unlocks_30d','emissions_30d','burn_30d','insider_fraction')
        if any(k not in facts for k in required) or not known('treasury_controls') or not known('vesting_controls'):
            block('SUPPLY_UNKNOWN','Supply, dilution and treasury/vesting controls need explicit evidence.')
        else:
            c,t=[decimal(facts[k]) for k in ('circulating','total')]
            maximum=decimal(facts['max_supply']) if facts.get('max_supply') is not None else None
            unlock,emission,burn,insider=[decimal(facts[k],zero=True) for k in required[2:]]
            if c>t or maximum is not None and t>maximum or insider>1 or unlock>t or burn>t:
                block('SUPPLY_INVALID','Supply totals, ownership fractions or scheduled flows are inconsistent.')
            metrics=dict(circulating=str(c),total=str(t),float_ratio=str(c/t),fdv_usd=str(maximum*midpoint_usd) if maximum is not None and midpoint_usd else None,
                         net_issuance_30d=str(emission-burn),unlocks_30d=str(unlock),insider_fraction=str(insider),facts=facts,
                         caveat='Maximum-supply FDV is hypothetical; unknown maximum supply leaves FDV unavailable. Unlocks do not equal net issuance.')
    elif name=='security':
        if any(facts.get(k) is True for k in ('active_exploit','suspended','reorg_alert')): block('SECURITY_VETO','Active exploit, reorganization alert or suspension vetoes qualification.')
        if facts.get('lifecycle_status')!='active': block('LIFECYCLE_RISK','Migration, redenomination, fork, delisting or unknown lifecycle requires a new reviewed identity snapshot.')
        required=('upgrade_controls','oracle_dependencies','bridge_dependencies','sequencer_dependencies','finality','counterparty_concentration')
        if facts.get('controls_reviewed') is not True or any(not known(k) for k in required) or any(type(facts.get(k)) is not bool for k in ('active_exploit','suspended','reorg_alert')):
            block('SECURITY_UNKNOWN','Critical governance, security, finality or counterparty controls are unknown.')
        metrics={'facts':facts,'caveat':'An operator checklist is not an audit or a guarantee against exploits, reorgs or losses.'}
    elif name=='adoption':
        if not known('adjustment_method') or facts.get('sybil_reviewed') is not True or facts.get('wash_activity_reviewed') is not True or facts.get('adjusted_activity') is None:
            block('ADOPTION_UNKNOWN','Raw addresses/volume are insufficient without a declared bot, Sybil and wash-activity review.')
        else: decimal(facts['adjusted_activity'],zero=True)
        metrics={'facts':facts,'caveat':'The declared adjustment is not independently rerun or validated.'}
    elif name=='macro':
        if not known('regime') or not known('cycle_risks') or facts.get('quote_custody_reviewed') is not True:
            block('MACRO_UNKNOWN','Regime, cycle and quote/custody exposure need explicit review.')
        metrics={'facts':facts,'caveat':'A macro narrative is context, not a timing signal or forecast.'}
    return dict(id=name,status='DOCUMENTED' if not gates else 'UNKNOWN',explanation=explanation,metrics=metrics,
                opposing_evidence=payload.get('opposing_evidence',[])),gates
