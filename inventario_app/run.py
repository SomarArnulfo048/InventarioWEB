# Archivo: run.py 
import sys
import traceback
import os

try:
    from app import create_app
    from app.core.services import InventarioService
    from werkzeug.security import generate_password_hash

    app = create_app()

    def inicializar_admin_por_defecto():
        with app.app_context():
            service = InventarioService()
            try:
                admins = service.get_all_admins()
                if not admins:
                    print("--- Creando usuario 'admin' por defecto... ---")
                    pass_hash = generate_password_hash('admin123')
                    service.add_admin('admin', pass_hash, 'admin') 
                    print("--- ¡LISTO! Usuario creado ---")
            except Exception as e:
                print(f"Nota BD: {e}")

    if __name__ == '__main__':
        print("--- INICIANDO SISTEMA BETTERDATAIT ---")
        inicializar_admin_por_defecto()
        # host='0.0.0.0' hace que sea visible en la red
        app.run(host='0.0.0.0', port=5000, debug=False)

except Exception:
    # SI ALGO FALLA, GUARDAMOS EL ERROR EN UN ARCHIVO
    with open("log_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("¡OCURRIÓ UN ERROR FATAL!")
    print("Revisa el archivo 'log_error.txt' que se acaba de crear.")
    input("Presiona ENTER para salir...") # Esto evita que se cierre la ventana