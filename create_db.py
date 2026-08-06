import os
import psycopg

# Load .env file
env_file = '.env'
if os.path.exists(env_file):
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip("'").strip('"')

# Connect to postgres db to create knowledgebase
try:
    conn = psycopg.connect(
        host=os.getenv('DB_HOST', '127.0.0.1'),
        port=os.getenv('DB_PORT', '5432'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        dbname='postgres',
        autocommit=True
    )
    with conn.cursor() as cur:
        # Check if database already exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'knowledgebase';")
        exists = cur.fetchone()
        if not exists:
            cur.execute("CREATE DATABASE knowledgebase;")
            print("Database 'knowledgebase' created successfully!")
        else:
            print("Database 'knowledgebase' already exists.")
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
