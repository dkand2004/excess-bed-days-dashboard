"""Turn raw Synthea (US/Massachusetts) tables into an ieMR-inspired Australian
`fact_separation` table.

Why this exists: Synthea is our *raw material* (synthetic patient timelines).
This script re-labels it using Australian hospital vocabulary and structure.
It does NOT make the clinical content Australian; the README says so.

Run:  python src/australianise.py
"""
import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv

load_dotenv()  # reads .env (paths, window start). Safe defaults below.

RAW = Path(os.getenv("RAW_DATA_DIR", "data/raw"))
OUT = Path(os.getenv("PROCESSED_DATA_DIR", "data/processed"))
DB = os.getenv("DUCKDB_PATH", "data/ebd.duckdb")
# Window start is a setting because Synthea simulates whole lifetimes and a
# short window leaves few stays per hospital. See README "Data" section.
WINDOW_START = os.getenv("WINDOW_START", "2019-01-01")
HOSPITALS = Path("data/mappings/hospitals.csv")

OUT.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(DB)

con.execute(f"create or replace table dim_hospital as select * from read_csv_auto('{HOSPITALS}')")
n_hosp = con.execute("select count(*) from dim_hospital").fetchone()[0]

# Step 1: pick inpatient stays in the window. Synthea 'inpatient' = admitted to a ward,
# which is what length of stay needs. Emergency-only visits are excluded.
con.execute(f"""
create or replace table stg_stay as
select e.Id as episode_id, e.PATIENT as patient_id, e.ORGANIZATION as org_id,
       e.START::timestamp as admission_ts, e.STOP::timestamp as separation_ts,
       e.REASONDESCRIPTION as diagnosis_text
from read_csv_auto('{RAW}/encounters.csv') e
where e.ENCOUNTERCLASS = 'inpatient'
  and e.START::timestamp >= '{WINDOW_START}'
  and e.STOP is not null
""")

# Step 2: assign each *patient* to one of N fictional hospitals using a repeatable hash.
# Why not map the original US hospitals? A few big ones hold hundreds of stays each, so
# grouping by US hospital gave very uneven volumes. Hashing by patient is balanced,
# repeatable (same input -> same hospital) and keeps one patient's stays together.
# Limitation: every fictional hospital gets about the same volume, which real remote
# hospitals would not. Noted in the README.
con.execute(f"""
create or replace table org_map as
select distinct patient_id, 1 + (hash(patient_id) % {n_hosp})::int as hospital_id from stg_stay
""")

# Step 3: build the fact table. Terms follow Australian usage:
#  - separation = discharge / end of an admitted episode
#  - same-day = admitted and separated on the same calendar day
#  - LOS convention: overnight = separation date - admission date; same-day counts as 1
#    (a commonly used convention in Australian hospital statistics; verify before quoting).
#  - mode of separation: Synthea has no transfers, so only 'Died' vs 'Discharged'.
#    A death within 1 day of separation is treated as died in hospital.
con.execute(f"""
create or replace table fact_separation as
select s.episode_id, s.patient_id, h.hospital_id, h.hospital_name, h.state, h.remoteness,
       s.admission_ts, s.separation_ts,
       (s.admission_ts::date = s.separation_ts::date) as same_day,
       greatest(1, date_diff('day', s.admission_ts::date, s.separation_ts::date)) as los_days,
       s.diagnosis_text as diagnosis_group,
       case when p.DEATHDATE is not null
                 and abs(date_diff('day', p.DEATHDATE::date, s.separation_ts::date)) <= 1
            then 'Died' else 'Discharged' end as mode_of_separation,
       case when p.GENDER = 'F' then 'Female' when p.GENDER = 'M' then 'Male' else 'Other' end as sex,
       date_diff('year', p.BIRTHDATE::date, s.admission_ts::date) as age_at_admission,
       case when date_diff('year', p.BIRTHDATE::date, s.admission_ts::date) < 18 then '0-17'
            when date_diff('year', p.BIRTHDATE::date, s.admission_ts::date) < 40 then '18-39'
            when date_diff('year', p.BIRTHDATE::date, s.admission_ts::date) < 65 then '40-64'
            else '65+' end as age_band
from stg_stay s
join org_map m using (patient_id)
join dim_hospital h using (hospital_id)
join read_csv_auto('{RAW}/patients.csv') p on p.Id = s.patient_id
""")
# NOTE: names, SSN, licence, passport, address, race/ethnicity are deliberately NOT carried over.

con.execute(f"copy dim_hospital to '{OUT}/dim_hospital.csv' (header)")
con.execute(f"copy fact_separation to '{OUT}/fact_separation.csv' (header)")
print(con.sql("select count(*) stays, count(distinct patient_id) patients, round(avg(los_days),2) avg_los from fact_separation"))
print(con.sql("select hospital_name, state, remoteness, count(*) stays, round(avg(los_days),2) avg_los from fact_separation group by all order by min(hospital_id)"))
