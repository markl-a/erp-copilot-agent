import pytest
from fastapi.testclient import TestClient

from agent import tools
from agent.api import app
from erp.readonly import QueryRejected, connect, query


@pytest.fixture
def db():
    return connect()


@pytest.mark.parametrize("sql", [
    "select * from part",                              # base table, not a view
    "delete from v_part",
    "select * from v_part; drop table part",
    "update price_list set unit_price = 0",
    "pragma table_info(part)",
    "select * from v_part join customer using(part_no)",
])
def test_guard_rejects(db, sql):
    with pytest.raises(QueryRejected):
        query(db, sql)


def test_guard_allows_views(db):
    assert len(query(db, "select * from v_part")) == 5


@pytest.mark.parametrize("text", ["ipw60r045cp", "IPW60R045 CP", "wk-10231", "WK 10231"])
def test_part_normalization(db, text):
    assert tools.lookup_part(db, text)["part_no"] == "WK-10231"


def test_rfq_to_draft_quote(db):
    rfq = "IPW60R045CP x 1500\nLPC55S69JBD100: 3,000 pcs\nFOO123 x 10\nIPW60R070P6 x 100"
    q = tools.draft_quote(db, rfq, "C002")
    by = {l["mfr_part_no"]: l for l in q["lines"]}
    assert by["IPW60R045CP"]["from_stock"] == 1500 and by["IPW60R045CP"]["short"] == 0
    assert by["LPC55S69JBD100"]["unit_price"] == 4.15              # tier B, qty >= 2500 break
    assert by["LPC55S69JBD100"]["short"] == 2200 and by["LPC55S69JBD100"]["eta_for_short"] == "2026-11-15"
    assert any("FOO123" in n for n in q["notes"])
    assert any("EOL" in n for n in q["notes"])
    assert q["status"] == "draft_pending_sales_approval"


def test_approval_required_and_checked(db):
    q = tools.draft_quote(db, "RTL8211F-CG x 100", "C001")
    assert tools.approve_quote(q["quote_id"], "sales_amy")["status"] == "approved"


def test_pcn_eol_impact(db):
    r = tools.pcn_impact(db, "PCN-2026-118")
    names = [c["customer"] for c in r["affected_customers"]]
    assert names == ["Acme Networks", "Delta Motion"]                # 12-month window excludes the 2025-06 shipment
    assert r["affected_customers"][1]["qty_12m"] == 600
    assert "last-time-buy" in r["action"] and "2026-12-31" in r["notification_drafts"][0]


def test_pcn_informational(db):
    r = tools.pcn_impact(db, "PCN-2026-204")
    assert r["action"] == "notify (informational)" and r["affected_customers"][0]["customer"] == "Nova Medical"


def test_api_openapi_has_connector_operations():
    c = TestClient(app)
    ops = {op["operationId"] for p in c.get("/openapi.json").json()["paths"].values() for op in p.values()}
    assert {"lookupPart", "draftQuote", "pcnImpact"} <= ops
    assert c.get("/parts/rtl8211f-cg").json()["available"] == 4000
