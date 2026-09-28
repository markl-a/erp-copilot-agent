"""HTTP API with an OpenAPI spec, so the same tools can be registered as a Copilot Studio custom connector /
Power Automate action or called by any agent runtime. Writes stay as drafts until a human approves."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from erp.readonly import QueryRejected, connect
from . import tools

app = FastAPI(title="erp-copilot-tools", version="0.1.0")
DB = connect()


class RFQ(BaseModel):
    cust_id: str
    text: str


@app.get("/parts/{text}", operation_id="lookupPart", summary="Find a part by internal or manufacturer part number")
def part(text: str):
    p = tools.lookup_part(DB, text)
    if not p:
        raise HTTPException(404, "part not found")
    return {**p, **tools.availability(DB, p["part_no"])}


@app.post("/quotes/draft", operation_id="draftQuote", summary="Draft a quote from an RFQ (requires sales approval)")
def draft(rfq: RFQ):
    return tools.draft_quote(DB, rfq.text, rfq.cust_id)


@app.get("/pcn/{pcn_id}/impact", operation_id="pcnImpact", summary="Customers affected by a PCN/EOL and draft notices")
def pcn(pcn_id: str):
    try:
        return tools.pcn_impact(DB, pcn_id)
    except KeyError:
        raise HTTPException(404, "unknown PCN")
