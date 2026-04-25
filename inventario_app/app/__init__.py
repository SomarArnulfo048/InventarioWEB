# inventario_app/app/__init__.py

import os
from datetime import timedelta
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from .core.services import InventarioService

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    
    # CLAVE SECRETA (Necesaria para firmar las cookies de sesión)
    app.config.from_mapping(
        SECRET_KEY='dev_clave_secreta_muy_segura', # ¡Cámbiala en producción!
        PERMANENT_SESSION_LIFETIME=timedelta(hours=1) # <--- AQUÍ ESTÁ TU REGLA DE 1 HORA
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # --- CONFIGURACIÓN DE LOGIN ---
    login_manager = LoginManager()
    login_manager.login_view = 'inventario.login' # Si no estás logueado, te manda aquí
    login_manager.init_app(app)
    
    # Esta función le dice a Flask cómo cargar al usuario desde la cookie
    @login_manager.user_loader
    def load_user(user_id):
        service = InventarioService()
        return service.get_admin_by_id(user_id)

    from . import routes
    app.register_blueprint(routes.bp)

    return app