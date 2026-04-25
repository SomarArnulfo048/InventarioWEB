# core/services.py

from data.db_manager import DBManager
from .models import Usuario, Dispositivo
from datetime import datetime
from flask_login import UserMixin
from types import SimpleNamespace
import pandas as pd 

# Clase para manejar al administrador con Flask-Login
class AdminUser(UserMixin):
    def __init__(self, id_admin, username, password, role='admin'):
        self.id = id_admin
        self.username = username
        self.password = password
        self.role = role

# --- FUNCIONES AUXILIARES ---
def clean_input(value):
    return value.strip() if isinstance(value, str) and value is not None else value

def get_id_or_none(field_name, form_or_dict):
    val = clean_input(form_or_dict.get(field_name))
    if val and isinstance(val, str) and val.isdigit() and int(val) > 0:
        return int(val)
    if isinstance(val, int) and val > 0:
        return val
    return None

class InventarioService:

    # --- ADMINISTRADORES (LOGIN) ---
    def get_admin_by_username(self, username):
        data = self.db_manager.execute_query("SELECT * FROM administradores WHERE username = %s", (username,))
        if data:
            row = data[0]
            # Pasamos el rol al crear el objeto
            return AdminUser(row['id_admin'], row['username'], row['password'], row['role'])
        return None

    def get_admin_by_id(self, user_id):
        data = self.db_manager.execute_query("SELECT * FROM administradores WHERE id_admin = %s", (user_id,))
        if data:
            row = data[0]
            # Pasamos el rol aquí también
            return AdminUser(row['id_admin'], row['username'], row['password'], row['role'])
        return None
    
    def __init__(self):
        self.db_manager = DBManager()

    # --- [NUEVO] LÓGICA DE HISTORIAL ---
    def registrar_historial(self, id_dispositivo, id_usuario_anterior, id_usuario_nuevo, comentarios="Cambio de asignación"):
        """
        Guarda un registro en la tabla historial_movimientos.
        Solo se llama si detectamos un cambio de usuario.
        """
        query = """
            INSERT INTO historial_movimientos 
            (id_dispositivo, usuario_anterior, usuario_nuevo, comentarios)
            VALUES (%s, %s, %s, %s)
        """
        # Si son None, los dejamos como None para la BD
        user_ant = id_usuario_anterior if id_usuario_anterior else None
        user_nue = id_usuario_nuevo if id_usuario_nuevo else None
        
        self.db_manager.execute_commit(query, (id_dispositivo, user_ant, user_nue, comentarios))

    def get_historial_by_device(self, id_dispositivo):
        # Esta consulta une tablas para obtener los nombres reales de los usuarios (no solo sus IDs)
        query = """
            SELECT 
                h.fecha_movimiento,
                h.comentarios,
                ua.nombre AS ant_nombre, ua.apellidos AS ant_apellidos,
                un.nombre AS nue_nombre, un.apellidos AS nue_apellidos
            FROM historial_movimientos h
            LEFT JOIN usuarios ua ON h.usuario_anterior = ua.id_usuario
            LEFT JOIN usuarios un ON h.usuario_nuevo = un.id_usuario
            WHERE h.id_dispositivo = %s
            ORDER BY h.fecha_movimiento DESC
        """
        return self.db_manager.execute_query(query, (id_dispositivo,))
    
    # --- DISPOSITIVOS ---
    def get_dispositivos_by_view(self, view_name):
        base_query = f"SELECT SQL_NO_CACHE * FROM {view_name} ORDER BY id_dispositivo DESC"
        return self.db_manager.execute_query(base_query)

    def get_dispositivo_by_id(self, id_dispositivo):
        query = "SELECT * FROM dispositivos WHERE id_dispositivo = %s"
        data = self.db_manager.execute_query(query, (id_dispositivo,))
        return Dispositivo.from_dict(data[0]) if data else None

    def get_dispositivo_detail(self, id_dispositivo):
        query = """
        SELECT d.*, m.nombre AS marca_nombre, s.estado AS estado_nombre, 
               u.id_usuario AS user_id, u.nombre AS user_nombre, u.apellidos AS user_apellidos, u.correo AS user_correo, 
               e.nombre AS empresa_nombre, td.nombre AS tipo_dispositivo, s.color AS estado_color
        FROM dispositivos d
        LEFT JOIN marcas m ON d.marca = m.id_marca
        LEFT JOIN estados s ON d.estado = s.id_status
        LEFT JOIN usuarios u ON d.usuario = u.id_usuario
        LEFT JOIN empresas e ON u.empresa = e.id_empresa
        LEFT JOIN tipo_dispositivo td ON d.tipo = td.id_tipo
        WHERE d.id_dispositivo = %s;
        """
        data = self.db_manager.execute_query(query, (id_dispositivo,))
        return SimpleNamespace(**data[0]) if data else None

    def add_dispositivo(self, dispositivo: Dispositivo):
        # Aseguramos que la fecha vacía sea None para que MySQL no falle
        fecha = dispositivo.fecha_compra if dispositivo.fecha_compra else None
        
        query = """INSERT INTO dispositivos 
                   (tipo, marca, modelo, estado, identificador, costo, fecha_compra, numerotel, plan_inicio, plan_fin, extra_info, usuario)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        params = (dispositivo.tipo, dispositivo.marca, dispositivo.modelo, dispositivo.estado, dispositivo.identificador, 
                  dispositivo.costo, fecha, # <--- Usamos la variable saneada
                  dispositivo.numerotel, dispositivo.plan_inicio, dispositivo.plan_fin, dispositivo.extra_info, dispositivo.usuario)
        
        return self.db_manager.execute_commit(query, params)

    def update_dispositivo(self, nuevo_disp: Dispositivo):
        # 1. Lógica del Historial (Se mantiene igual)
        dispositivo_actual = self.get_dispositivo_by_id(nuevo_disp.id_dispositivo)
        
        if dispositivo_actual:
            usuario_anterior = dispositivo_actual.usuario
            usuario_nuevo = nuevo_disp.usuario
            if usuario_anterior != usuario_nuevo:
                self.registrar_historial(nuevo_disp.id_dispositivo, usuario_anterior, usuario_nuevo)

        # 2. SQL ACTUALIZADO (Aquí faltaban el costo y la fecha)
        query = """
            UPDATE dispositivos SET 
            tipo=%s, marca=%s, modelo=%s, estado=%s, identificador=%s, 
            costo=%s, fecha_compra=%s, 
            numerotel=%s, plan_inicio=%s, plan_fin=%s, extra_info=%s, usuario=%s 
            WHERE id_dispositivo=%s
        """
        
        params = (
            nuevo_disp.tipo, 
            nuevo_disp.marca, 
            nuevo_disp.modelo, 
            nuevo_disp.estado, 
            nuevo_disp.identificador, 
            nuevo_disp.costo,        
            nuevo_disp.fecha_compra, 
            nuevo_disp.numerotel, 
            nuevo_disp.plan_inicio, 
            nuevo_disp.plan_fin, 
            nuevo_disp.extra_info, 
            nuevo_disp.usuario, 
            nuevo_disp.id_dispositivo
        )
        
        return self.db_manager.execute_commit(query, params)
    
    def delete_dispositivo(self, id_dispositivo):
        # [MODIFICADO] Primero borramos historial para evitar error de FK (o usamos CASCADE en BD)
        # Como pusimos ON DELETE CASCADE en la BD nueva, no es necesario borrar historial manualmente.
        return self.db_manager.execute_commit("DELETE FROM dispositivos WHERE id_dispositivo = %s", (id_dispositivo,))

    # --- USUARIOS ---
    def get_all_usuarios(self):
        base_query = "SELECT SQL_NO_CACHE u.*, e.nombre AS empresa_nombre FROM usuarios u LEFT JOIN empresas e ON u.empresa = e.id_empresa ORDER BY u.apellidos;"
        
        # Consulta corregida para contar dispositivos
        device_query = """
            SELECT u.id_usuario,
                COALESCE((SELECT GROUP_CONCAT(CONCAT(m.nombre, ' ', d.modelo) SEPARATOR ', ') FROM dispositivos d JOIN marcas m ON d.marca = m.id_marca WHERE d.usuario = u.id_usuario AND d.tipo = 1), NULL) AS celulares_asignados,
                COALESCE((SELECT GROUP_CONCAT(CONCAT(m.nombre, ' ', d.modelo) SEPARATOR ', ') FROM dispositivos d JOIN marcas m ON d.marca = m.id_marca WHERE d.usuario = u.id_usuario AND d.tipo = 2), NULL) AS laptops_asignadas
            FROM usuarios u
        """
        
        usuarios_data = self.db_manager.execute_query(base_query)
        # Si no hay usuarios, inicializamos la lista vacía para evitar el error NoneType
        if not usuarios_data:
            return []

        dispositivos_agregados = self.db_manager.execute_query(device_query)
        
        device_map = {item['id_usuario']: item for item in dispositivos_agregados}
        usuarios_list = []
        
        for data in usuarios_data:
            user = Usuario.from_dict(data)
            setattr(user, 'empresa_nombre', data.get('empresa_nombre') or 'Sin empresa')
            
            info = device_map.get(user.id_usuario, {})
            setattr(user, 'celular_info', info.get('celulares_asignados') or 'Sin celular')
            setattr(user, 'laptop_info', info.get('laptops_asignadas') or 'Sin laptop')
            
            usuarios_list.append(user)
            
        # [CORRECCIÓN CRÍTICA] El return debe estar AQUÍ, fuera del for
        return usuarios_list

    def get_usuario_by_id(self, id_usuario):
        data = self.db_manager.execute_query("SELECT * FROM usuarios WHERE id_usuario = %s", (id_usuario,))
        return Usuario.from_dict(data[0]) if data else None

    # Actualiza estas dos funciones para recibir fecha_ingreso
    def add_usuario(self, usuario: Usuario):
        # Agregamos fecha_ingreso al INSERT
        query = "INSERT INTO usuarios (empresa, nombre, apellidos, correo, fecha_ingreso) VALUES (%s, %s, %s, %s, %s)"
        return self.db_manager.execute_commit(query, (usuario.empresa, usuario.nombre, usuario.apellidos, usuario.correo, usuario.fecha_ingreso))

    def update_usuario(self, usuario: Usuario):
        # Agregamos fecha_ingreso al UPDATE
        query = "UPDATE usuarios SET empresa=%s, nombre=%s, apellidos=%s, correo=%s, fecha_ingreso=%s WHERE id_usuario=%s"
        return self.db_manager.execute_commit(query, (usuario.empresa, usuario.nombre, usuario.apellidos, usuario.correo, usuario.fecha_ingreso, usuario.id_usuario))
    
    # --- NUEVA FUNCIÓN: Obtener usuario + TODOS sus dispositivos ---
    def get_usuario_full_detail(self, id_usuario):
        # 1. Datos del usuario
        user_data = self.get_usuario_by_id(id_usuario)
        if not user_data: return None, []

        # 2. Sus dispositivos (Tablets, Laptops, Celulares... TODO)
        query_devices = """
            SELECT d.*, td.nombre as tipo_nombre, td.color as tipo_color, m.nombre as marca_nombre
            FROM dispositivos d
            JOIN tipo_dispositivo td ON d.tipo = td.id_tipo
            JOIN marcas m ON d.marca = m.id_marca
            WHERE d.usuario = %s
        """
        devices = self.db_manager.execute_query(query_devices, (id_usuario,))
        return user_data, devices
    
    def delete_usuario(self, id_usuario):
        # Al borrar usuario, desasignamos equipos
        self.db_manager.execute_commit("UPDATE dispositivos SET usuario = NULL WHERE usuario = %s", (id_usuario,))
        return self.db_manager.execute_commit("DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,))

    # --- CATÁLOGOS (ACTUALIZADOS A NUEVA BD) ---
    def get_all_tipos_dispositivo(self):
        # Ahora traemos también el color
        return self.db_manager.execute_query("SELECT id_tipo, nombre, color FROM tipo_dispositivo ORDER BY nombre")
    
    def get_all_estados(self):
        return self.db_manager.execute_query("SELECT id_status, estado, color FROM estados ORDER BY estado")

    def get_all_marcas(self):
        return self.db_manager.execute_query("SELECT id_marca, nombre FROM marcas ORDER BY nombre")
    
    def get_marcas_by_tipo(self, tipo_id):
        return self.get_all_marcas()
    
    def get_all_empresas(self):
        return self.db_manager.execute_query("SELECT id_empresa, nombre, alias FROM empresas ORDER BY nombre")

    # --- CRUD Catálogos Simples ---
    def add_estado(self, nombre, color):
        return self.db_manager.execute_commit("INSERT INTO estados (estado, color) VALUES (%s, %s)", (nombre, color))
    
    def delete_estado(self, id_status):
        return self.db_manager.execute_commit("DELETE FROM estados WHERE id_status = %s", (id_status,))

    def add_marca(self, nombre_marca): # [MODIFICADO] Quitamos parametro tipo
        return self.db_manager.execute_commit("INSERT INTO marcas (nombre) VALUES (%s)", (nombre_marca,))
    
    def delete_marca(self, id_marca):
        return self.db_manager.execute_commit("DELETE FROM marcas WHERE id_marca = %s", (id_marca,))

    def add_empresa(self, nombre, alias):
        return self.db_manager.execute_commit("INSERT INTO empresas (nombre, alias) VALUES (%s, %s)", (nombre, alias))
    
    def delete_empresa(self, id_empresa):
        return self.db_manager.execute_commit("DELETE FROM empresas WHERE id_empresa = %s", (id_empresa,))

    def update_estado(self, id_status, nombre, color):
        return self.db_manager.execute_commit("UPDATE estados SET estado = %s, color = %s WHERE id_status = %s", (nombre, color, id_status))

    def update_marca(self, id_marca, nombre_marca):
        return self.db_manager.execute_commit("UPDATE marcas SET nombre = %s WHERE id_marca = %s", (nombre_marca, id_marca))

    def update_empresa(self, id_empresa, nombre, alias):
        return self.db_manager.execute_commit("UPDATE empresas SET nombre = %s, alias = %s WHERE id_empresa = %s", (nombre, alias, id_empresa))
    
    # --- CRUD TIPOS DE DISPOSITIVO ---
    def add_tipo_dispositivo(self, nombre, color):
        return self.db_manager.execute_commit("INSERT INTO tipo_dispositivo (nombre, color) VALUES (%s, %s)", (nombre, color))

    def update_tipo_dispositivo(self, id_tipo, nombre, color):
        return self.db_manager.execute_commit("UPDATE tipo_dispositivo SET nombre = %s, color = %s WHERE id_tipo = %s", (nombre, color, id_tipo))

    def delete_tipo_dispositivo(self, id_tipo):
        return self.db_manager.execute_commit("DELETE FROM tipo_dispositivo WHERE id_tipo = %s", (id_tipo,))
    
    # --- DASHBOARD / ESTADÍSTICAS ---
    def get_dashboard_stats(self):
        stats = {}
        
        # 1. Conteo Total
        res_total = self.db_manager.execute_query("SELECT COUNT(*) as total FROM dispositivos")
        stats['total_dispositivos'] = res_total[0]['total'] if res_total else 0
        
        # 2. Conteo por Estado (Activo, Dañado, etc.)
        query_estados = """
            SELECT s.estado, COUNT(*) as total 
            FROM dispositivos d 
            JOIN estados s ON d.estado = s.id_status 
            GROUP BY s.estado
        """
        stats['por_estado'] = self.db_manager.execute_query(query_estados)
        
        # 3. Conteo por Tipo (Laptop, Celular, etc.)
        query_tipos = """
            SELECT td.nombre, td.color, COUNT(*) as total 
            FROM dispositivos d 
            JOIN tipo_dispositivo td ON d.tipo = td.id_tipo 
            GROUP BY td.nombre, td.color
        """
        stats['por_tipo'] = self.db_manager.execute_query(query_tipos)
        
        return stats
    
    # --- FINANZAS ---

    def get_financial_stats(self, year=None):
        """
        Si year es None: Devuelve gasto total por AÑO (Evolución histórica).
        Si year tiene valor: Devuelve gasto total por MES de ese año.
        """
        if year:
            # Desglose MENSUAL para un año específico
            query = """
                SELECT DATE_FORMAT(fecha_compra, '%Y-%m') as periodo, SUM(costo) as total
                FROM dispositivos
                WHERE YEAR(fecha_compra) = %s
                GROUP BY periodo
                ORDER BY periodo ASC
            """
            return self.db_manager.execute_query(query, (year,))
        else:
            # Desglose ANUAL (Histórico)
            query = """
                SELECT YEAR(fecha_compra) as periodo, SUM(costo) as total
                FROM dispositivos
                WHERE fecha_compra IS NOT NULL
                GROUP BY periodo
                ORDER BY periodo ASC
            """
            return self.db_manager.execute_query(query)
    
    def get_available_years(self):
        """Obtiene la lista de años que tienen compras registradas."""
        query = "SELECT DISTINCT YEAR(fecha_compra) as anio FROM dispositivos WHERE fecha_compra IS NOT NULL ORDER BY anio DESC"
        return self.db_manager.execute_query(query)

    def export_to_excel(self):
        """Genera un archivo Excel con dos hojas."""
        # 1. Obtener DataFrames usando Pandas y SQLAlchemy (o directo de la lista de dicts)
        users = self.get_all_usuarios() # Devuelve lista de objetos, hay que convertir a dicts
        devices = self.get_dispositivos_by_view('vw_dispositivos') # Devuelve lista de dicts
        
        # Convertir objetos Usuario a dicts para pandas
        users_data = [vars(u) for u in users] 
        
        df_users = pd.DataFrame(users_data)
        df_devices = pd.DataFrame(devices)
        
        # Limpiar columnas que no queremos exportar (opcional)
        if not df_devices.empty:
            cols_to_keep = ['id_dispositivo', 'tipo_dispositivo', 'marca', 'modelo', 'identificador', 'costo', 'fecha_compra', 'usuario', 'estado', 'empresa']
            # Filtramos solo si las columnas existen
            df_devices = df_devices[[c for c in cols_to_keep if c in df_devices.columns]]

        # Crear el Excel en memoria
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_devices.to_excel(writer, sheet_name='Dispositivos', index=False)
            df_users.to_excel(writer, sheet_name='Usuarios', index=False)
        
        output.seek(0)
        return output
    
    # --- IMPORTACIÓN MASIVA ---
    def _get_or_create_catalogo(self, tabla, campo_nombre, campo_id, valor, color_default='#9CA3AF'):
        """Busca un ID por nombre; si no existe, lo crea."""
        if not valor or pd.isna(valor): return None
        
        valor = str(valor).strip() # Limpiar espacios
        
        # 1. Buscar si existe
        query_search = f"SELECT {campo_id} FROM {tabla} WHERE {campo_nombre} = %s"
        res = self.db_manager.execute_query(query_search, (valor,))
        if res:
            return res[0][campo_id]
        
        # 2. Si no existe, crear (Manejando el color si la tabla lo pide)
        if tabla in ['tipo_dispositivo', 'estados']:
            query_insert = f"INSERT INTO {tabla} ({campo_nombre}, color) VALUES (%s, %s)"
            self.db_manager.execute_commit(query_insert, (valor, color_default))
        else:
            query_insert = f"INSERT INTO {tabla} ({campo_nombre}) VALUES (%s)"
            self.db_manager.execute_commit(query_insert, (valor,))
            
        # 3. Recuperar el ID recién creado
        res_new = self.db_manager.execute_query(query_search, (valor,))
        return res_new[0][campo_id] if res_new else None

    def importar_dispositivos_excel(self, file_storage):
        try:
            # Leemos el Excel
            df = pd.read_excel(file_storage)
            
            # Normalizamos nombres de columnas a minúsculas para evitar errores (ej: "Marca " -> "marca")
            df.columns = [c.lower().strip() for c in df.columns]
            
            # Diccionario de sinónimos (Mapea tus columnas del Excel viejo a lo que Python entiende)
            mapa = {
                'serie': 'identificador',
                's/n': 'identificador',
                'número de serie': 'identificador',
                'imei': 'identificador',
                'equipo': 'tipo',
                'tipo de dispositivo': 'tipo',
                'status': 'estado',
                'estatus': 'estado',
                'precio': 'costo',
                'importe': 'costo'
            }
            df.rename(columns=mapa, inplace=True)
            
            count = 0
            for index, row in df.iterrows():
                # Validación mínima: Debe tener Modelo
                modelo = row.get('modelo')
                if pd.isna(modelo): continue 

                # --- MAGIA: BUSCAR O CREAR IDs ---
                # Buscamos la marca por nombre (ej: "Dell"), si no existe, la crea
                marca_id = self._get_or_create_catalogo('marcas', 'nombre', 'id_marca', row.get('marca')) or 1 # 1=Genérica si falla
                
                # Buscamos el tipo (ej: "Laptop"), si no existe, lo crea con color gris
                tipo_id = self._get_or_create_catalogo('tipo_dispositivo', 'nombre', 'id_tipo', row.get('tipo')) or 2 # 2=Laptop default
                
                # Buscamos el estado (ej: "Activo"), si no existe, lo crea
                estado_id = self._get_or_create_catalogo('estados', 'estado', 'id_status', row.get('estado')) or 1 # 1=Activo default

                # Limpieza de datos (CORREGIDO)
                raw_id = row.get('identificador', '')
                identificador = str(raw_id).strip()
                
                # Truco: Si termina en .0 (ej: "12345.0"), se lo quitamos
                if identificador.endswith('.0'):
                    identificador = identificador[:-2]
                    
                if identificador == 'nan' or not identificador: 
                    identificador = 'S/N Desconocido'
                
                # Costos y Fechas
                try: costo = float(row.get('costo', 0))
                except: costo = 0.0
                
                fecha = row.get('fecha_compra')
                if pd.isna(fecha): fecha = None

                extra = row.get('especificaciones', '')
                if pd.isna(extra): extra = 'Importado masivamente'

                # Insertar
                query = """INSERT INTO dispositivos 
                           (tipo, marca, modelo, estado, identificador, costo, fecha_compra, extra_info)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
                
                self.db_manager.execute_commit(query, (tipo_id, marca_id, modelo, estado_id, identificador, costo, fecha, extra))
                count += 1
                
            return count, None
        except Exception as e:
            return 0, str(e)
    
    # --- GESTIÓN DE ACCESOS (ADMINS) ---
    def get_all_admins(self):
        return self.db_manager.execute_query("SELECT id_admin, username, role FROM administradores")

    def add_admin(self, username, password_hash, role):
        return self.db_manager.execute_commit("INSERT INTO administradores (username, password, role) VALUES (%s, %s, %s)", (username, password_hash, role))

    def delete_admin(self, id_admin):
        return self.db_manager.execute_commit("DELETE FROM administradores WHERE id_admin = %s", (id_admin,))