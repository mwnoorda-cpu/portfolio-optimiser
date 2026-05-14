from src.db.connection import get_connection


def init_db():
    con = get_connection()

    con.execute("""
        CREATE TABLE IF NOT EXISTS etf_universe (
            isin VARCHAR,
            product VARCHAR,
            symbol VARCHAR,
            yahoo_ticker VARCHAR,
            provider VARCHAR,
            benchmark VARCHAR,
            region VARCHAR,
            currency VARCHAR,
            total_expense_ratio VARCHAR,
            mapping_status VARCHAR,
            replication_method VARCHAR,
            lookthrough_quality VARCHAR,
            economic_exposure_basis VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS etf_holdings (
            etf_isin VARCHAR,
            as_of_date DATE,
            holding_isin VARCHAR,
            holding_name VARCHAR,
            holding_ticker VARCHAR,
            holding_weight DOUBLE,
            sector VARCHAR,
            country VARCHAR,
            currency VARCHAR,
            provider VARCHAR,
            exposure_type VARCHAR,
            source_file VARCHAR,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS security_master (
            holding_isin VARCHAR,
            holding_name VARCHAR,
            sector VARCHAR,
            country VARCHAR,
            currency VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")