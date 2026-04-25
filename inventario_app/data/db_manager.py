# Archivo: data/db_manager.py
import os
import mysql.connector
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()

class DBManager:
    """
    Clase para gestionar la conexión y las operaciones con la base de datos MySQL.
    Asegura que la conexión se abra y cierre para cada operación para evitar la caché.
    """
    
    def __init__(self):
        """Inicializa los parámetros de conexión desde las variables de entorno."""
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        if not all([self.host, self.database, self.user, self.password]):
            raise ValueError("Faltan variables de conexión a la base de datos en el archivo .env")

    def get_connection(self):
        """
        Establece y retorna una nueva conexión a la base de datos.
        """
        try:
            # Usar autocommit=True previene que los cursores mantengan transacciones abiertas
            # que puedan causar que SELECTs posteriores lean datos viejos.
            conn = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                autocommit=True # Nueva configuración CRÍTICA
            )
            return conn
        except mysql.connector.Error as err:
            print(f"Error al conectar con MySQL: {err}")
            raise err

    def execute_query(self, query, params=None):
        """
        Ejecuta una consulta SELECT y retorna la lista de resultados (filas).
        """
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            return results
        except mysql.connector.Error as err:
            print(f"Error en la consulta: {err}")
            return []
        finally:
            cursor.close()
            conn.close() # Aseguramos el cierre de la conexión

    def execute_commit(self, query, params=None):
        """
        Ejecuta una consulta INSERT, UPDATE o DELETE y realiza un commit.
        Retorna el número de filas afectadas.
        """
        # Ya no necesitamos conn.commit() explícito aquí porque autocommit=True
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            # conn.commit() # Eliminado porque autocommit=True
            return cursor.rowcount
        except mysql.connector.Error as err:
            print(f"Error en la operación de escritura: {err}")
            conn.rollback() # El rollback sigue siendo útil en caso de error
            return 0
        finally:
            cursor.close()
            conn.close() # Aseguramos el cierre de la conexión