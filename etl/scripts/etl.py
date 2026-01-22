# coding: utf8

"""
ETL script to create DDF dataset from World Bank Education Statistics.
"""

import re
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR.parent / "source"
OUTPUT_DIR = SCRIPT_DIR.parent.parent  # Root of the DDF dataset
DATAPOINTS_DIR = OUTPUT_DIR / "datapoints"


def to_concept_id(indicator_code: str) -> str:
    """Convert indicator code to valid DDF concept ID."""
    # Lowercase and replace dots/spaces with underscores
    concept_id = indicator_code.lower()
    concept_id = re.sub(r"[.\s]+", "_", concept_id)
    # Remove any other invalid characters
    concept_id = re.sub(r"[^a-z0-9_]", "", concept_id)
    return concept_id


def read_source_csv(filename: str) -> pd.DataFrame:
    """Read source CSV file with proper encoding."""
    return pd.read_csv(SOURCE_DIR / filename, encoding="utf-8-sig")


def create_concepts(data_df: pd.DataFrame) -> pd.DataFrame:
    """Create concepts from series metadata."""
    series_df = read_source_csv("EdStatsSeries.csv")

    # Clean up column names (remove quotes and extra columns)
    series_df.columns = series_df.columns.str.strip().str.replace('"', "")
    series_df = series_df.loc[:, ~series_df.columns.str.startswith("Unnamed")]

    # Create concept IDs from Series Code
    concepts = pd.DataFrame()
    concepts["concept"] = series_df["Series Code"].apply(to_concept_id)
    concepts["concept_type"] = "measure"
    concepts["name"] = series_df["Indicator Name"]
    concepts["indicator_code"] = series_df["Series Code"]
    concepts["topic"] = series_df["Topic"]
    concepts["short_definition"] = series_df["Short definition"]
    concepts["long_definition"] = series_df["Long definition"]
    concepts["unit_of_measure"] = series_df["Unit of measure"]
    concepts["periodicity"] = series_df["Periodicity"]
    concepts["base_period"] = series_df["Base Period"]
    concepts["other_notes"] = series_df["Other notes"]
    concepts["aggregation_method"] = series_df["Aggregation method"]
    concepts["limitations_and_exceptions"] = series_df["Limitations and exceptions"]
    concepts["notes_from_original_source"] = series_df["Notes from original source"]
    concepts["general_comments"] = series_df["General comments"]
    concepts["source"] = series_df["Source"]
    concepts["statistical_concept_and_methodology"] = series_df[
        "Statistical concept and methodology"
    ]
    concepts["development_relevance"] = series_df["Development relevance"]
    concepts["related_source_links"] = series_df["Related source links"]
    concepts["other_web_links"] = series_df["Other web links"]
    concepts["related_indicators"] = series_df["Related indicators"]
    concepts["license_type"] = series_df["License Type"]

    # Add missing indicators from data file
    series_codes = set(series_df["Series Code"].apply(to_concept_id))
    data_indicators = data_df[["Indicator Code", "Indicator Name"]].drop_duplicates()
    data_indicators["concept"] = data_indicators["Indicator Code"].apply(to_concept_id)
    missing_indicators = data_indicators[~data_indicators["concept"].isin(series_codes)]

    if len(missing_indicators) > 0:
        print(f"  Adding {len(missing_indicators)} indicators from data file")
        missing_concepts = pd.DataFrame()
        missing_concepts["concept"] = missing_indicators["concept"].values
        missing_concepts["concept_type"] = "measure"
        missing_concepts["name"] = missing_indicators["Indicator Name"].values
        missing_concepts["indicator_code"] = missing_indicators["Indicator Code"].values
        concepts = pd.concat([concepts, missing_concepts], ignore_index=True)

    # Add dimension concepts
    dim_concepts = pd.DataFrame(
        [
            {"concept": "country", "concept_type": "entity_domain", "name": "Country"},
            {"concept": "year", "concept_type": "time", "name": "Year"},
        ]
    )

    # Add property concepts for country metadata
    country_df = read_source_csv("EdStatsCountry.csv")
    country_df.columns = country_df.columns.str.strip().str.replace('"', "")

    property_concepts = []
    country_property_mapping = {
        "Short Name": ("short_name", "Short Name"),
        "Table Name": ("table_name", "Table Name"),
        "Long Name": ("long_name", "Long Name"),
        "2-alpha code": ("alpha2_code", "2-Alpha Code"),
        "Currency Unit": ("currency_unit", "Currency Unit"),
        "Special Notes": ("special_notes", "Special Notes"),
        "Region": ("region", "Region"),
        "Income Group": ("income_group", "Income Group"),
        "WB-2 code": ("wb2_code", "WB-2 Code"),
        "National accounts base year": (
            "national_accounts_base_year",
            "National Accounts Base Year",
        ),
        "National accounts reference year": (
            "national_accounts_reference_year",
            "National Accounts Reference Year",
        ),
        "SNA price valuation": ("sna_price_valuation", "SNA Price Valuation"),
        "Lending category": ("lending_category", "Lending Category"),
        "Other groups": ("other_groups", "Other Groups"),
        "System of National Accounts": (
            "system_of_national_accounts",
            "System of National Accounts",
        ),
        "Alternative conversion factor": (
            "alternative_conversion_factor",
            "Alternative Conversion Factor",
        ),
        "PPP survey year": ("ppp_survey_year", "PPP Survey Year"),
        "Balance of Payments Manual in use": (
            "balance_of_payments_manual_in_use",
            "Balance of Payments Manual in Use",
        ),
        "External debt Reporting status": (
            "external_debt_reporting_status",
            "External Debt Reporting Status",
        ),
        "System of trade": ("system_of_trade", "System of Trade"),
        "Government Accounting concept": (
            "government_accounting_concept",
            "Government Accounting Concept",
        ),
        "IMF data dissemination standard": (
            "imf_data_dissemination_standard",
            "IMF Data Dissemination Standard",
        ),
        "Latest population census": (
            "latest_population_census",
            "Latest Population Census",
        ),
        "Latest household survey": (
            "latest_household_survey",
            "Latest Household Survey",
        ),
        "Source of most recent Income and expenditure data": (
            "source_of_most_recent_income_and_expenditure_data",
            "Source of Most Recent Income and Expenditure Data",
        ),
        "Vital registration complete": (
            "vital_registration_complete",
            "Vital Registration Complete",
        ),
        "Latest agricultural census": (
            "latest_agricultural_census",
            "Latest Agricultural Census",
        ),
        "Latest industrial data": ("latest_industrial_data", "Latest Industrial Data"),
        "Latest trade data": ("latest_trade_data", "Latest Trade Data"),
        "Latest water withdrawal data": (
            "latest_water_withdrawal_data",
            "Latest Water Withdrawal Data",
        ),
    }

    for src_col, (concept_id, name) in country_property_mapping.items():
        if src_col in country_df.columns:
            property_concepts.append(
                {"concept": concept_id, "concept_type": "string", "name": name}
            )

    # Add property concepts for indicator metadata
    indicator_property_mapping = {
        "indicator_code": ("indicator_code", "Indicator Code"),
        "topic": ("topic", "Topic"),
        "short_definition": ("short_definition", "Short Definition"),
        "long_definition": ("long_definition", "Long Definition"),
        "unit_of_measure": ("unit_of_measure", "Unit of Measure"),
        "periodicity": ("periodicity", "Periodicity"),
        "base_period": ("base_period", "Base Period"),
        "other_notes": ("other_notes", "Other Notes"),
        "aggregation_method": ("aggregation_method", "Aggregation Method"),
        "limitations_and_exceptions": (
            "limitations_and_exceptions",
            "Limitations and Exceptions",
        ),
        "notes_from_original_source": (
            "notes_from_original_source",
            "Notes from Original Source",
        ),
        "general_comments": ("general_comments", "General Comments"),
        "source": ("source", "Source"),
        "statistical_concept_and_methodology": (
            "statistical_concept_and_methodology",
            "Statistical Concept and Methodology",
        ),
        "development_relevance": ("development_relevance", "Development Relevance"),
        "related_source_links": ("related_source_links", "Related Source Links"),
        "other_web_links": ("other_web_links", "Other Web Links"),
        "related_indicators": ("related_indicators", "Related Indicators"),
        "license_type": ("license_type", "License Type"),
    }

    for concept_id, (_, name) in indicator_property_mapping.items():
        property_concepts.append(
            {"concept": concept_id, "concept_type": "string", "name": name}
        )

    # Add name concept
    property_concepts.append(
        {"concept": "name", "concept_type": "string", "name": "Name"}
    )

    prop_df = pd.DataFrame(property_concepts)

    # Combine all concepts
    all_concepts = pd.concat([dim_concepts, prop_df, concepts], ignore_index=True)

    # Drop duplicates (keep first occurrence)
    all_concepts = all_concepts.drop_duplicates(subset=["concept"], keep="first")

    return all_concepts


def create_countries(data_df: pd.DataFrame) -> pd.DataFrame:
    """Create country entities from country metadata."""
    country_df = read_source_csv("EdStatsCountry.csv")
    country_df.columns = country_df.columns.str.strip().str.replace('"', "")
    country_df = country_df.loc[:, ~country_df.columns.str.startswith("Unnamed")]

    # Add missing countries from data file
    country_codes = set(country_df["Country Code"].str.lower())
    data_countries = data_df[["Country Code", "Country Name"]].drop_duplicates()
    data_countries["country_lower"] = data_countries["Country Code"].str.lower()
    missing_countries = data_countries[
        ~data_countries["country_lower"].isin(country_codes)
    ]

    if len(missing_countries) > 0:
        print(f"  Adding {len(missing_countries)} countries from data file")
        for _, row in missing_countries.iterrows():
            new_row = pd.DataFrame(
                {
                    "Country Code": [row["Country Code"]],
                    "Short Name": [row["Country Name"]],
                }
            )
            country_df = pd.concat([country_df, new_row], ignore_index=True)

    entities = pd.DataFrame()
    entities["country"] = country_df["Country Code"].str.lower()
    entities["name"] = country_df["Short Name"].fillna(country_df["Country Code"])
    entities["short_name"] = country_df["Short Name"]
    entities["table_name"] = country_df["Table Name"]
    entities["long_name"] = country_df["Long Name"]
    entities["alpha2_code"] = country_df["2-alpha code"]
    entities["currency_unit"] = country_df["Currency Unit"]
    entities["special_notes"] = country_df["Special Notes"]
    entities["region"] = country_df["Region"]
    entities["income_group"] = country_df["Income Group"]
    entities["wb2_code"] = country_df["WB-2 code"]
    entities["national_accounts_base_year"] = country_df["National accounts base year"]
    entities["national_accounts_reference_year"] = country_df[
        "National accounts reference year"
    ]
    entities["sna_price_valuation"] = country_df["SNA price valuation"]
    entities["lending_category"] = country_df["Lending category"]
    entities["other_groups"] = country_df["Other groups"]
    entities["system_of_national_accounts"] = country_df["System of National Accounts"]
    entities["alternative_conversion_factor"] = country_df[
        "Alternative conversion factor"
    ]
    entities["ppp_survey_year"] = country_df["PPP survey year"]
    entities["balance_of_payments_manual_in_use"] = country_df[
        "Balance of Payments Manual in use"
    ]
    entities["external_debt_reporting_status"] = country_df[
        "External debt Reporting status"
    ]
    entities["system_of_trade"] = country_df["System of trade"]
    entities["government_accounting_concept"] = country_df[
        "Government Accounting concept"
    ]
    entities["imf_data_dissemination_standard"] = country_df[
        "IMF data dissemination standard"
    ]
    entities["latest_population_census"] = country_df["Latest population census"]
    entities["latest_household_survey"] = country_df["Latest household survey"]
    entities["source_of_most_recent_income_and_expenditure_data"] = country_df[
        "Source of most recent Income and expenditure data"
    ]
    entities["vital_registration_complete"] = country_df["Vital registration complete"]
    entities["latest_agricultural_census"] = country_df["Latest agricultural census"]
    entities["latest_industrial_data"] = country_df["Latest industrial data"]
    entities["latest_trade_data"] = country_df["Latest trade data"]
    entities["latest_water_withdrawal_data"] = country_df[
        "Latest water withdrawal data"
    ]

    return entities


def create_datapoints(data_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create datapoints from main data file."""
    # Get year columns (numeric columns)
    year_cols = [c for c in data_df.columns if c.isdigit()]

    print(f"Found {len(year_cols)} year columns: {year_cols[0]} to {year_cols[-1]}")
    print(f"Found {data_df['Indicator Code'].nunique()} unique indicators")

    # Melt to long format
    print("Melting data to long format...")
    df_long = data_df.melt(
        id_vars=["Country Code", "Indicator Code"],
        value_vars=year_cols,
        var_name="year",
        value_name="value",
    )

    # Drop rows with empty values
    df_long = df_long.dropna(subset=["value"])
    df_long = df_long[df_long["value"] != ""]

    # Convert year to integer
    df_long["year"] = df_long["year"].astype(int)

    # Convert country code to lowercase
    df_long["country"] = df_long["Country Code"].str.lower()

    # Create concept ID from indicator code
    df_long["concept"] = df_long["Indicator Code"].apply(to_concept_id)

    print(f"Total datapoints after removing empty values: {len(df_long)}")

    # Group by indicator and create separate dataframes
    datapoints = {}
    for concept_id, group in df_long.groupby("concept"):
        dp = group[["country", "year", "value"]].copy()
        dp.columns = ["country", "year", concept_id]
        dp = dp.sort_values(["country", "year"])
        datapoints[concept_id] = dp

    return datapoints


def main():
    """Run the ETL process."""
    # Read data file first to get all indicators and countries
    print("Reading main data file...")
    data_df = read_source_csv("EdStatsData.csv")
    data_df.columns = data_df.columns.str.strip().str.replace('"', "")
    data_df = data_df.loc[:, ~data_df.columns.str.startswith("Unnamed")]

    print("\nCreating concepts...")
    concepts = create_concepts(data_df)
    concepts.to_csv(OUTPUT_DIR / "ddf--concepts.csv", index=False)
    print(f"Created {len(concepts)} concepts")

    print("\nCreating country entities...")
    countries = create_countries(data_df)
    countries.to_csv(OUTPUT_DIR / "ddf--entities--country.csv", index=False)
    print(f"Created {len(countries)} countries")

    print("\nCreating datapoints...")
    datapoints = create_datapoints(data_df)

    print(f"\nWriting {len(datapoints)} datapoint files...")
    DATAPOINTS_DIR.mkdir(exist_ok=True)
    for i, (concept_id, dp) in enumerate(datapoints.items()):
        filename = f"ddf--datapoints--{concept_id}--by--country--year.csv"
        dp.to_csv(DATAPOINTS_DIR / filename, index=False)
        if (i + 1) % 500 == 0:
            print(f"  Written {i + 1}/{len(datapoints)} files...")

    print(f"\nDone! Created {len(datapoints)} datapoint files")


if __name__ == "__main__":
    main()
