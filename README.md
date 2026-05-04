# Trade Finance Structuring Engine (TFSE)

> An agentic Python CLI that ingests a client trade-finance intake and produces a PDF term sheet, XLSX profitability model, Markdown pitch deck, and JSON CRM entry — powered by Claude SDK.

## Elevator Pitch

TFSE does what an AVP on a GTS desk does for a new prospect: diagnose the working-capital pain point, select the right product (RF / SCF / Inventory), structure the facility, price it to a 12% RoE hurdle, and produce client-ready deliverables. Three demo clients across the energy & commodities space — all different products, all different diagnostics.

## Architecture

```
Client JSON → Intake (Haiku) → Diagnostic (Opus) → Structuring (Opus) → Pricing (deterministic) → Pitch (Haiku)
                                                                                    ↓
                                              term_sheet.pdf | profitability_model.xlsx | pitch_deck.md | cme_entry.json
```

## Prerequisites

1. Python 3.11+
2. Add your Anthropic API key to a `.env` file in the project root:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## Install

```bash
pip install -e .
```

## Run

```bash
python -m tfse run clients/gulf_coast_refining.json
python -m tfse run clients/permian_pure_energy.json
python -m tfse run clients/atlantic_metals_trading.json
```

Artifacts land in `outputs/<client_slug>/`:
- `term_sheet.pdf` — 2-page indicative term sheet
- `profitability_model.xlsx` — RoE waterfall with live Excel formulas
- `pitch_deck.md` — structured pitch for Claude Design styling
- `cme_entry.json` — mock CRM deal record

## Run Tests (no API key needed)

```bash
pytest tests/ -v
```

## Three Demo Clients

| Client | Product | Facility | Key Diagnostic |
|---|---|---|---|
| Gulf Coast Refining LLC | Receivables Finance | $250M committed | IG-concentrated AR, off-BS appetite |
| Permian Pure Energy | Supply Chain Finance | $150M uncommitted | DPO extension, critical OFS suppliers |
| Atlantic Metals Trading | Inventory Finance | $100M uncommitted | LME copper/aluminum, full borrowing base |
