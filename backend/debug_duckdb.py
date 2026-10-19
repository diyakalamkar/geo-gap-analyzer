import duckdb
from pathlib import Path


# =========================================================
# CONFIGURATION
# =========================================================

RAW_FILE = Path(
    r"C:\Users\Nalavade\PycharmProjects\geo-gap-analyzer\data\raw\All_Beauty.jsonl"
)

CATEGORY = "All_Beauty"


# =========================================================
# CONNECTION
# =========================================================

con = duckdb.connect()

print("DuckDB version:", duckdb.__version__)
print("File exists:", RAW_FILE.exists())
print("File:", RAW_FILE)


# =========================================================
# EXPLICIT REVIEW SCHEMA
# =========================================================
#
# This matches the review JSONL structure already verified
# from the dataset.
#
# "images" is intentionally not included because it is not
# required by the cleaning pipeline.
# =========================================================

SCHEMA = """
{
    'rating': 'DOUBLE',
    'title': 'VARCHAR',
    'text': 'VARCHAR',
    'asin': 'VARCHAR',
    'parent_asin': 'VARCHAR',
    'user_id': 'VARCHAR',
    'timestamp': 'BIGINT',
    'helpful_vote': 'BIGINT',
    'verified_purchase': 'BOOLEAN'
}
"""


# =========================================================
# TEST 1 - BASIC DUCKDB
# =========================================================

print("\n" + "=" * 60)
print("TEST 1 - Basic DuckDB")
print("=" * 60)

query = """
SELECT 42
"""

result = con.execute(query).fetchone()

print("Result:", result)


# =========================================================
# TEST 2 - READ JSONL
# =========================================================

print("\n" + "=" * 60)
print("TEST 2 - Read JSONL")
print("=" * 60)

query = f"""
SELECT count(*)
FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited'
)
"""

result = con.execute(query).fetchone()

print("JSONL row count:", result)


# =========================================================
# TEST 3 - EXPLICIT JSON SCHEMA
# =========================================================

print("\n" + "=" * 60)
print("TEST 3 - Explicit JSON schema")
print("=" * 60)

query = f"""
SELECT
    rating,
    title,
    text,
    asin,
    parent_asin,
    user_id,
    timestamp,
    helpful_vote,
    verified_purchase

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

LIMIT 3
"""

result = con.execute(query).fetchall()

for row in result:
    print(row)


# =========================================================
# TEST 4 - ROW_NUMBER
# =========================================================

print("\n" + "=" * 60)
print("TEST 4 - ROW_NUMBER")
print("=" * 60)

query = f"""
SELECT
    user_id,
    asin,
    timestamp,

    row_number() OVER (
        PARTITION BY user_id, asin, timestamp
        ORDER BY length(coalesce(text, '')) DESC
    ) AS rn

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)
"""

result = con.execute(query).fetchall()

print("Number of rows:", len(result))

for row in result[:5]:
    print(row)


# =========================================================
# TEST 5 - QUALIFY
# =========================================================

print("\n" + "=" * 60)
print("TEST 5 - QUALIFY")
print("=" * 60)

query = f"""
SELECT
    user_id,
    asin,
    timestamp,

    row_number() OVER (
        PARTITION BY user_id, asin, timestamp
        ORDER BY length(coalesce(text, '')) DESC
    ) AS rn

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

QUALIFY rn = 1
"""

result = con.execute(query).fetchall()

print("Rows after QUALIFY:", len(result))

for row in result[:5]:
    print(row)


# =========================================================
# TEST 6 - TIMESTAMP CONVERSION
# =========================================================

print("\n" + "=" * 60)
print("TEST 6 - Timestamp conversion")
print("=" * 60)

query = f"""
SELECT
    timestamp,

    timestamp / 1000.0 AS timestamp_seconds,

    to_timestamp(timestamp / 1000.0)::TIMESTAMP
        AS review_ts

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

LIMIT 5
"""

result = con.execute(query).fetchall()

for row in result:
    print(row)


# =========================================================
# TEST 7 - FULL TEXT CONSTRUCTION
# =========================================================

print("\n" + "=" * 60)
print("TEST 7 - Full text construction")
print("=" * 60)

query = f"""
SELECT
    title,
    text,

    concat_ws(
        '. ',
        nullif(trim(title), ''),
        nullif(trim(text), '')
    ) AS full_text

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

LIMIT 5
"""

result = con.execute(query).fetchall()

for row in result:
    print(row)


# =========================================================
# TEST 8 - HTML REMOVAL
# =========================================================

print("\n" + "=" * 60)
print("TEST 8 - HTML removal")
print("=" * 60)

query = f"""
SELECT

    regexp_replace(
        concat_ws(
            '. ',
            nullif(trim(title), ''),
            nullif(trim(text), '')
        ),

        '<[^>]+>',

        ' ',

        'g'

    ) AS cleaned_html

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

LIMIT 5
"""

result = con.execute(query).fetchall()

for row in result:
    print(row)


# =========================================================
# TEST 9 - WHITESPACE NORMALIZATION
# =========================================================

print("\n" + "=" * 60)
print("TEST 9 - Whitespace normalization")
print("=" * 60)

query = f"""
SELECT

    trim(

        regexp_replace(

            regexp_replace(

                concat_ws(
                    '. ',
                    nullif(trim(title), ''),
                    nullif(trim(text), '')
                ),

                '<[^>]+>',

                ' ',

                'g'
            ),

            '\\\\s+',

            ' ',

            'g'
        )

    ) AS full_text

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

LIMIT 5
"""

result = con.execute(query).fetchall()

for row in result:
    print(row)


# =========================================================
# TEST 10 - MD5 REVIEW ID
# =========================================================

print("\n" + "=" * 60)
print("TEST 10 - MD5 review ID")
print("=" * 60)

query = f"""
SELECT

    md5(
        concat_ws(
            '|',
            '{CATEGORY}',
            user_id,
            asin,
            CAST(timestamp AS VARCHAR)
        )
    ) AS review_id

FROM read_json(
    '{RAW_FILE.as_posix()}',
    format='newline_delimited',
    columns={SCHEMA}
)

LIMIT 5
"""

result = con.execute(query).fetchall()

for row in result:
    print(row)


# =========================================================
# TEST 11 - COMPLETE CLEANING SELECT
# =========================================================
#
# IMPORTANT:
#
# The previous failing query performed:
#
#     read_json
#         -> filtering
#         -> QUALIFY
#         -> derived expressions
#
# in one SELECT block.
#
# Here we deliberately separate the operations:
#
#     source
#        ↓
#     filtered
#        ↓
#     deduplicated
#        ↓
#     final SELECT
#
# This isolates the window/deduplication operation from
# review_id, timestamp and full_text calculations.
# =========================================================

print("\n" + "=" * 60)
print("TEST 11 - Complete cleaning SELECT")
print("=" * 60)

query = f"""
WITH source AS (

    SELECT
        rating,
        title,
        text,
        asin,
        parent_asin,
        user_id,
        timestamp,
        helpful_vote,
        verified_purchase

    FROM read_json(
        '{RAW_FILE.as_posix()}',
        format='newline_delimited',
        columns={SCHEMA}
    )

),

filtered AS (

    SELECT *
    FROM source

    WHERE rating BETWEEN 1 AND 5
      AND parent_asin IS NOT NULL
      AND timestamp IS NOT NULL

),

ranked AS (

    SELECT
        *,
        row_number() OVER (
            PARTITION BY user_id, asin, timestamp
            ORDER BY length(coalesce(text, '')) DESC
        ) AS rn

    FROM filtered

),

deduplicated AS (

    SELECT
        rating,
        title,
        text,
        asin,
        parent_asin,
        user_id,
        timestamp,
        helpful_vote,
        verified_purchase

    FROM ranked

    WHERE rn = 1

)

SELECT

    md5(
        concat_ws(
            '|',
            '{CATEGORY}',
            user_id,
            asin,
            CAST(timestamp AS VARCHAR)
        )
    ) AS review_id,

    '{CATEGORY}' AS category,

    parent_asin,

    asin,

    user_id,

    rating,

    to_timestamp(timestamp / 1000.0)::TIMESTAMP
        AS review_ts,

    title,

    text,

    trim(

        regexp_replace(

            regexp_replace(

                concat_ws(
                    '. ',
                    nullif(trim(title), ''),
                    nullif(trim(text), '')
                ),

                '<[^>]+>',

                ' ',

                'g'
            ),

            '\\\\s+',

            ' ',

            'g'
        )

    ) AS full_text,

    coalesce(
        helpful_vote,
        0
    ) AS helpful_vote,

    coalesce(
        verified_purchase,
        FALSE
    ) AS verified_purchase

FROM deduplicated

LIMIT 10
"""

result = con.execute(query).fetchall()

print("Rows returned:", len(result))

for row in result[:3]:
    print(row)


# =========================================================
# TEST 12 - COMPLETE CLEANING + PARQUET
# =========================================================
#
# Only run this after TEST 11 succeeds.
#
# This checks whether the actual COPY -> Parquet operation
# works.
# =========================================================

print("\n" + "=" * 60)
print("TEST 12 - Complete cleaning SELECT + Parquet")
print("=" * 60)

TEST_OUTPUT = Path(
    r"C:\Users\Nalavade\PycharmProjects\geo-gap-analyzer\data\processed"
) / "debug_All_Beauty.parquet"

TEST_OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

# Remove old diagnostic output if it exists.
if TEST_OUTPUT.exists():
    TEST_OUTPUT.unlink()


query = f"""
COPY (

    WITH source AS (

        SELECT
            rating,
            title,
            text,
            asin,
            parent_asin,
            user_id,
            timestamp,
            helpful_vote,
            verified_purchase

        FROM read_json(
            '{RAW_FILE.as_posix()}',
            format='newline_delimited',
            columns={SCHEMA}
        )

    ),

    filtered AS (

        SELECT *

        FROM source

        WHERE rating BETWEEN 1 AND 5
          AND parent_asin IS NOT NULL
          AND timestamp IS NOT NULL

    ),

    ranked AS (

        SELECT
            *,
            row_number() OVER (
                PARTITION BY user_id, asin, timestamp
                ORDER BY length(coalesce(text, '')) DESC
            ) AS rn

        FROM filtered

    ),

    deduplicated AS (

        SELECT
            rating,
            title,
            text,
            asin,
            parent_asin,
            user_id,
            timestamp,
            helpful_vote,
            verified_purchase

        FROM ranked

        WHERE rn = 1

    )

    SELECT

        md5(
            concat_ws(
                '|',
                '{CATEGORY}',
                user_id,
                asin,
                CAST(timestamp AS VARCHAR)
            )
        ) AS review_id,

        '{CATEGORY}' AS category,

        parent_asin,

        asin,

        user_id,

        rating,

        to_timestamp(timestamp / 1000.0)::TIMESTAMP
            AS review_ts,

        title,

        text,

        trim(

            regexp_replace(

                regexp_replace(

                    concat_ws(
                        '. ',
                        nullif(trim(title), ''),
                        nullif(trim(text), '')
                    ),

                    '<[^>]+>',

                    ' ',

                    'g'
                ),

                '\\\\s+',

                ' ',

                'g'
            )

        ) AS full_text,

        coalesce(
            helpful_vote,
            0
        ) AS helpful_vote,

        coalesce(
            verified_purchase,
            FALSE
        ) AS verified_purchase

    FROM deduplicated

)

TO '{TEST_OUTPUT.as_posix()}'

(
    FORMAT PARQUET,
    COMPRESSION ZSTD
)
"""

con.execute(query)

print("Parquet created:", TEST_OUTPUT.exists())
print("Parquet path:", TEST_OUTPUT)


# =========================================================
# TEST 13 - VERIFY PARQUET
# =========================================================

print("\n" + "=" * 60)
print("TEST 13 - Verify Parquet")
print("=" * 60)

if TEST_OUTPUT.exists():

    query = f"""
    SELECT count(*)
    FROM read_parquet(
        '{TEST_OUTPUT.as_posix()}'
    )
    """

    result = con.execute(query).fetchone()

    print("Parquet row count:", result)

    query = f"""
    SELECT *
    FROM read_parquet(
        '{TEST_OUTPUT.as_posix()}'
    )
    LIMIT 3
    """

    result = con.execute(query).fetchall()

    print("\nFirst 3 Parquet rows:")

    for row in result:
        print(row)

else:

    print("ERROR: Parquet file was not created.")


# =========================================================
# CLOSE CONNECTION
# =========================================================

con.close()

print("\n" + "=" * 60)
print("ALL TESTS COMPLETED")
print("=" * 60)