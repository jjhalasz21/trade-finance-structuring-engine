# TFSE Architecture

## Pipeline

```
clients/*.json
    └─► Intake Agent (Haiku)        validate + normalize → ClientProfile
    └─► Diagnostic Agent (Opus)     score 5 WC axes, pick product → DiagnosticReport
    └─► Structuring Agent (Opus)    set term-sheet params → Structure
    └─► Pricing Agent (deterministic) RoE waterfall, margin iteration → Economics
    └─► Pitch Agent (Haiku)         write client narrative → str (markdown)
    └─► Output Generators
            term_sheet.pdf          reportlab
            profitability_model.xlsx  openpyxl (live Excel formulas)
            pitch_deck.md           markdown for Claude Design
            cme_entry.json          mock CRM payload
```

## Finance Modules (deterministic, no LLM)

- `rwa.py` — Basel III EAD = drawn + CCF × (limit − drawn); capital = RWA × 12%
- `roe.py` — gross revenue − CoF − OpEx − EL → pre-tax NII → tax → post-tax RoE
- `advance_rate.py` — weighted-average by obligor rating (RF); blended by commodity (inventory)
- `dilution.py` — rolling dilution rate × 2× multiplier
- `pricing_buildup.py` — iterates margin in 5bps steps until RoE ≥ 12% hurdle
