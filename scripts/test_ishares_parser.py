from src.data.holdings_providers.ishares_parser import parse_ishares_holdings

path = "data/raw/holdings/ishares/ishares_test_holdings.csv"

df, as_of_date = parse_ishares_holdings(path)

print("As of date:", as_of_date)
print(df.head())
print(df.dtypes)
print("Weight sum:", df["holding_weight"].sum())