# /app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from xhtml2pdf import pisa
from io import BytesIO
from datetime import date
import qrcode
import pandas as pd
import socket

# Importaciones locales (usando punto relativo)
from .core.services import InventarioService, clean_input, get_id_or_none
from .core.models import Dispositivo, Usuario 

# Configuración inicial
bp = Blueprint('inventario', __name__, url_prefix='/')
service = InventarioService()

# ==========================================
#  AUTENTICACIÓN Y SEGURIDAD
# ==========================================

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('inventario.inventario_general'))
    
    if request.method == 'POST':
        username = clean_input(request.form.get('username'))
        password = clean_input(request.form.get('password'))
        
        user = service.get_admin_by_username(username)
        
        # Verificación de contraseña segura (Hash)
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Bienvenido de nuevo.', 'success')
            # Redirección inteligente (si venía de otra página)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('inventario.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
            
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada.', 'success')
    return redirect(url_for('inventario.login'))

# ==========================================
#  DASHBOARD Y FINANZAS
# ==========================================

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    try:
        stats = service.get_dashboard_stats()
        years = service.get_available_years()
        finanzas = service.get_financial_stats() # Histórico por defecto
        return render_template('dashboard.html', stats=stats, years=years, finanzas=finanzas, titulo='Panel de Control')
    except Exception as e:
        print(f"Error dashboard: {e}")
        return render_template('dashboard.html', stats={}, years=[], finanzas=[], error=str(e), titulo='Panel de Control')

@bp.route('/api/finanzas')
@login_required
def api_finanzas():
    year_input = request.args.get('year')
    target_year = int(year_input) if year_input and year_input.isdigit() else None
    
    data = service.get_financial_stats(target_year)
    
    labels = [str(d['periodo']) for d in data]
    values = [float(d['total']) for d in data]
    
    return jsonify({'labels': labels, 'data': values})

# ==========================================
#  INVENTARIO GENERAL
# ==========================================

@bp.route('/inventario_general')
@login_required
def inventario_general():
    try:
        tipos = service.get_all_tipos_dispositivo() # Para el menú de añadir
        inventario = service.get_dispositivos_by_view('vw_dispositivos')
        return render_template('inventario_general.html', 
                               inventario=inventario, 
                               tipos_disp=tipos, 
                               titulo='Inventario General')
    except Exception as e:
        print(f"Error inventario_general: {e}")
        return render_template('inventario_general.html', inventario=[], tipos_disp=[], error=str(e), titulo='Inventario General')

@bp.route('/dispositivo/add_edit/<int:tipo_id>', methods=['GET', 'POST'])
@bp.route('/dispositivo/add_edit/<int:tipo_id>/<int:id_dispositivo>', methods=['GET', 'POST'])
@login_required
def add_edit_dispositivo(tipo_id, id_dispositivo=None):
    # Seguridad: Solo admin puede editar/añadir
    if current_user.role != 'admin':
        flash('No tienes permiso para realizar esta acción.', 'error')
        return redirect(url_for('inventario.inventario_general'))

    dispositivo = service.get_dispositivo_by_id(id_dispositivo) if id_dispositivo else None
    marcas = service.get_all_marcas()
    estados = service.get_all_estados()
    usuarios = service.get_all_usuarios()
    
    if request.method == 'POST':
        try:
            costo_input = request.form.get('costo')
            fecha_input = request.form.get('fecha_compra')

            disp = Dispositivo(
                id_dispositivo=id_dispositivo, tipo=tipo_id,
                marca=get_id_or_none('marca', request.form), 
                modelo=clean_input(request.form.get('modelo')),
                estado=get_id_or_none('estado', request.form), 
                usuario=get_id_or_none('usuario', request.form),
                identificador=clean_input(request.form.get('identificador')),
                numerotel=clean_input(request.form.get('numero')), 
                extra_info=clean_input(request.form.get('extra_data')),
                plan_inicio=clean_input(request.form.get('plan_inicio')) or None, 
                plan_fin=clean_input(request.form.get('plan_fin')) or None,
                
                # Datos Financieros
                costo=float(costo_input) if costo_input else 0.0,
                fecha_compra=fecha_input if fecha_input else None
            )
            
            if id_dispositivo: service.update_dispositivo(disp)
            else: service.add_dispositivo(disp)
            
            flash('Dispositivo guardado con éxito', 'success')
            return redirect(url_for('inventario.inventario_general'))
        except Exception as e:
            print(f"Error guardando dispositivo: {e}")
            flash(f'Error al guardar: {e}', 'error')
            
    # Selección de plantilla según tipo (Celular tiene campos extra)
    template = 'celulares_add_edit.html' if tipo_id == 1 else 'laptops_add_edit.html'
    
    return render_template(template, 
                           celular=dispositivo, laptop=dispositivo, # Pasamos ambos nombres para compatibilidad
                           estados=estados, marcas=marcas, usuarios=usuarios, 
                           id_dispositivo=id_dispositivo, current_tipo=tipo_id,
                           titulo='Editar' if id_dispositivo else 'Añadir')

@bp.route('/dispositivo/delete/<int:id_dispositivo>', methods=['POST'])
@login_required
def delete_dispositivo(id_dispositivo):
    if current_user.role != 'admin': return redirect(url_for('inventario.inventario_general'))
    try: 
        service.delete_dispositivo(id_dispositivo)
        flash('Dispositivo eliminado', 'success')
    except Exception as e: 
        flash(f'Error: {e}', 'error')
    return redirect(url_for('inventario.inventario_general'))

# ==========================================
#  DETALLES Y HERRAMIENTAS (QR/PDF)
# ==========================================

@bp.route('/dispositivo/detail/<int:id_dispositivo>')
@login_required
def dispositivo_detail(id_dispositivo):
    dispositivo = service.get_dispositivo_detail(id_dispositivo)
    if not dispositivo: return redirect(url_for('inventario.inventario_general'))
    
    # Si es celular, usamos la vista especial
    if dispositivo.tipo == 1:
        return render_template('celular_detail.html', celular=dispositivo, titulo="Detalle Celular")
    
    # Vista genérica para todo lo demás
    return render_template('dispositivo_detail.html', dispositivo=dispositivo, titulo=f"Detalle {dispositivo.tipo_dispositivo}")

@bp.route('/historial/<int:id_dispositivo>')
@login_required
def ver_historial(id_dispositivo):
    try:
        dispositivo = service.get_dispositivo_by_id(id_dispositivo)
        movimientos = service.get_historial_by_device(id_dispositivo)
        return render_template('historial_list.html', movimientos=movimientos, dispositivo=dispositivo, titulo='Historial de Movimientos')
    except Exception as e:
        flash(f'Error historial: {e}', 'error')
        return redirect(url_for('inventario.inventario_general'))

@bp.route('/dispositivo/qr/<int:id_dispositivo>')
@login_required
def generar_qr(id_dispositivo):
    # 1. DETECTAR LA IP REAL DE LA MÁQUINA
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        mi_ip = s.getsockname()[0]
    except Exception:
        mi_ip = '127.0.0.1' # Fallback si no hay red
    finally:
        s.close()

    # 2. CONSTRUIR LA URL A LA FUERZA CON ESA IP
    # Obtenemos solo la parte del camino (ej: /dispositivo/detail/5)
    path = url_for('inventario.dispositivo_detail', id_dispositivo=id_dispositivo)
    
    # La pegamos manualmente con la IP detectada
    url_destino = f"http://{mi_ip}:5000{path}"
    
    # 3. Crear el QR
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url_destino)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', download_name=f'QR_{id_dispositivo}.png')

@bp.route('/dispositivo/pdf/<int:id_dispositivo>')
@login_required
def descargar_pdf(id_dispositivo):
    dispositivo = service.get_dispositivo_detail(id_dispositivo)
    if not dispositivo or not dispositivo.user_id:
        flash('No se puede generar PDF sin dispositivo o usuario asignado.', 'error')
        return redirect(url_for('inventario.inventario_general'))

    usuario_pdf = {'nombre': dispositivo.user_nombre, 'apellidos': dispositivo.user_apellidos}
    html = render_template('pdf_responsiva.html', dispositivo=dispositivo, usuario=usuario_pdf, hoy=date.today().strftime('%d/%m/%Y'))
    
    pdf_output = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_output)
    
    if not pisa_status.err:
        response = make_response(pdf_output.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Responsiva_{dispositivo.modelo}.pdf'
        return response
    
    return redirect(url_for('inventario.inventario_general'))

# ==========================================
#  USUARIOS
# ==========================================

@bp.route('/usuarios')
@login_required
def usuarios_list():
    usuarios = service.get_all_usuarios()
    return render_template('usuarios.html', usuarios=usuarios, titulo='Gestión de Usuarios')

@bp.route('/usuario/add_edit', methods=['GET', 'POST'])
@bp.route('/usuario/add_edit/<int:id_usuario>', methods=['GET', 'POST'])
@login_required
def add_edit_usuario(id_usuario=None):
    if current_user.role != 'admin':
        flash('Acceso denegado.', 'error')
        return redirect(url_for('inventario.usuarios_list'))

    usuario = service.get_usuario_by_id(id_usuario) if id_usuario else None
    empresas = service.get_all_empresas()
    
    if request.method == 'POST':
        try:
            fecha_ing = clean_input(request.form.get('fecha_ingreso'))
            user = Usuario(
                id_usuario=id_usuario, 
                nombre=clean_input(request.form.get('nombre')),
                apellidos=clean_input(request.form.get('apellidos')), 
                correo=clean_input(request.form.get('correo')),
                empresa=get_id_or_none('empresa', request.form),
                fecha_ingreso=fecha_ing if fecha_ing else None
            )
            if id_usuario: service.update_usuario(user)
            else: service.add_usuario(user)
            flash('Usuario guardado', 'success')
            return redirect(url_for('inventario.usuarios_list'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
            
    return render_template('usuarios_add_edit.html', usuario=usuario, empresas=empresas, titulo='Usuario')

@bp.route('/usuario/detail/<int:id_usuario>')
@login_required
def usuario_detail(id_usuario):
    usuario, dispositivos = service.get_usuario_full_detail(id_usuario)
    anios, progreso = 0, 0
    if usuario and usuario.fecha_ingreso:
        hoy = date.today()
        anios = hoy.year - usuario.fecha_ingreso.year - ((hoy.month, hoy.day) < (usuario.fecha_ingreso.month, usuario.fecha_ingreso.day))
        delta = hoy - usuario.fecha_ingreso
        progreso = int((delta.days % 365) / 365 * 100)
    return render_template('usuario_detail.html', usuario=usuario, dispositivos=dispositivos, anios=anios, progreso=progreso)

@bp.route('/usuario/delete/<int:id_usuario>', methods=['POST'])
@login_required
def delete_usuario(id_usuario):
    if current_user.role == 'admin':
        service.delete_usuario(id_usuario)
        flash('Usuario eliminado', 'success')
    return redirect(url_for('inventario.usuarios_list'))

# ==========================================
#  CATÁLOGOS Y ADMIN
# ==========================================

@bp.route('/catalogos/estados')
@login_required
def estados_list():
    items = service.get_all_estados()
    return render_template('catalogo_list.html', items=items, titulo='Estados', nombre_tabla='Estado', id_field='id_status', name_field='estado', base_route='inventario.estados_list')

@bp.route('/catalogos/marcas')
@login_required
def marcas_list():
    marcas = service.get_all_marcas()
    return render_template('catalogo_marcas.html', marcas=marcas, titulo='Marcas')

@bp.route('/catalogos/empresas')
@login_required
def empresas_list():
    items = service.get_all_empresas()
    return render_template('catalogo_list.html', items=items, titulo='Empresas', nombre_tabla='Empresa', id_field='id_empresa', name_field='nombre', base_route='inventario.empresas_list')

@bp.route('/catalogos/tipos')
@login_required
def tipos_list():
    items = service.get_all_tipos_dispositivo()
    return render_template('catalogo_list.html', items=items, titulo='Tipos de Dispositivo', nombre_tabla='Tipo', id_field='id_tipo', name_field='nombre', base_route='inventario.tipos_list')

@bp.route('/catalogo/add_edit/<string:table_name>/', methods=['GET', 'POST'])
@bp.route('/catalogo/add_edit/<string:table_name>/<int:item_id>', methods=['GET', 'POST'])
@login_required
def add_edit_catalogo(table_name, item_id=None):
    if current_user.role != 'admin': return redirect(url_for('inventario.inventario_general'))
    
    item = None
    if request.method == 'POST':
        try:
            nombre = clean_input(request.form.get('nombre'))
            if table_name == 'estado':
                color = clean_input(request.form.get('color'))
                if item_id: service.update_estado(item_id, nombre, color)
                else: service.add_estado(nombre, color)
                flash('Estado guardado', 'success'); return redirect(url_for('inventario.estados_list'))
            elif table_name == 'marca':
                if item_id: service.update_marca(item_id, nombre)
                else: service.add_marca(nombre)
                flash('Marca guardada', 'success'); return redirect(url_for('inventario.marcas_list'))
            elif table_name == 'empresa':
                alias = clean_input(request.form.get('alias'))
                if item_id: service.update_empresa(item_id, nombre, alias)
                else: service.add_empresa(nombre, alias)
                flash('Empresa guardada', 'success'); return redirect(url_for('inventario.empresas_list'))
            elif table_name == 'tipo':
                color = clean_input(request.form.get('color'))
                if item_id: service.update_tipo_dispositivo(item_id, nombre, color)
                else: service.add_tipo_dispositivo(nombre, color)
                flash('Tipo guardado', 'success'); return redirect(url_for('inventario.tipos_list'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
        return redirect(url_for('inventario.inventario_general'))

    # Cargar datos para editar
    if item_id:
        if table_name == 'estado': data = service.db_manager.execute_query("SELECT * FROM estados WHERE id_status=%s", (item_id,))
        elif table_name == 'marca': data = service.db_manager.execute_query("SELECT * FROM marcas WHERE id_marca=%s", (item_id,))
        elif table_name == 'empresa': data = service.db_manager.execute_query("SELECT * FROM empresas WHERE id_empresa=%s", (item_id,))
        elif table_name == 'tipo': data = service.db_manager.execute_query("SELECT * FROM tipo_dispositivo WHERE id_tipo=%s", (item_id,))
        if data: item = data[0]

    template_map = {
        'empresa': 'catalogo_empresas_add_edit.html',
        'marca': 'catalogo_marcas_add_edit.html',
        'tipo': 'catalogo_tipos_add_edit.html',
        'estado': 'catalogo_estados_add_edit.html'
    }
    template_name = template_map.get(table_name, 'catalogo_add_edit.html')
    return render_template(template_name, item=item, titulo='Editar' if item_id else 'Añadir', nombre_tabla=table_name.capitalize(), name_field='nombre' if table_name != 'estado' else 'estado', base_route=f'inventario.{table_name}s_list')

@bp.route('/catalogo/delete/<string:table_name>/<int:item_id>', methods=['POST'])
@login_required
def delete_catalogo(table_name, item_id):
    if current_user.role == 'admin':
        try:
            if table_name == 'marca': service.delete_marca(item_id); url = 'marcas_list'
            elif table_name == 'empresa': service.delete_empresa(item_id); url = 'empresas_list'
            elif table_name == 'estado': service.delete_estado(item_id); url = 'estados_list'
            elif table_name == 'tipo': service.delete_tipo_dispositivo(item_id); url = 'tipos_list'
            flash('Elemento eliminado', 'success')
            return redirect(url_for(f'inventario.{url}'))
        except Exception as e: flash(f'Error: {e}', 'error')
    return redirect(url_for('inventario.inventario_general'))

# --- EXCEL ---
@bp.route('/exportar_excel')
@login_required
def exportar_excel():
    try:
        excel_file = service.export_to_excel()
        return send_file(excel_file, download_name="Inventario_Completo.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    except Exception as e:
        flash(f'Error exportando: {e}', 'error')
        return redirect(url_for('inventario.inventario_general'))

@bp.route('/importar_excel', methods=['POST'])
@login_required
def importar_excel():
    if current_user.role != 'admin': return redirect(url_for('inventario.inventario_general'))
    if 'file' not in request.files: return redirect(url_for('inventario.inventario_general'))
    
    file = request.files['file']
    if file and file.filename.endswith(('.xlsx', '.xls')):
        count, error = service.importar_dispositivos_excel(file)
        if error: flash(f'Error: {error}', 'error')
        else: flash(f'Se importaron {count} dispositivos.', 'success')
    return redirect(url_for('inventario.inventario_general'))

# --- GESTIÓN DE ACCESOS ---
@bp.route('/config/accesos', methods=['GET', 'POST'])
@login_required
def gestion_accesos():
    if current_user.role != 'admin': return redirect(url_for('inventario.inventario_general'))

    if request.method == 'POST':
        try:
            username = clean_input(request.form.get('username'))
            password = clean_input(request.form.get('password'))
            role = clean_input(request.form.get('role'))
            pass_hash = generate_password_hash(password)
            service.add_admin(username, pass_hash, role)
            flash('Usuario agregado.', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'error')
            
    admins = service.get_all_admins()
    return render_template('gestion_accesos.html', admins=admins, titulo='Gestión de Accesos')

@bp.route('/config/accesos/delete/<int:id_admin>', methods=['POST'])
@login_required
def delete_admin_user(id_admin):
    if current_user.role == 'admin' and int(id_admin) != int(current_user.id):
        service.delete_admin(id_admin)
        flash('Usuario eliminado.', 'success')
    return redirect(url_for('inventario.gestion_accesos'))