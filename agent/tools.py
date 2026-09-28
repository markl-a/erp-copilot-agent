"""Business tools for a distributor sales/FAE copilot. Each tool is a small, testable function over the read-only views."""
from __future__ import annotations

import re
import uuid
from datetime import date

from erp.readonly import query

_PN = re.compile(r"[^A-Z0-9]")


def normalize(pn: str) -> str:
    """Customers write part numbers in many ways: 'ipw60r045cp', 'IPW60R045 CP', 'WK 10231'."""
    return _PN.sub("", pn.upper())


def lookup_part(db, text: str) -> dict | None:
    key = normalize(text)
    for p in query(db, "select * from v_part"):
        if key in (normalize(p["part_no"]), normalize(p["mfr_part_no"])):
            return p
    return None


def availability(db, part_no: str) -> dict:
    avail = query(db, "select available from v_available where part_no = ?", (part_no,))
    inbound = query(db, "select eta, qty from v_inbound where part_no = ? order by eta", (part_no,))
    return {"available": avail[0]["available"] if avail else 0, "inbound": inbound}


def unit_price(db, part_no: str, tier: str, qty: int) -> dict | None:
    rows = query(db, "select min_qty, unit_price, currency from v_price where part_no = ? and tier = ? and min_qty <= ? "
                     "order by min_qty desc limit 1", (part_no, tier, qty))
    return rows[0] if rows else None


RFQ_LINE = re.compile(r"(?P<pn>[A-Za-z0-9][A-Za-z0-9 \-]{4,24}?)\s*[x×*:,\s]\s*(?P<qty>[\d,]+)\s*(?:pcs|ea|k)?", re.I)


def parse_rfq(text: str) -> list[dict]:
    """Rule-based RFQ line parser (an LLM can replace this; the downstream contract stays the same)."""
    out = []
    for line in text.splitlines():
        m = RFQ_LINE.search(line.strip())
        if m:
            qty = int(m.group("qty").replace(",", ""))
            if line.lower().rstrip().endswith("k"):
                qty *= 1000
            out.append({"requested": m.group("pn").strip(), "qty": qty})
    return out


QUOTES: dict[str, dict] = {}


def draft_quote(db, rfq_text: str, cust_id: str) -> dict:
    cust = query(db, "select tier from v_customer where cust_id = ?", (cust_id,))
    tier = cust[0]["tier"] if cust else "B"   # unknown customer -> list price tier
    lines, notes = [], []
    for item in parse_rfq(rfq_text):
        part = lookup_part(db, item["requested"])
        if not part:
            notes.append(f"'{item['requested']}' not found — needs FAE review")
            continue
        price = unit_price(db, part["part_no"], tier, item["qty"])
        stock = availability(db, part["part_no"])
        short = max(0, item["qty"] - stock["available"])
        line = {"part_no": part["part_no"], "mfr_part_no": part["mfr_part_no"], "qty": item["qty"],
                "unit_price": price["unit_price"] if price else None, "currency": price["currency"] if price else None,
                "from_stock": min(item["qty"], stock["available"]), "short": short,
                "eta_for_short": next((i["eta"] for i in stock["inbound"] if i["qty"] >= short), None) if short else None,
                "lifecycle": part["lifecycle"]}
        if part["lifecycle"] != "active":
            notes.append(f"{part['mfr_part_no']} is {part['lifecycle']}: check PCN before quoting")
        if short and not line["eta_for_short"]:
            notes.append(f"{part['mfr_part_no']}: {short} pcs short with no inbound covering it — confirm lead time with vendor")
        lines.append(line)
    qid = f"Q-{uuid.uuid4().hex[:8]}"
    quote = {"quote_id": qid, "cust_id": cust_id, "tier": tier, "lines": lines, "notes": notes,
             "status": "draft_pending_sales_approval", "created": date.today().isoformat()}
    QUOTES[qid] = quote
    return quote


def approve_quote(qid: str, approver: str) -> dict:
    q = QUOTES[qid]
    if any(l["unit_price"] is None for l in q["lines"]):
        raise ValueError("cannot approve: a line has no price")
    q.update(status="approved", approver=approver)
    return q


def pcn_impact(db, pcn_id: str) -> dict:
    pcn = query(db, "select * from v_pcn where pcn_id = ?", (pcn_id,))
    if not pcn:
        raise KeyError(pcn_id)
    pcn = pcn[0]
    part = lookup_part(db, pcn["mfr_part_no"])
    customers = query(db, "select customer, cust_id, qty_12m, last_ship from v_customer_parts where part_no = ? order by qty_12m desc",
                      (part["part_no"],)) if part else []
    repl = lookup_part(db, pcn["replacement"]) if pcn["replacement"] else None
    repl_stock = availability(db, repl["part_no"]) if repl else None
    action = "notify + propose replacement + last-time-buy" if pcn["change_type"] == "EOL" else "notify (informational)"
    drafts = [f"Dear {c['customer']}, per {pcn_id} ({pcn['change_type']}, effective {pcn['effective']}) {pcn['mfr_part_no']} is affected. "
              f"You purchased {c['qty_12m']} pcs in the last 12 months."
              + (f" Last-time-buy date: {pcn['last_time_buy']}. Suggested replacement: {pcn['replacement']} ({repl_stock['available']} pcs in stock)." if repl else "")
              for c in customers]
    return {"pcn": pcn, "affected_customers": customers, "action": action, "replacement_stock": repl_stock,
            "notification_drafts": drafts, "status": "drafts_pending_FAE_review"}
