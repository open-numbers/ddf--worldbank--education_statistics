# coding: utf8

"""
ETL script to create DDF dataset from World Bank Education Statistics.
"""

from pathlib import Path

import polars as pl

SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR.parent / "source"
OUTPUT_DIR = SCRIPT_DIR.parent.parent  # Root of the DDF dataset
DATAPOINTS_DIR = OUTPUT_DIR / "datapoints"


def to_concept_id_expr(col: str) -> pl.Expr:
    """Return a Polars expression that converts an indicator code column to a valid DDF concept ID."""
    return (
        pl.col(col)
        .str.to_lowercase()
        .str.replace_all(r"[\.\s]+", "_")
        .str.replace_all(r"[^a-z0-9_]", "")
    )


def read_source_csv(filename: str) -> pl.DataFrame:
    """Read source CSV file with proper encoding."""
    df = pl.read_csv(
        SOURCE_DIR / filename, encoding="utf8-lossy", infer_schema_length=0
    )
    # Clean up column names (remove BOM and quotes)
    new_names = [c.strip().replace('"', "").replace("\ufeff", "") for c in df.columns]
    df = df.rename(dict(zip(df.columns, new_names)))
    # Remove unnamed columns
    df = df.select([c for c in df.columns if not c.startswith("Unnamed") and c != ""])
    return df


def create_concepts(data_df: pl.DataFrame) -> pl.DataFrame:
    """Create concepts from series metadata."""
    series_df = read_source_csv("EdStatsSeries.csv")

    # Create concept IDs from Series Code
    concepts = series_df.select(
        to_concept_id_expr("Series Code").alias("concept"),
        pl.lit("measure").alias("concept_type"),
        pl.col("Indicator Name").alias("name"),
        pl.col("Series Code").alias("indicator_code"),
        pl.col("Topic").alias("topic"),
        pl.col("Short definition").alias("short_definition"),
        pl.col("Long definition").alias("long_definition"),
        pl.col("Unit of measure").alias("unit_of_measure"),
        pl.col("Periodicity").alias("periodicity"),
        pl.col("Base Period").alias("base_period"),
        pl.col("Other notes").alias("other_notes"),
        pl.col("Aggregation method").alias("aggregation_method"),
        pl.col("Limitations and exceptions").alias("limitations_and_exceptions"),
        pl.col("Notes from original source").alias("notes_from_original_source"),
        pl.col("General comments").alias("general_comments"),
        pl.col("Source").alias("source"),
        pl.col("Statistical concept and methodology").alias(
            "statistical_concept_and_methodology"
        ),
        pl.col("Development relevance").alias("development_relevance"),
        pl.col("Related source links").alias("related_source_links"),
        pl.col("Other web links").alias("other_web_links"),
        pl.col("Related indicators").alias("related_indicators"),
        pl.col("License Type").alias("license_type"),
    )

    # Add missing indicators from data file
    series_codes = set(
        series_df.select(to_concept_id_expr("Series Code")).to_series().to_list()
    )

    data_indicators = data_df.select(
        pl.col("Indicator Code"),
        pl.col("Indicator Name"),
        to_concept_id_expr("Indicator Code").alias("concept"),
    ).unique()

    missing_indicators = data_indicators.filter(~pl.col("concept").is_in(series_codes))

    if missing_indicators.height > 0:
        print(f"  Adding {missing_indicators.height} indicators from data file")
        missing_concepts = missing_indicators.select(
            pl.col("concept"),
            pl.lit("measure").alias("concept_type"),
            pl.col("Indicator Name").alias("name"),
            pl.col("Indicator Code").alias("indicator_code"),
        )
        concepts = pl.concat([concepts, missing_concepts], how="diagonal")

    # Add dimension concepts
    dim_concepts = pl.DataFrame(
        [
            {"concept": "country", "concept_type": "entity_domain", "name": "Country"},
            {"concept": "year", "concept_type": "time", "name": "Year"},
        ]
    )

    # Add property concepts for country metadata
    property_concepts = [
        {"concept": "short_name", "concept_type": "string", "name": "Short Name"},
        {"concept": "table_name", "concept_type": "string", "name": "Table Name"},
        {"concept": "long_name", "concept_type": "string", "name": "Long Name"},
        {"concept": "alpha2_code", "concept_type": "string", "name": "2-Alpha Code"},
        {"concept": "currency_unit", "concept_type": "string", "name": "Currency Unit"},
        {"concept": "special_notes", "concept_type": "string", "name": "Special Notes"},
        {"concept": "region", "concept_type": "string", "name": "Region"},
        {"concept": "income_group", "concept_type": "string", "name": "Income Group"},
        {"concept": "wb2_code", "concept_type": "string", "name": "WB-2 Code"},
        {
            "concept": "national_accounts_base_year",
            "concept_type": "string",
            "name": "National Accounts Base Year",
        },
        {
            "concept": "national_accounts_reference_year",
            "concept_type": "string",
            "name": "National Accounts Reference Year",
        },
        {
            "concept": "sna_price_valuation",
            "concept_type": "string",
            "name": "SNA Price Valuation",
        },
        {
            "concept": "lending_category",
            "concept_type": "string",
            "name": "Lending Category",
        },
        {"concept": "other_groups", "concept_type": "string", "name": "Other Groups"},
        {
            "concept": "system_of_national_accounts",
            "concept_type": "string",
            "name": "System of National Accounts",
        },
        {
            "concept": "alternative_conversion_factor",
            "concept_type": "string",
            "name": "Alternative Conversion Factor",
        },
        {
            "concept": "ppp_survey_year",
            "concept_type": "string",
            "name": "PPP Survey Year",
        },
        {
            "concept": "balance_of_payments_manual_in_use",
            "concept_type": "string",
            "name": "Balance of Payments Manual in Use",
        },
        {
            "concept": "external_debt_reporting_status",
            "concept_type": "string",
            "name": "External Debt Reporting Status",
        },
        {
            "concept": "system_of_trade",
            "concept_type": "string",
            "name": "System of Trade",
        },
        {
            "concept": "government_accounting_concept",
            "concept_type": "string",
            "name": "Government Accounting Concept",
        },
        {
            "concept": "imf_data_dissemination_standard",
            "concept_type": "string",
            "name": "IMF Data Dissemination Standard",
        },
        {
            "concept": "latest_population_census",
            "concept_type": "string",
            "name": "Latest Population Census",
        },
        {
            "concept": "latest_household_survey",
            "concept_type": "string",
            "name": "Latest Household Survey",
        },
        {
            "concept": "source_of_most_recent_income_and_expenditure_data",
            "concept_type": "string",
            "name": "Source of Most Recent Income and Expenditure Data",
        },
        {
            "concept": "vital_registration_complete",
            "concept_type": "string",
            "name": "Vital Registration Complete",
        },
        {
            "concept": "latest_agricultural_census",
            "concept_type": "string",
            "name": "Latest Agricultural Census",
        },
        {
            "concept": "latest_industrial_data",
            "concept_type": "string",
            "name": "Latest Industrial Data",
        },
        {
            "concept": "latest_trade_data",
            "concept_type": "string",
            "name": "Latest Trade Data",
        },
        {
            "concept": "latest_water_withdrawal_data",
            "concept_type": "string",
            "name": "Latest Water Withdrawal Data",
        },
        # Indicator metadata properties
        {
            "concept": "indicator_code",
            "concept_type": "string",
            "name": "Indicator Code",
        },
        {"concept": "topic", "concept_type": "string", "name": "Topic"},
        {
            "concept": "short_definition",
            "concept_type": "string",
            "name": "Short Definition",
        },
        {
            "concept": "long_definition",
            "concept_type": "string",
            "name": "Long Definition",
        },
        {
            "concept": "unit_of_measure",
            "concept_type": "string",
            "name": "Unit of Measure",
        },
        {"concept": "periodicity", "concept_type": "string", "name": "Periodicity"},
        {"concept": "base_period", "concept_type": "string", "name": "Base Period"},
        {"concept": "other_notes", "concept_type": "string", "name": "Other Notes"},
        {
            "concept": "aggregation_method",
            "concept_type": "string",
            "name": "Aggregation Method",
        },
        {
            "concept": "limitations_and_exceptions",
            "concept_type": "string",
            "name": "Limitations and Exceptions",
        },
        {
            "concept": "notes_from_original_source",
            "concept_type": "string",
            "name": "Notes from Original Source",
        },
        {
            "concept": "general_comments",
            "concept_type": "string",
            "name": "General Comments",
        },
        {"concept": "source", "concept_type": "string", "name": "Source"},
        {
            "concept": "statistical_concept_and_methodology",
            "concept_type": "string",
            "name": "Statistical Concept and Methodology",
        },
        {
            "concept": "development_relevance",
            "concept_type": "string",
            "name": "Development Relevance",
        },
        {
            "concept": "related_source_links",
            "concept_type": "string",
            "name": "Related Source Links",
        },
        {
            "concept": "other_web_links",
            "concept_type": "string",
            "name": "Other Web Links",
        },
        {
            "concept": "related_indicators",
            "concept_type": "string",
            "name": "Related Indicators",
        },
        {"concept": "license_type", "concept_type": "string", "name": "License Type"},
        {"concept": "name", "concept_type": "string", "name": "Name"},
    ]

    prop_df = pl.DataFrame(property_concepts)

    # Combine all concepts
    all_concepts = pl.concat([dim_concepts, prop_df, concepts], how="diagonal")

    # Drop duplicates (keep first occurrence)
    all_concepts = all_concepts.unique(subset=["concept"], keep="first")

    return all_concepts


def create_countries(data_df: pl.DataFrame) -> pl.DataFrame:
    """Create country entities from country metadata."""
    country_df = read_source_csv("EdStatsCountry.csv")

    # Add missing countries from data file
    country_codes = set(
        country_df.select(pl.col("Country Code").str.to_lowercase())
        .to_series()
        .to_list()
    )

    data_countries = data_df.select(
        pl.col("Country Code"),
        pl.col("Country Name"),
        pl.col("Country Code").str.to_lowercase().alias("country_lower"),
    ).unique()

    missing_countries = data_countries.filter(
        ~pl.col("country_lower").is_in(country_codes)
    )

    if missing_countries.height > 0:
        print(f"  Adding {missing_countries.height} countries from data file")
        missing_df = missing_countries.select(
            pl.col("Country Code"),
            pl.col("Country Name").alias("Short Name"),
        )
        country_df = pl.concat([country_df, missing_df], how="diagonal")

    # Build entities dataframe with renamed columns
    entities = country_df.select(
        pl.col("Country Code").str.to_lowercase().alias("country"),
        pl.coalesce(pl.col("Short Name"), pl.col("Country Code")).alias("name"),
        pl.col("Short Name").alias("short_name"),
        pl.col("Table Name").alias("table_name"),
        pl.col("Long Name").alias("long_name"),
        pl.col("2-alpha code").alias("alpha2_code"),
        pl.col("Currency Unit").alias("currency_unit"),
        pl.col("Special Notes").alias("special_notes"),
        pl.col("Region").alias("region"),
        pl.col("Income Group").alias("income_group"),
        pl.col("WB-2 code").alias("wb2_code"),
        pl.col("National accounts base year").alias("national_accounts_base_year"),
        pl.col("National accounts reference year").alias(
            "national_accounts_reference_year"
        ),
        pl.col("SNA price valuation").alias("sna_price_valuation"),
        pl.col("Lending category").alias("lending_category"),
        pl.col("Other groups").alias("other_groups"),
        pl.col("System of National Accounts").alias("system_of_national_accounts"),
        pl.col("Alternative conversion factor").alias("alternative_conversion_factor"),
        pl.col("PPP survey year").alias("ppp_survey_year"),
        pl.col("Balance of Payments Manual in use").alias(
            "balance_of_payments_manual_in_use"
        ),
        pl.col("External debt Reporting status").alias(
            "external_debt_reporting_status"
        ),
        pl.col("System of trade").alias("system_of_trade"),
        pl.col("Government Accounting concept").alias("government_accounting_concept"),
        pl.col("IMF data dissemination standard").alias(
            "imf_data_dissemination_standard"
        ),
        pl.col("Latest population census").alias("latest_population_census"),
        pl.col("Latest household survey").alias("latest_household_survey"),
        pl.col("Source of most recent Income and expenditure data").alias(
            "source_of_most_recent_income_and_expenditure_data"
        ),
        pl.col("Vital registration complete").alias("vital_registration_complete"),
        pl.col("Latest agricultural census").alias("latest_agricultural_census"),
        pl.col("Latest industrial data").alias("latest_industrial_data"),
        pl.col("Latest trade data").alias("latest_trade_data"),
        pl.col("Latest water withdrawal data").alias("latest_water_withdrawal_data"),
    )

    return entities


def create_datapoints(data_df: pl.DataFrame) -> int:
    """Create datapoints from main data file. Writes files directly to save memory.

    Returns the number of datapoint files written.
    """
    # Get year columns (numeric columns)
    year_cols = [c for c in data_df.columns if c.isdigit()]

    print(f"Found {len(year_cols)} year columns: {year_cols[0]} to {year_cols[-1]}")
    print(f"Found {data_df.select('Indicator Code').n_unique()} unique indicators")

    # Melt to long format, keeping only needed columns
    print("Melting data to long format...")
    df_long = data_df.select(
        pl.col("Country Code").str.to_lowercase().alias("country"),
        to_concept_id_expr("Indicator Code").alias("concept"),
        *[pl.col(c) for c in year_cols],
    ).unpivot(
        index=["country", "concept"],
        on=year_cols,
        variable_name="year",
        value_name="value",
    )

    # Drop the source dataframe to free memory
    del data_df

    # Drop rows with empty values and cast year
    df_long = df_long.filter(
        pl.col("value").is_not_null() & (pl.col("value") != "")
    ).with_columns(pl.col("year").cast(pl.Int64))

    print(f"Total datapoints after removing empty values: {df_long.height}")

    # Write each indicator's datapoints directly to disk
    DATAPOINTS_DIR.mkdir(exist_ok=True)
    count = 0
    for (concept_id,), dp in df_long.group_by("concept"):
        dp.select(
            pl.col("country"),
            pl.col("year"),
            pl.col("value").alias(concept_id),
        ).sort(["country", "year"]).write_csv(
            DATAPOINTS_DIR / f"ddf--datapoints--{concept_id}--by--country--year.csv"
        )
        count += 1
        if count % 500 == 0:
            print(f"  Written {count} files...")

    return count


def main():
    """Run the ETL process."""
    # Read data file first to get all indicators and countries
    print("Reading main data file...")
    data_df = read_source_csv("EdStatsData.csv")

    print("\nCreating concepts...")
    concepts = create_concepts(data_df).sort("concept")
    concepts.write_csv(OUTPUT_DIR / "ddf--concepts.csv")
    print(f"Created {concepts.height} concepts")

    print("\nCreating country entities...")
    countries = create_countries(data_df).sort("country")
    countries.write_csv(OUTPUT_DIR / "ddf--entities--country.csv")
    print(f"Created {countries.height} countries")

    print("\nCreating datapoints...")
    num_datapoints = create_datapoints(data_df)

    print(f"\nDone! Created {num_datapoints} datapoint files")


if __name__ == "__main__":
    main()
