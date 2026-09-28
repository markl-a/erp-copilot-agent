INSERT INTO part VALUES
 ('WK-10231','Infineon','IPW60R045CP','600V CoolMOS power MOSFET TO-247','active'),
 ('WK-10232','Infineon','IPW60R070P6','600V CoolMOS P6 TO-247','EOL-announced'),
 ('WK-20511','NXP','LPC55S69JBD100','Cortex-M33 MCU 640KB flash','active'),
 ('WK-30077','Realtek','RTL8211F-CG','Gigabit Ethernet PHY','active'),
 ('WK-30078','Realtek','RTL8211FD-CG','Gigabit Ethernet PHY, extended temp','active');
INSERT INTO customer VALUES ('C001','Acme Networks','A'),('C002','Delta Motion','B'),('C003','Nova Medical','B');
INSERT INTO price_list VALUES
 ('WK-10231','A',1,3.10,'USD','2026-12-31'),('WK-10231','A',1000,2.85,'USD','2026-12-31'),('WK-10231','B',1,3.40,'USD','2026-12-31'),
 ('WK-10232','A',1,2.60,'USD','2026-12-31'),('WK-10232','B',1,2.90,'USD','2026-12-31'),
 ('WK-20511','A',1,4.20,'USD','2026-12-31'),('WK-20511','B',1,4.60,'USD','2026-12-31'),('WK-20511','B',2500,4.15,'USD','2026-12-31'),
 ('WK-30077','A',1,0.92,'USD','2026-12-31'),('WK-30077','B',1,1.05,'USD','2026-12-31');
INSERT INTO inventory VALUES ('WK-10231','TPE',1200,300),('WK-10231','HKG',800,0),('WK-10232','TPE',400,350),
 ('WK-20511','TPE',900,100),('WK-30077','TPE',5000,1000),('WK-30078','HKG',0,0);
INSERT INTO inbound VALUES ('WK-20511','2026-11-15',3000),('WK-30078','2026-10-20',2000);
INSERT INTO shipment VALUES
 ('S1','C001','WK-10232',2000,'2026-03-02'),('S2','C002','WK-10232',600,'2026-07-19'),('S3','C001','WK-20511',1500,'2026-08-01'),
 ('S4','C003','WK-30077',4000,'2026-06-11'),('S5','C002','WK-10232',300,'2025-06-01');
INSERT INTO pcn VALUES
 ('PCN-2026-118','IPW60R070P6','EOL','2027-03-31','2026-12-31','IPW60R045CP','CoolMOS P6 TO-247 discontinued; recommended replacement IPW60R045CP.'),
 ('PCN-2026-204','RTL8211F-CG','assembly site change','2026-12-01',NULL,NULL,'Additional assembly site qualified; no form/fit/function change.');
