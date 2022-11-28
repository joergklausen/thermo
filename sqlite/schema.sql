CREATE TABLE "tei49c" (
	"dtm"	TIMESTAMP NOT NULL,
	"pcdate"	TEXT,
	"pctime"	TEXT,
	"time"	TEXT,
	"date"	TEXT,
	"o3"	REAL,
	"flags"	TEXT,
	"cellai"	INTEGER,
	"cellbi"	INTEGER,
	"bncht"	REAL,
	"lmpt"	REAL,
	"flowa"	REAL,
	"flowb"	REAL,
	"pres"	REAL,
	"source"	TEXT
)

CREATE TABLE "tei49i" (
	"dtm"	TIMESTAMP NOT NULL,
	"pcdate"	TEXT,
	"pctime"	TEXT,
	"time"	TEXT,
	"date"	TEXT,
	"o3"	REAL,
	"flags"	TEXT,
	"cellai"	INTEGER,
	"cellbi"	INTEGER,
	"bncht"	REAL,
	"lmpt"	REAL,
	"o3lt"	REAL,
	"flowa"	REAL,
	"flowb"	REAL,
	"pres"	REAL,
	"source"	TEXT
)

CREATE TABLE "tei49i_2" (
	"dtm"	TIMESTAMP NOT NULL,
	"pcdate"	TEXT,
	"pctime"	TEXT,
	"time"	TEXT,
	"date"	TEXT,
	"o3"	REAL,
	"flags"	TEXT,
	"cellai"	INTEGER,
	"cellbi"	INTEGER,
	"bncht"	REAL,
	"lmpt"	REAL,
	"o3lt"	REAL,
	"flowa"	REAL,
	"flowb"	REAL,
	"pres"	REAL,
	"source"	TEXT
)

CREATE VIEW "V_O3_tei49c_clean" AS 
select * from tei49c 
where (flags = "1c000000" or flags = "1c100500") and bncht > 23 and lmpt >= 55.5 and o3 > 5 
order by dtm

CREATE VIEW "V_O3_tei49i_clean" as 
select * from tei49i 
where (flags = "0C100400" or flags = "0C104400" or flags = "0C100500" or flags = "0C104500") and o3 > 5
order by dtm

CREATE VIEW "V_O3_tei49i_2_clean" as 
select * from tei49i_2 
where (flags = "0C100000" or flags = "0C100100" or flags = "0C100400" or flags = "0C105000") and o3 > 10 
order by dtm

CREATE VIEW "V_O3_tei49c_hourly" AS
select strftime('%Y-%m-%d %H:00:00', dtm) dtm, count(*) n, avg(o3) as o3,
 (count(*)*sum(o3*o3)-(sum(o3) * sum(o3)))/count(*)/(count(*)-1) varo3 
from V_O3_tei49c_clean group by strftime('%Y-%m-%d %H:00:00', dtm) 
order by strftime('%Y-%m-%d %H:00:00', dtm)

CREATE VIEW "V_O3_tei49i_hourly" AS 
select strftime('%Y-%m-%d %H:00:00', dtm) dtm, count(*) n, avg(o3) as o3,
 (count(*)*sum(o3*o3)-(sum(o3) * sum(o3)))/count(*)/(count(*)-1) varo3 
from V_O3_tei49i_clean group by strftime('%Y-%m-%d %H:00:00', dtm) 
order by strftime('%Y-%m-%d %H:00:00', dtm)

CREATE VIEW "V_O3_tei49i_2_hourly" AS 
select strftime('%Y-%m-%d %H:00:00', dtm) dtm, count(*) n, avg(o3) as o3,
 (count(*)*sum(o3*o3)-(sum(o3) * sum(o3)))/count(*)/(count(*)-1) varo3 
from V_O3_tei49i_2_clean group by strftime('%Y-%m-%d %H:00:00', dtm) 
order by strftime('%Y-%m-%d %H:00:00', dtm)

CREATE VIEW "V_O3_comparison" AS 
select 
  tei49c.dtm, 
  tei49c.o3 o3_tei49c, 
  tei49i.o3 o3_tei49i, 
  tei49i_2.o3 o3_tei49i_2  
from V_O3_tei49c_clean tei49c
left join V_O3_tei49i_clean tei49i
using (dtm)
left join V_O3_tei49i_2_clean tei49i_2 
using (dtm)
union all 
select 
  tei49i.dtm, 
  tei49c.o3 o3_tei49c, 
  tei49i.o3 o3_tei49i, 
  tei49i_2.o3 o3_tei49i_2  
from V_O3_tei49i_clean tei49i
left join V_O3_tei49c_clean tei49c
using (dtm)
left join V_O3_tei49i_2_clean tei49i_2 
using (dtm)
where tei49c.dtm is null and tei49i_2.dtm is null
union all 
select 
  tei49i_2.dtm, 
  tei49c.o3 o3_tei49c, 
  tei49i.o3 o3_tei49i, 
  tei49i_2.o3 o3_tei49i_2  
from V_O3_tei49i_2_clean tei49i_2
left join V_O3_tei49c_clean tei49c
using (dtm)
left join V_O3_tei49i_clean tei49i 
using (dtm)
where tei49c.dtm is null and tei49i.dtm is null

-- can be improved along the lines of V_O3_comparison
CREATE VIEW "V_O3_hourly_comparison" AS 
select dtm, o3 o3_tei49c, Null o3_tei49i, Null o3_tei49i_2 from V_O3_tei49c_hourly
union
select dtm, Null o3_tei49c, o3 o3_tei49i, Null o3_tei49i_2 from V_O3_tei49i_hourly
union 
select dtm, Null o3_tei49c, Null o3_tei49i, o3 o3_tei49i_2 from V_O3_tei49i_2_hourly
order by dtm

