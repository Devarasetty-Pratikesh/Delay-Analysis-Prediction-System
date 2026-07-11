import pandas as pd
import numpy as np
import os

def clean_delays_dataset():
    csv_path = r"c:\Users\Prethikesh\Desktop\RINL\sample_delays_data.csv"
    master_path = r"c:\Users\Prethikesh\Desktop\RINL\master_data.xls"
    output_path = r"c:\Users\Prethikesh\Desktop\RINL\cleaned_delays_data.csv"
    
    print("Loading datasets...")
    df = pd.read_csv(csv_path)
    m_df = pd.read_excel(master_path, sheet_name='SQL Results')
    
    print(f"Original shape: {df.shape}")
    
    # 1. Parse Dates and Shift by +20 Years (7305 days)
    print("Parsing dates and applying +20 year shift...")
    df['DATE'] = pd.to_datetime(df['DEL_DATE'], format='%d-%m-%Y', errors='coerce')
    if df['DATE'].isnull().any():
        df = df.dropna(subset=['DATE'])
        
    df['DATE'] = df['DATE'] + pd.to_timedelta(7305, unit='D')
    df['DEL_DATE'] = df['DATE'].dt.strftime('%d-%m-%Y')
    df['MON_RR'] = df['DATE'].dt.strftime('%b-%y').str.upper()
    
    # 2. Define Seasons
    df['SEASON'] = df['DATE'].dt.month.apply(lambda m: 'Monsoon' if m in [6, 7, 8, 9] else 'Non-Monsoon')
    
    # 3. Standardize durations (HH.MM format to decimal hours)
    print("Processing and standardizing durations...")
    def hhmm_to_hours(val):
        if pd.isnull(val):
            return np.nan
        val_abs = abs(val)
        hours = int(val_abs)
        dec = round((val_abs - hours) * 100)
        if dec >= 60:
            hours += dec // 60
            dec = dec % 60
        return hours + dec / 60.0

    df['calc_from_hours'] = df['DELAY_FROM'].apply(hhmm_to_hours)
    df['calc_to_hours'] = df['DELAY_TO'].apply(hhmm_to_hours)

    def calc_duration_hours(row):
        f = row['calc_from_hours']
        t = row['calc_to_hours']
        d = row['DELAY_DURN']
        
        if pd.isnull(f) or pd.isnull(t):
            if not pd.isnull(d):
                return hhmm_to_hours(d)
            return np.nan
        
        if f == 0.0 and t == 0.0 and not pd.isnull(d) and d > 0:
            return hhmm_to_hours(d)
            
        if t >= f:
            dur = t - f
        else:
            dur = (24.0 - f) + t
            
        if dur == 0.0 and not pd.isnull(d) and d > 0:
            return hhmm_to_hours(d)
            
        return dur

    df['CALC_DURATION_HOURS'] = df.apply(calc_duration_hours, axis=1)
    df['EFF_DURATION_CLEAN'] = df['EFF_DURATION'].fillna(df['CALC_DURATION_HOURS'])
    
    # Drop intermediate columns
    df = df.drop(columns=['calc_from_hours', 'calc_to_hours'])
    
    # 4. Impute Shop Descriptions and Equipments
    print("Mapping shop and equipment metadata...")
    shop_desc_map = m_df.dropna(subset=['SHOP_CODE', 'SHOP_DESC']).set_index('SHOP_CODE')['SHOP_DESC'].to_dict()
    
    def assign_shop_desc(row):
        code = row['SHOP_CODE']
        eq = str(row['EQPT']).upper()
        if code == 7:
            if 'BILLET' in eq or 'BAR' in eq:
                return 'BAR/BILLET MILL'
            return 'BAR MILL'
        return shop_desc_map.get(code, 'UNKNOWN')

    df['SHOP_DESC'] = df.apply(assign_shop_desc, axis=1)

    # Impute EQPT using SUB_EQPT or REMARKS
    sub_to_eqpt = m_df.dropna(subset=['SUB_EQPT_CODE', 'EQPT_CODE']).set_index('SUB_EQPT_CODE')['EQPT_CODE'].to_dict()

    def impute_eqpt(row):
        eq = row['EQPT']
        sub = row['SUB_EQPT']
        rem = str(row['REMARKS']).upper()
        
        if not pd.isnull(eq):
            return str(eq).strip().upper()
            
        if not pd.isnull(sub):
            sub_str = str(sub).strip().upper()
            if sub_str in sub_to_eqpt:
                return sub_to_eqpt[sub_str]
            if sub_str.startswith('CC-') or sub_str.startswith('CO-') or 'CONV' in sub_str:
                return 'CONVEYOR'
            if 'CHAMBER' in sub_str:
                return 'CHAMBER'
            if 'STOVE' in sub_str:
                return 'STOVE'
            return sub_str
            
        if 'CONV' in rem or 'CONY' in rem or 'CONVEYOR' in rem:
            return 'CONVEYOR'
        if 'MILL' in rem:
            return 'MILL'
        if 'IDLE' in rem:
            return 'IDLE'
            
        return 'UNKNOWN'

    df['CLEAN_EQPT'] = df.apply(impute_eqpt, axis=1)

    # 5. Classify Conveyors
    print("Classifying conveyors...")
    def is_conveyor(row):
        eq = str(row['CLEAN_EQPT']).upper()
        sub = str(row['SUB_EQPT']).upper()
        rem = str(row['REMARKS']).upper()
        
        if 'CONV' in eq or 'CONVEYOR' in eq or 'CONY' in eq:
            return True
        if 'CONV' in sub or 'CONVEYOR' in sub or 'CONY' in sub or sub.startswith('CC-') or sub.startswith('CO-'):
            return True
        if 'CONV' in rem or 'CONVEYOR' in rem or 'CONY' in rem:
            return True
        return False

    df['IS_CONVEYOR'] = df.apply(is_conveyor, axis=1)
    
    # 6. Drop Unnecessary Columns
    print("Dropping unnecessary columns...")
    keep_columns = [
        'DELAY_ID',
        'DEL_DATE',
        'SHOP_CODE',
        'SHOP_DESC',
        'CLEAN_EQPT',
        'SUB_EQPT',
        'DELAY_FROM',
        'EFF_DURATION_CLEAN',
        'AGENCY_CODE',
        'REMARKS',
        'MON_RR',
        'SEASON',
        'IS_CONVEYOR'
    ]
    
    # Select only the columns that exist in df and are in keep_columns
    df_cleaned = df[[col for col in keep_columns if col in df.columns]].copy()
    
    # Rename CLEAN_EQPT to EQPT in the final output to keep it standard
    df_cleaned = df_cleaned.rename(columns={'CLEAN_EQPT': 'EQPT', 'EFF_DURATION_CLEAN': 'EFF_DURATION'})
    
    # 7. Save cleaned dataset
    print("Saving cleaned dataset...")
    df_cleaned.to_csv(output_path, index=False)
    print(f"Dataset successfully cleaned and saved to: {output_path}")
    print(f"Cleaned shape: {df_cleaned.shape}")
    print(f"Columns in cleaned dataset: {list(df_cleaned.columns)}")
    
    # 8. Export to MySQL database
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
            
        try:
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
            mysql_config = secrets["connections"]["mysql"]
            
            user = mysql_config.get("username", "root")
            password = mysql_config.get("password", "")
            host = mysql_config.get("host", "localhost")
            port = mysql_config.get("port", 3306)
            db_name = mysql_config.get("database", "rinl_delays")
            
            # Reformat to native SQL DATE format
            df_to_db = df_cleaned.copy()
            df_to_db.insert(0, 'id', range(1, len(df_to_db) + 1))
            df_to_db['DEL_DATE'] = pd.to_datetime(df_to_db['DEL_DATE'], format='%d-%m-%Y')
            
            from sqlalchemy import create_engine, text
            from sqlalchemy.types import VARCHAR, INT, DOUBLE, BOOLEAN, DATE, TEXT
            
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
            
            import urllib.parse
            password_encoded = urllib.parse.quote_plus(password)
            db_url = f"mysql+pymysql://{user}:{password_encoded}@{host}:{port}/{db_name}"
            db_engine = create_engine(db_url)
            
            print(f"Connecting to MySQL database '{db_name}' at {host}...")
            with db_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(text("DROP TABLE IF EXISTS delays;"))
            
            df_to_db.to_sql(
                name='delays',
                con=db_engine,
                if_exists='fail',
                index=False,
                dtype=dtype_mapping
            )
            
            with db_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(text("ALTER TABLE delays ADD PRIMARY KEY (id);"))
                
            print(f"Ingested {len(df_to_db):,} records successfully into MySQL table 'delays' and set Primary Key.")
        except Exception as db_err:
            print(f"Warning: Database export failed: {db_err}")
            print("Local CSV backup is saved and ready for Streamlit fallback usage.")
    else:
        print("Note: Secrets config file not found. Ingested to local CSV only.")

if __name__ == '__main__':
    clean_delays_dataset()
