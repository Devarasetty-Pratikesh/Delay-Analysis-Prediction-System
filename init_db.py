import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.types import VARCHAR, INT, DOUBLE, BOOLEAN, DATE, TEXT

def init_database():
    # 1. Resolve credentials (check env variables first, fallback to secrets.toml)
    if os.environ.get("STREAMLIT_CONNECTIONS_MYSQL_HOST"):
        print("Loading database configuration from environment variables...")
        user = os.environ.get("STREAMLIT_CONNECTIONS_MYSQL_USERNAME", "root")
        password = os.environ.get("STREAMLIT_CONNECTIONS_MYSQL_PASSWORD", "")
        host = os.environ.get("STREAMLIT_CONNECTIONS_MYSQL_HOST", "localhost")
        port = int(os.environ.get("STREAMLIT_CONNECTIONS_MYSQL_PORT", 3306))
        db_name = os.environ.get("STREAMLIT_CONNECTIONS_MYSQL_DATABASE", "rinl_delays")
    else:
        print("Loading database configuration from secrets.toml...")
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if not os.path.exists(secrets_path):
            print(f"Error: Secrets file not found at {secrets_path} and no environment variables present.")
            return

        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
        
        try:
            mysql_config = secrets["connections"]["mysql"]
        except KeyError:
            print("Error: Could not find [connections.mysql] section in secrets.toml.")
            return

        user = mysql_config.get("username", "root")
        password = mysql_config.get("password", "")
        host = mysql_config.get("host", "localhost")
        port = mysql_config.get("port", 3306)
        db_name = mysql_config.get("database", "rinl_delays")

    # 2. Try to connect directly to the database first
    import urllib.parse
    password_encoded = urllib.parse.quote_plus(password)
    db_url = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{db_name}"
    
    print(f"Connecting to database '{db_name}' at {host}:{port}...")
    try:
        db_engine = create_engine(db_url)
        # Test connection
        with db_engine.connect() as conn:
            print(f"Successfully connected directly to database '{db_name}'.")
    except Exception as e:
        print(f"Could not connect directly to database '{db_name}'. Attempting to verify/create database on server...")
        server_url = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/"
        try:
            server_engine = create_engine(server_url)
            with server_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name};"))
                print(f"Database '{db_name}' verified/created.")
            db_engine = create_engine(db_url)
        except Exception as server_err:
            print(f"Error connecting to MySQL server: {server_err}")
            print("Please ensure your MySQL server is running and credentials in secrets.toml/environment are correct.")
            return

    # 4. Load cleaned CSV data if available
    csv_path = r"c:\Users\Prethikesh\Desktop\RINL\cleaned_delays_data.csv"
    if not os.path.exists(csv_path):
        print(f"Cleaned CSV dataset not found at {csv_path}.")
        print("Please run clean_data.py first to generate the cleaned CSV database backup.")
        return

    print(f"Loading cleaned dataset from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Insert a unique integer ID column as the primary key
    df.insert(0, 'id', range(1, len(df) + 1))

    # Convert DEL_DATE string ('dd-mm-yyyy') to pandas datetime object for native SQL DATE format
    df['DEL_DATE'] = pd.to_datetime(df['DEL_DATE'], format='%d-%m-%Y')

    # Define exact schema mappings
    dtype_mapping = {
        'id': INT,
        'DELAY_ID': INT,
        'DEL_DATE': DATE,
        'SHOP_CODE': INT,
        'SHOP_DESC': VARCHAR(100),
        'EQPT': VARCHAR(100),
        'SUB_EQPT': VARCHAR(100),
        'DELAY_FROM': DOUBLE,
        'EFF_DURATION': DOUBLE,
        'AGENCY_CODE': VARCHAR(50),
        'REMARKS': TEXT,
        'MON_RR': VARCHAR(20),
        'SEASON': VARCHAR(20),
        'IS_CONVEYOR': BOOLEAN
    }

    print("Recreating database table 'delays'...")
    try:
        with db_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("DROP TABLE IF EXISTS delays;"))
        
        # Write data to SQL
        df.to_sql(
            name='delays',
            con=db_engine,
            if_exists='fail',
            index=False,
            dtype=dtype_mapping
        )
        
        # Set primary key on the unique ID column
        with db_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(text("ALTER TABLE delays ADD PRIMARY KEY (id);"))
            print("Successfully designated unique 'id' as Primary Key constraint.")

        print(f"Ingested {len(df):,} delay log records successfully into MySQL table 'delays'.")
        print("Database initialization complete! You can now run the dashboard.")
    except Exception as e:
        print(f"Error initializing table and loading records: {e}")

if __name__ == '__main__':
    init_database()
