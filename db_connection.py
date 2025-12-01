import mysql.connector

# --- CONFIGURACIÓN Y CONEXIÓN A MYSQL ---
DB_CONFIG = {
    'user': 'root',
    'password': '1234',
    'host': 'localhost',
    'database': 'timesnapbd'
}

def get_db_connection():
    """Establece y devuelve una nueva conexión a la DB."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar a MySQL: {err}")
        return None
