# 10-Minute Interview Walkthrough

## Min 0–1: Architecture overview
"I built this over a weekend to ground my prep in something concrete. It's an agentic system that does what an AVP on a GTS desk would do for a new prospect — diagnose the working capital pain point, pick the right product, price it to a 12% RoE hurdle, and produce the deliverables."

Point to README architecture diagram.

## Min 1–3: Run Client 1 (Gulf Coast Refining)

```bash
python -m tfse run clients/gulf_coast_refining.json
```

"The intake captures what you'd get from an exploratory call — AR aging, top obligors, payment terms, working capital gap, banking relationships. The diagnostic agent scores five WC axes and identifies that this client has IG-concentrated receivables and wants off-balance-sheet treatment. That maps directly to non-recourse RF."

## Min 3–5: Show term sheet PDF

Open `outputs/gulf_coast_refining/term_sheet.pdf`

"The structuring agent sets the advance rate based on the obligor rating mix, with a dilution reserve. Non-recourse because the obligors are investment grade. The pricing builds up from the bank's FTP: spread plus fee minus cost of funds minus OpEx minus expected loss. The clearing margin is whatever clears a 12% post-tax RoE hurdle."

## Min 5–7: Open profitability XLSX

Open `outputs/gulf_coast_refining/profitability_model.xlsx`

"Change the drawn balance in B3. Watch the RoE in B24 update. The waterfall is: gross revenue minus cost of funds, minus OpEx, minus expected loss — pre-tax NII, tax it, divide by allocated capital. RWA uses Basel III standardized: EAD times risk weight, where EAD = drawn plus CCF times undrawn. The whole thing is auditable — no black box."

## Min 7–9: Open pitch deck markdown

Open `outputs/gulf_coast_refining/pitch_deck.md`

"This goes into Claude Design for visual polish. The content — diagnostic, solution, economics, terms, next steps — is all agent-generated, grounded in the actual numbers from the pricing model."

## Min 9–10: Compare all three clients

"Same engine, three completely different solutions. Gulf Coast gets RF because the obligors are IG and concentrated and they want off-balance-sheet treatment. Permian Pure gets SCF because they need DPO extension and have strategic OFS suppliers — HSBC underwrites the anchor's credit, not the suppliers' credit. Atlantic Metals gets inventory finance because the borrowing base is full and they have LME-quality copper and aluminum in controlled warehouses. Product selection is a diagnosis problem, not a sales pitch problem."
