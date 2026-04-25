# Archivo: core/models.py

class Usuario:
    """Representa la tabla 'usuarios'."""
    # Agregamos fecha_ingreso al __init__
    def __init__(self, id_usuario, nombre, apellidos, correo, empresa=None, fecha_ingreso=None):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.apellidos = apellidos
        self.correo = correo
        self.empresa = empresa
        self.fecha_ingreso = fecha_ingreso # <--- ¡ESTA LÍNEA FALTABA!

    @classmethod
    def from_dict(cls, data):
        return cls(
            id_usuario=data.get('id_usuario'),
            nombre=data.get('nombre'),
            apellidos=data.get('apellidos'),
            correo=data.get('correo'),
            empresa=data.get('empresa'),
            fecha_ingreso=data.get('fecha_ingreso') # <--- Y ESTA TAMBIÉN
        )

class Dispositivo:
    def __init__(self, id_dispositivo, tipo, marca, modelo, estado, 
                 identificador=None, costo=0.0, fecha_compra=None, # <--- NUEVOS
                 extra_info=None, usuario=None, 
                 numerotel=None, plan_inicio=None, plan_fin=None):
        self.id_dispositivo = id_dispositivo
        self.tipo = tipo 
        self.marca = marca 
        self.modelo = modelo
        self.estado = estado 
        self.identificador = identificador
        self.costo = costo             # <---
        self.fecha_compra = fecha_compra # <---
        self.numerotel = numerotel
        self.plan_inicio = plan_inicio
        self.plan_fin = plan_fin
        self.extra_info = extra_info
        self.usuario = usuario 

    @classmethod
    def from_dict(cls, data):
        # ... (lógica de usuario_id igual) ...
        # Conversión segura de costo
        try: costo = float(data.get('costo') or 0.0)
        except: costo = 0.0

        return cls(
            id_dispositivo=data.get('id_dispositivo'),
            tipo=data.get('tipo'),
            marca=data.get('marca'),
            modelo=data.get('modelo'),
            estado=data.get('estado'),
            identificador=data.get('identificador') or data.get('imei') or data.get('serialnum'),
            costo=costo,            
            fecha_compra=data.get('fecha_compra'), 
            numerotel=data.get('numerotel'),
            extra_info=data.get('extra_info'),
            plan_inicio=data.get('plan_inicio'),
            plan_fin=data.get('plan_fin'),
            usuario=data.get('usuario')
        )