"""Single source of truth for what the database contains and exposes."""
from typing import NamedTuple


class Column(NamedTuple):
    csv_name: str
    name: str
    sql_type: str
    description: str


TABLE_DESCRIPTIONS = {
    "patients": "One row per synthetic patient, without direct identifiers.",
    "encounters": "Visits and hospital stays of each patient.",
    "conditions": "Diagnoses recorded for each patient.",
    "medications": "Medications prescribed to each patient.",
}

SCHEMA = {
    "patients": [
        Column("Id", "id", "TEXT PRIMARY KEY", "Patient identifier"),
        Column("BIRTHDATE", "birth_date", "TEXT", "Birth date, YYYY-MM-DD"),
        Column("DEATHDATE", "death_date", "TEXT", "Death date, NULL if alive"),
        Column("GENDER", "gender", "TEXT", "M or F"),
        Column("MARITAL", "marital", "TEXT", "M, S, D, W or NULL"),
        Column("COUNTY", "county", "TEXT", "County of residence"),
        Column("HEALTHCARE_EXPENSES", "healthcare_expenses", "REAL", "Lifetime expenses, USD"),
        Column("HEALTHCARE_COVERAGE", "healthcare_coverage", "REAL", "Lifetime coverage, USD"),
    ],
    "encounters": [
        Column("Id", "id", "TEXT PRIMARY KEY", "Encounter identifier"),
        Column("START", "start_time", "TEXT", "Start, ISO 8601 UTC"),
        Column("STOP", "stop_time", "TEXT", "End, ISO 8601 UTC"),
        Column("PATIENT", "patient_id", "TEXT", "References patients.id"),
        Column("ENCOUNTERCLASS", "encounter_class", "TEXT", "For example ambulatory, wellness, inpatient, emergency"),
        Column("DESCRIPTION", "description", "TEXT", "Type of encounter"),
        Column("TOTAL_CLAIM_COST", "total_claim_cost", "REAL", "Total claim cost, USD"),
        Column("PAYER_COVERAGE", "payer_coverage", "REAL", "Amount covered by the payer, USD"),
        Column("REASONDESCRIPTION", "reason", "TEXT", "Reason for the encounter, may be NULL"),
    ],
    "conditions": [
        Column("START", "start_date", "TEXT", "Onset date, YYYY-MM-DD"),
        Column("STOP", "stop_date", "TEXT", "Resolution date, NULL if ongoing"),
        Column("PATIENT", "patient_id", "TEXT", "References patients.id"),
        Column("ENCOUNTER", "encounter_id", "TEXT", "References encounters.id"),
        Column("CODE", "code", "TEXT", "Clinical code"),
        Column("DESCRIPTION", "description", "TEXT", "Name of the condition"),
    ],
    "medications": [
        Column("START", "start_time", "TEXT", "Start, ISO 8601 UTC"),
        Column("STOP", "stop_time", "TEXT", "End, NULL if ongoing"),
        Column("PATIENT", "patient_id", "TEXT", "References patients.id"),
        Column("ENCOUNTER", "encounter_id", "TEXT", "References encounters.id"),
        Column("CODE", "code", "TEXT", "Medication code"),
        Column("DESCRIPTION", "description", "TEXT", "Name of the medication"),
        Column("DISPENSES", "dispenses", "INTEGER", "Number of dispenses"),
        Column("TOTALCOST", "total_cost", "REAL", "Total cost, USD"),
        Column("REASONDESCRIPTION", "reason", "TEXT", "Reason, may be NULL"),
    ],
}


def create_table_sql(table: str) -> str:
    columns = ", ".join(f"{c.name} {c.sql_type}" for c in SCHEMA[table])
    return f"CREATE TABLE {table} ({columns})"