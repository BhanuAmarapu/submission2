import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import Config
from mongo_wrapper import get_mongo_connection

db_type = getattr(Config, 'DB_TYPE', 'mysql').lower()

try:
    if db_type == 'mysql':
        print(f"Connecting to MySQL ({Config.MYSQL_USER}@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.MYSQL_DB})...")
        conn = get_mongo_connection()
        tables_res = conn.execute("SHOW TABLES").fetchall()
        tables = [row[0] for row in tables_res]
        print("Tables in MySQL:", tables)

        users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        print(f"Users in MySQL: {users_count}")

        print("\nTable Statistics:")
        for tbl in tables:
            try:
                cnt = conn.execute(f"SELECT COUNT(*) FROM `{tbl}`").fetchone()[0]
                print(f"  - {tbl}: {cnt} rows")
            except Exception as e:
                print(f"  - {tbl}: error ({e})")

        conn.close()
        print("\nMySQL database connection verified successfully!")

    else:
        print(f"Connecting to MongoDB Atlas at database: {Config.MONGO_DB}...")
        from mongo_wrapper import get_mongo_db
        db = get_mongo_db()
        collections = db.list_collection_names()
        print("Collections in MongoDB:", collections)

        conn = get_mongo_connection()
        users_count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        print(f"Users in MongoDB: {users_count}")

        print("\nCollection Statistics:")
        for col in collections:
            if col != 'counters':
                print(f"  - {col}: {db[col].count_documents({})} documents")

        conn.close()
        print("\nMongoDB Atlas connection verified successfully!")

except Exception as e:
    print(f"Connection failed: {e}")
