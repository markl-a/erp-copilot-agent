# erp-copilot-agent

**Copilot tools for an electronic-component distributor: RFQ → draft quote, PCN/EOL → affected customers and draft notices — over read-only ERP views, with a human approval step before anything leaves the building.**

Portfolio demo (Sept 2026). SQLite stands in for Oracle; 16 tests run offline.

```
Sales / FAE ──► Copilot Studio · Power Automate · any agent runtime
                       │  OpenAPI (operationId: lookupPart · draftQuote · pcnImpact)
                       ▼
                 erp-copilot-tools (FastAPI)
                       │  SELECT only · v_* views only · row cap
                       ▼
                 ERP read-only views  (v_part · v_price · v_available · v_inbound · v_customer_parts · v_pcn · v_customer)
```

## What it does

| Flow | Output | Human step |
|---|---|---|
| **RFQ → quote draft** | Parses free-text RFQ lines, normalises part numbers (`ipw60r045cp`, `WK 10231`…), picks the customer's price tier and quantity break, splits stock vs shortage, finds the inbound ETA that covers the shortage, flags EOL parts and unknown part numbers | Sales approves; a quote with an unpriced line cannot be approved |
| **PCN / EOL impact** | Customers who bought the affected part in the last 12 months (by quantity), replacement part with stock, last-time-buy date, one draft notice per customer | FAE reviews drafts before sending |
| **Part lookup** | Internal ↔ manufacturer part number, availability and inbound | — |

## Guardrails live in code, not in the prompt

- The AI layer can reach **only the `v_*` views** — base tables are rejected (`erp/readonly.py`). On Oracle this is a read-only user with `SELECT` on the views only.
- **One `SELECT` statement**, no DDL/DML, no `PRAGMA`/`ATTACH`, row cap on every query.
- Views are the **data-minimisation contract**: the copilot sees what a quote needs, not the whole ERP.
- **Writes are drafts.** Nothing is sent to a customer or written back to the ERP without a named approver.

## Run

```bash
pip install -r requirements.txt
pytest -q
uvicorn agent.api:app --port 8000     # OpenAPI at /docs → import as a Copilot Studio custom connector / Power Automate action
```

## How this plugs into M365 Copilot

Copilot Studio agent → **Action** from this OpenAPI spec (custom connector) for quotes and PCN impact; **Knowledge** from SharePoint for datasheets and PCN PDFs (see the companion repo **component-kb-rag** for the retrieval side). Business units build the conversation in Copilot Studio; the ERP access, guardrails and tests stay here.

## Not done here

Oracle connection (`oracledb`) · auth (Entra ID) on the API · LLM-based RFQ parsing for messy e-mails (the rule parser is the contract/test baseline) · currency conversion.
