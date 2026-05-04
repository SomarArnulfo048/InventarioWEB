💻 Sistema de Gestión de Activos IT - Bestground International
## 1. Resumen Ejecutivo
* **Descripción:** Plataforma centralizada para el control y seguimiento de activos tecnológicos, dispositivos móviles y periféricos.
* **Problema Identificado:** Falta de control en la asignación de hardware, dificultad para rastrear cartas responsivas y necesidad de gestionar el ciclo de vida de los dispositivos.
* **Solución:** Sistema web con generación de QRs para activos, gestión de cartas responsivas digitales y vinculación de usuarios.
* **Arquitectura:** Backend en Flask (Python) y base de datos relacional en MySQL administrada con Workbench.

---

## 2. Tabla de Contenidos (ToC)
* [3. Requerimientos](#3-requerimientos)
* [4. Instalación](#4-instalación)
* [5. Configuración](#5-configuración)
* [6. Uso](#6-uso)
* [7. Contribución](#7-contribución)
* [8. Roadmap](#8-roadmap)

---

## 3. Requerimientos
* **Servidores:** Aplicación Flask y motor de base de datos MySQL.
* **Lenguaje:** Python 3.10 o superior.
* **Bibliotecas Clave:** Flask-SQLAlchemy, PyMySQL, qrcode, Flask-Login.

---

## 4. Instalación
1. Clonar el repositorio: `git clone https://github.com/SomarArnulfo048/InventarioWEB.git`
2. Instalar dependencias: `pip install -r requirements.txt`

---

## 5. Configuración
* **Base de Datos:** Importar el esquema SQL desde MySQL Workbench.
* **Variables:** Configurar credenciales en `config.py`.

---

## 6. Uso
* **Administrador:** Registro de laptops, periféricos y asignación de cartas responsivas.
* **Usuario:** Consulta de activos mediante escaneo de códigos QR.

---

## 7. Contribución
1. Clonar repositorio.
2. Crear un nuevo branch: `git checkout -b feature/mejora`.
3. Enviar Pull Request a la rama `develop`.

---

## 8. Roadmap
* Integración de cámara móvil para escaneo directo.
* Módulo de mantenimiento preventivo.