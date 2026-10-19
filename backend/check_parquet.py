import duckdb

con = duckdb.connect()

all_beauty = con.execute(
    "SELECT count(*) FROM read_parquet('../data/processed/reviews_clean/All_Beauty.parquet')"
).fetchone()[0]

beauty_personal = con.execute(
    "SELECT count(*) FROM read_parquet('../data/processed/reviews_clean/Beauty_and_Personal_Care.parquet')"
).fetchone()[0]

print("All_Beauty:", all_beauty)
print("Beauty_and_Personal_Care:", beauty_personal)

con.close()