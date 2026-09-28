-- Minimal distributor ERP. In production these would be Oracle EBS tables; the agent only ever sees the views.
CREATE TABLE part (part_no TEXT PRIMARY KEY, mfr TEXT, mfr_part_no TEXT, description TEXT, lifecycle TEXT);
CREATE TABLE customer (cust_id TEXT PRIMARY KEY, name TEXT, tier TEXT);
CREATE TABLE price_list (part_no TEXT, tier TEXT, min_qty INT, unit_price REAL, currency TEXT, valid_to TEXT);
CREATE TABLE inventory (part_no TEXT, warehouse TEXT, on_hand INT, allocated INT);
CREATE TABLE inbound (part_no TEXT, eta TEXT, qty INT);
CREATE TABLE shipment (ship_id TEXT, cust_id TEXT, part_no TEXT, qty INT, ship_date TEXT);
CREATE TABLE pcn (pcn_id TEXT, mfr_part_no TEXT, change_type TEXT, effective TEXT, last_time_buy TEXT, replacement TEXT, summary TEXT);

-- Read-only views: the contract between the AI layer and the ERP. Column choice = data minimisation.
CREATE VIEW v_customer AS SELECT cust_id, name, tier FROM customer;
CREATE VIEW v_part AS SELECT part_no, mfr, mfr_part_no, description, lifecycle FROM part;
CREATE VIEW v_available AS
  SELECT i.part_no, SUM(i.on_hand - i.allocated) AS available FROM inventory i GROUP BY i.part_no;
CREATE VIEW v_price AS SELECT part_no, tier, min_qty, unit_price, currency, valid_to FROM price_list;
CREATE VIEW v_inbound AS SELECT part_no, eta, qty FROM inbound;
CREATE VIEW v_customer_parts AS
  SELECT s.cust_id, c.name AS customer, s.part_no, SUM(s.qty) AS qty_12m, MAX(s.ship_date) AS last_ship
  FROM shipment s JOIN customer c USING (cust_id)
  WHERE s.ship_date >= date('2025-10-01') GROUP BY s.cust_id, s.part_no;
CREATE VIEW v_pcn AS SELECT pcn_id, mfr_part_no, change_type, effective, last_time_buy, replacement, summary FROM pcn;
