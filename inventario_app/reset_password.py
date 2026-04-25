from app import create_app
from app.core.services import InventarioService
from werkzeug.security import generate_password_hash

# Inicializamos la app para poder acceder a la base de datos
app = create_app()

with app.app_context():
    service = InventarioService()
    
    print("--- RESTAURADOR DE CONTRASEÑAS ---")
    usuario = input("Introduce el nombre de usuario (ej: admin o lector): ")
    nueva_pass = input("Introduce la nueva contraseña (ej: 12345): ")
    
    # 1. Buscamos si el usuario existe
    user_db = service.get_admin_by_username(usuario)
    
    if user_db:
        # 2. Generamos el hash compatible con TU computadora
        pass_hash = generate_password_hash(nueva_pass)
        
        # 3. Actualizamos la base de datos directamente
        sql = "UPDATE administradores SET password = %s WHERE username = %s"
        service.db_manager.execute_commit(sql, (pass_hash, usuario))
        
        print(f"\n¡LISTO! La contraseña de '{usuario}' ha sido actualizada correctamente.")
        print("Intenta iniciar sesión ahora.")
    else:
        print(f"\nERROR: El usuario '{usuario}' no existe en la base de datos.")