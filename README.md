💻 Sistema de Gestión de Activos IT - Bestground International
1. Resumen Ejecutivo
Descripción: Plataforma centralizada para el control y seguimiento de activos tecnológicos, dispositivos móviles y periféricos.

Problema Identificado: Falta de control en la asignación de hardware, dificultad para rastrear cartas responsivas y necesidad de gestionar el ciclo de vida de los dispositivos (laptops, PCs, celulares).

Solución: Sistema web con generación de QRs para activos, gestión de cartas responsivas digitales y vinculación de usuarios con dispositivos específicos.

Arquitectura: Backend en Flask (Python) y base de datos relacional en MySQL administrada con Workbench.

2. Tabla de Contenidos (ToC)
Requerimientos

Instalación

Configuración

Uso

Contribución

Roadmap

3. Requerimientos
Servidores: Aplicación Flask y motor de base de datos MySQL.

Lenguaje: Python 3.10 o superior.

Bibliotecas Clave: Flask-SQLAlchemy, PyMySQL (conector MySQL), qrcode (para generación de etiquetas), Flask-Login.

Hardware: Servidor local o instancia en la nube con soporte para Python.

4. Instalación
Ambiente de Desarrollo
Clonar el repositorio: git clone [https://github.com/SomarArnulfo048/InventarioWEB.git](https://github.com/SomarArnulfo048/InventarioWEB.git)

Crear entorno virtual: python -m venv venv

Activar entorno: venv\Scripts\activate

Instalar dependencias: pip install -r requirements.txt

Pruebas Manuales
Ejecutar pytest para verificar los módulos de asignación de dispositivos y validación de usuarios.

5. Configuración
Base de Datos: Ejecutar el script SQL generado en MySQL Workbench para crear las tablas de Activos, Usuarios, Responsivas y Asignaciones.

Archivos de Configuración: Ajustar las credenciales de conexión en el archivo config.py o variables de entorno.

6. Uso
Manual para Usuario Final
Escanear el Código QR del dispositivo para consultar su estado actual.

Firmar la Carta Responsiva digital al recibir un nuevo equipo asignado.

Manual para Usuario Administrador
Registro de nuevos activos (Laptops, Monitores, Impresoras, etc.).

Vinculación de dispositivos a usuarios específicos.

Generación y descarga de reportes de activos asignados y disponibles.

7. Contribución
Para colaborar en el desarrollo de nuevas funciones de IT:

Clonar el repositorio.

Crear un nuevo branch: git checkout -b feature/nueva-funcionalidad.

Enviar Pull Request detallando los cambios en la lógica de asignación o seguridad.

8. Roadmap (Futuro)
Integración de escaneo de QR mediante cámara de dispositivos móviles en tiempo real.

Módulo de tickets de soporte técnico vinculado a cada activo.

Alertas automáticas de renovación de garantía de hardware.