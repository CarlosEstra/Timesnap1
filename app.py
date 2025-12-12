from flask import Flask, request, jsonify, session, send_from_directory
from datetime import datetime, timedelta, date
import base64
import io
from flask_cors import CORS
from db_connection import get_db_connection

# Inicialización de la aplicación Flask
app = Flask(__name__)

# --- CONFIGURACIÓN CORS CON COOKIES ---
# Permitir múltiples orígenes para desarrollo local
CORS(app, supports_credentials=True, origins=[
    'http://127.0.0.1:5500', 'http://localhost:5500',  # Live Server VS Code
    'http://127.0.0.1:3000', 'http://localhost:3000',  # Otros puertos comunes
    'http://127.0.0.1:8000', 'http://localhost:8000',
    'http://127.0.0.1:5000', 'http://localhost:5000',  # Nuestro Flask server
    'http://127.0.0.1:5001', 'http://localhost:5001'   # Registration server
])

# --- CONFIGURACIÓN DE SESIÓN ---
# ⚠️ Cambia esta clave. Necesaria para Flask Sessions.
app.secret_key = '123456789'

# Configuración adicional para sesiones
app.config['SESSION_COOKIE_SECURE'] = False  # Para desarrollo local
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora

# ----------------------------------------------------------------------
# 2. Ruta de Login por ID y Contraseña
# ----------------------------------------------------------------------

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    # El JS envía 'employeeNumber' como 'username'. Lo trataremos como el ID del empleado.
    employee_id = data.get('username') 
    password = data.get('password')
    
    if not employee_id or not password:
        return jsonify({'success': False, 'message': 'Faltan credenciales.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True) 
    try:
        # 1. Búsqueda directa por id_empleado y password
        # La consulta usa los campos EXACTOS de la tabla: id_empleado y password (texto plano)
        sql = "SELECT id_empleado, nombre, id_puestos FROM empleados WHERE id_empleado = %s AND contrasena = %s"
        mycursor.execute(sql, (employee_id, password)) 
        empleado = mycursor.fetchone()

        if empleado:
            # 2. Éxito: Crear la sesión
            session.clear() 
            session['logged_in'] = True
            session['user_id'] = empleado['id_empleado']
            session['username'] = empleado['nombre']
            session['puesto'] = empleado['id_puestos']
            
            response_data = {
                'success': True,
                'message': f'Bienvenido(a), {empleado["nombre"]}.',
                'user_id': empleado['id_empleado'],
                'puesto': empleado['id_puestos']
            }
            print(f"Login exitoso para {empleado['nombre']}, puesto: {empleado['id_puestos']}")
            return jsonify(response_data)
        
        else:
            return jsonify({'success': False, 'message': 'ID de empleado o contraseña incorrectos.'}), 401

    except Exception as err:
        return jsonify({'success': False, 'message': f'Error DB: {str(err)}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

# ----------------------------------------------------------------------
# 3. RUTA PROTEGIDA: DASHBOARD
# ----------------------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    # 1. Verificar si el usuario ha iniciado sesión
    if not session.get('logged_in'):
        return jsonify({'message': 'Acceso denegado. Por favor, inicia sesión.'}), 403
    
    # 2. Si ha iniciado sesión, mostrar contenido o renderizar template
    user_name = session.get('username', 'Usuario Desconocido')
    puesto = session.get('puesto', 'N/A')
    
    # ⚠️ En una aplicación real, se enviaría el archivo HTML: render_template('dashboard.html')
    return jsonify({
        'message': f'Acceso al Dashboard concedido. ¡Hola, {user_name}!',
        'user_id': session.get('user_id'),
        'puesto': puesto,
        'status': 'logged_in'
    })


# ----------------------------------------------------------------------
# --- RUTAS DE NEGOCIO (Las mismas que ya tienes) ---
# ----------------------------------------------------------------------

@app.route('/registrar_empleado', methods=['POST'])
def registrar_empleado():
    # Requiere login. Puedes añadir lógica para verificar el puesto del empleado (e.g., si es Admin).
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Acceso denegado. Inicia sesión.'}), 403 

    # Lógica de registro de empleados...
    return jsonify({'success': True, 'message': f'Registro de empleado (SIMULACIÓN).'})

@app.route('/registrar_asistencia', methods=['POST'])
def registrar_asistencia():
    # Obtener user_id de múltiples fuentes para mayor compatibilidad
    user_id = None

    # Primero intentar de la sesión
    if session.get('logged_in'):
        user_id = session.get('user_id')

    # Si no hay sesión, intentar del header (enviado por JavaScript)
    if not user_id:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            user_id = auth_header.replace('Bearer ', '')

    # Si aún no hay user_id, intentar del body
    if not user_id:
        data = request.json or {}
        user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'Usuario no autenticado.'}), 401

    data = request.json
    tipo = data.get('tipo')  # 'entrada' o 'salida'
    empleado_id = data.get('empleado_id')

    if not tipo or not empleado_id:
        return jsonify({'success': False, 'message': 'Faltan datos requeridos.'}), 400

    if tipo not in ['entrada', 'salida']:
        return jsonify({'success': False, 'message': 'Tipo de asistencia inválido.'}), 400

    # Verificar que el empleado_id coincide con el user_id (seguridad)
    if str(empleado_id) != str(user_id):
        return jsonify({'success': False, 'message': 'No tienes permiso para registrar asistencia de otro empleado.'}), 403

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor()
    try:
        # Verificar que el empleado existe
        mycursor.execute("SELECT nombre FROM empleados WHERE id_empleado = %s", (empleado_id,))
        empleado = mycursor.fetchone()

        if not empleado:
            return jsonify({'success': False, 'message': 'Empleado no encontrado.'}), 404

        # Obtener fecha y hora actual
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        hora_actual = datetime.now().strftime('%H:%M:%S')

        # Verificar si ya existe un registro para hoy del mismo tipo
        mycursor.execute("""
            SELECT id_registro FROM registros_asistencia
            WHERE id_empleado = %s AND fecha = %s AND tipo = %s
        """, (empleado_id, fecha_actual, tipo))

        registro_existente = mycursor.fetchone()

        if registro_existente:
            return jsonify({
                'success': False,
                'message': f'Ya existe un registro de {tipo} para hoy.'
            }), 409

        # Insertar nuevo registro de asistencia
        sql = """
        INSERT INTO registros_asistencia (id_empleado, tipo, fecha, hora)
        VALUES (%s, %s, %s, %s)
        """
        val = (empleado_id, tipo, fecha_actual, hora_actual)
        mycursor.execute(sql, val)
        mydb.commit()

        return jsonify({
            'success': True,
            'message': f'{tipo.capitalize()} registrada correctamente.',
            'empleado': empleado[0],  # nombre
            'fecha': fecha_actual,
            'hora': hora_actual
        })

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()
    
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Sesión cerrada.'})

# ----------------------------------------------------------------------
# RUTAS DE REGISTRO DE EMPLEADOS (de registroweb.py)
# ----------------------------------------------------------------------

@app.route('/get_sucursales', methods=['GET'])
def get_sucursales():
    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        mycursor.execute("SELECT id_sucursal, nombre FROM sucursal")
        sucursales = mycursor.fetchall()
        return jsonify({'success': True, 'sucursales': sucursales})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_puestos', methods=['GET'])
def get_puestos():
    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        mycursor.execute("SELECT id_puestos, nombre_puestos FROM puestos")
        puestos = mycursor.fetchall()
        return jsonify({'success': True, 'puestos': puestos})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/agregar_sucursal', methods=['POST'])
def agregar_sucursal():
    data = request.json
    nombre = data.get('nombre')
    if not nombre:
        return jsonify({'success': False, 'message': 'Nombre de sucursal requerido.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor()
    try:
        # Generar ID de sucursal
        mycursor.execute("SELECT MAX(CAST(id_sucursal AS UNSIGNED)) FROM sucursal")
        max_id = mycursor.fetchone()[0] or 0
        id_sucursal = str(max_id + 1)

        # Valores por defecto para otros campos
        direccion = 'Dirección por definir'
        calle = None
        colonia = 'Colonia por definir'
        cp = '00000'

        sql = """
        INSERT INTO sucursal (id_sucursal, nombre, direccion, calle, colonia, cp)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        val = (id_sucursal, nombre, direccion, calle, colonia, cp)
        mycursor.execute(sql, val)
        mydb.commit()

        return jsonify({'success': True, 'message': f'Sucursal "{nombre}" agregada con ID {id_sucursal}', 'id_sucursal': id_sucursal})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error al agregar sucursal: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/agregar_puesto', methods=['POST'])
def agregar_puesto():
    data = request.json
    nombre_puestos = data.get('nombre')
    if not nombre_puestos:
        return jsonify({'success': False, 'message': 'Nombre del puesto requerido.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor()
    try:
        # Generar ID de puesto
        mycursor.execute("SELECT MAX(CAST(id_puestos AS UNSIGNED)) FROM puestos")
        max_id = mycursor.fetchone()[0] or 0
        id_puestos = str(max_id + 1)

        sql = "INSERT INTO puestos (id_puestos, nombre_puestos) VALUES (%s, %s)"
        val = (id_puestos, nombre_puestos)
        mycursor.execute(sql, val)
        mydb.commit()

        return jsonify({'success': True, 'message': f'Puesto "{nombre_puestos}" agregado con ID {id_puestos}', 'id_puestos': id_puestos})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error al agregar puesto: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/registrar_empleado_real', methods=['POST'])
def registrar_empleado_real():
    data = request.json
    nombre = data.get('nombre')
    apellido1 = data.get('apellidoP')
    apellido2 = data.get('apellidoM')
    id_sucursal = data.get('sucursal')
    puesto_name = data.get('puesto')  # Nombre del puesto
    hora_entrada_puesto = data.get('horaEntrada')
    hora_salida_puesto = data.get('horaSalida')
    hora_comida_entrada = data.get('comidaEntrada')
    hora_comida_salida = data.get('comidaSalida')
    face_descriptor = data.get('faceDescriptor')  # Descriptor facial
    photoData = data.get('photoData')  # Datos de la foto

    print(f'📥 Datos recibidos - faceDescriptor: {"Presente" if face_descriptor else "Nulo"}')
    if face_descriptor:
        print(f'   Longitud del descriptor: {len(face_descriptor)}')
    if photoData:
        print(f'   Datos de foto: {photoData[:50]}...')

    if not all([nombre, apellido1, id_sucursal, puesto_name]):
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor()
    try:
        # Generar ID de empleado (incremento simple)
        mycursor.execute("SELECT MAX(CAST(id_empleado AS UNSIGNED)) FROM empleados")
        max_id = mycursor.fetchone()[0] or 0
        id_empleado = str(max_id + 1)

        # Obtener ID del puesto por nombre
        mycursor.execute("SELECT id_puestos FROM puestos WHERE nombre_puestos = %s", (puesto_name,))
        puesto_row = mycursor.fetchone()
        if not puesto_row:
            return jsonify({'success': False, 'message': 'Puesto no encontrado.'}), 400
        id_puestos = puesto_row[0]

        # Contraseña del formulario
        contraseña = data.get('contrasena', '1234')

        # Preparar fotoperfil: guardar descriptor y foto separados por delimitador
        import json
        if face_descriptor:
            fotoperfil = json.dumps(face_descriptor)
            if photoData:
                fotoperfil += '|||DELIMITER|||' + photoData
        else:
            fotoperfil = photoData if photoData else None

        sql = """
        INSERT INTO empleados
        (id_empleado, fotoperfil, nombre, apellido1, apellido2, hora_comida_entrada, hora_comida_salida,
         hora_entrada_puesto, hora_salida_puesto, id_puestos, id_sucursal, contrasena)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        val = (id_empleado, fotoperfil, nombre, apellido1, apellido2 or None, hora_comida_entrada or None,
               hora_comida_salida or None, hora_entrada_puesto or None, hora_salida_puesto or None,
               id_puestos, id_sucursal, contraseña)

        mycursor.execute(sql, val)
        mydb.commit()

        return jsonify({'success': True, 'message': f'Empleado {nombre} registrado con ID {id_empleado}. Contraseña: {contraseña}'})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error al registrar: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_empleados_facial', methods=['GET'])
def get_empleados_facial():
    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        mycursor.execute("SELECT id_empleado, nombre, fotoperfil FROM empleados WHERE fotoperfil IS NOT NULL")
        empleados_raw = mycursor.fetchall()

        empleados = []
        for emp in empleados_raw:
            # Extraer el descriptor del fotoperfil
            if emp['fotoperfil']:
                descriptor = emp['fotoperfil'].split('|||DELIMITER|||')[0] if '|||DELIMITER|||' in emp['fotoperfil'] else emp['fotoperfil']
                empleados.append({
                    'id_empleado': emp['id_empleado'],
                    'nombre': emp['nombre'],
                    'fotoperfil': descriptor
                })

        return jsonify({'success': True, 'empleados': empleados})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_todos_empleados', methods=['GET'])
def get_todos_empleados():
    # Obtener parámetros de filtro
    puesto_filtro = request.args.get('puesto', '')
    sucursal_filtro = request.args.get('sucursal', '')

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        # Consulta que obtiene empleados con información de puesto y sucursal
        query = """
        SELECT
            e.id_empleado,
            CONCAT(e.nombre, ' ', COALESCE(e.apellido1, ''), ' ', COALESCE(e.apellido2, '')) as nombre_completo,
            COALESCE(p.nombre_puestos, 'Sin puesto') as puesto,
            COALESCE(s.nombre, 'Sin sucursal') as sucursal,
            '' as estado_facial
        FROM empleados e
        LEFT JOIN puestos p ON e.id_puestos = p.id_puestos
        LEFT JOIN sucursal s ON e.id_sucursal = s.id_sucursal
        """

        # Construir condiciones WHERE dinámicamente
        conditions = []
        params = []

        if puesto_filtro:
            conditions.append("p.nombre_puestos = %s")
            params.append(puesto_filtro)

        if sucursal_filtro:
            conditions.append("s.nombre = %s")
            params.append(sucursal_filtro)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY e.nombre ASC"

        mycursor.execute(query, params)
        empleados = mycursor.fetchall()

        # Formatear los datos para el frontend
        empleados_formateados = []
        for emp in empleados:
            empleados_formateados.append({
                'id': emp['id_empleado'],
                'nombre': emp['nombre_completo'].strip(),
                'puesto': emp['puesto'],
                'sucursal': emp['sucursal'],
                'fecha': 'N/A',  # Fecha de registro no disponible en la tabla
                'horas': 'N/A',  # Por ahora no calculamos horas
                'estado': emp['estado_facial'],
                'observaciones': ''
            })

        return jsonify({'success': True, 'empleados': empleados_formateados})

    except Exception as err:
        return jsonify({'success': False, 'message': f'Error DB: {str(err)}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/eliminar_empleados', methods=['POST'])
def eliminar_empleados():
    data = request.json
    empleados_ids = data.get('empleados_ids', [])

    if not empleados_ids or not isinstance(empleados_ids, list):
        return jsonify({'success': False, 'message': 'IDs de empleados requeridos.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor()
    try:
        # Eliminar también los registros de asistencia relacionados
        empleados_ids_str = ','.join(['%s'] * len(empleados_ids))

        # Primero eliminar registros de asistencia
        mycursor.execute(f"DELETE FROM registros_asistencia WHERE id_empleado IN ({empleados_ids_str})", empleados_ids)

        # Luego eliminar empleados
        mycursor.execute(f"DELETE FROM empleados WHERE id_empleado IN ({empleados_ids_str})", empleados_ids)

        mydb.commit()

        empleados_eliminados = mycursor.rowcount
        return jsonify({
            'success': True,
            'message': f'{empleados_eliminados} empleado(s) eliminado(s) correctamente.',
            'eliminados': empleados_eliminados
        })

    except mysql.connector.Error as err:
        mydb.rollback()
        return jsonify({'success': False, 'message': f'Error al eliminar: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_empleado_detalle/<empleado_id>', methods=['GET'])
def get_empleado_detalle(empleado_id):
    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        # Consulta detallada del empleado
        query = """
        SELECT
            e.id_empleado,
            e.nombre,
            e.apellido1,
            e.apellido2,
            e.hora_entrada_puesto,
            e.hora_salida_puesto,
            e.hora_comida_entrada,
            e.hora_comida_salida,
            e.id_puestos,
            e.id_sucursal,
            e.fotoperfil,
            p.nombre_puestos as puesto_nombre,
            s.nombre as sucursal_nombre
        FROM empleados e
        LEFT JOIN puestos p ON e.id_puestos = p.id_puestos
        LEFT JOIN sucursal s ON e.id_sucursal = s.id_sucursal
        WHERE e.id_empleado = %s
        """

        mycursor.execute(query, (empleado_id,))
        empleado = mycursor.fetchone()

        if empleado:
            # Handle fotoperfil - extraer imagen si está presente
            fotoperfil_data = None
            if empleado['fotoperfil']:
                fotoperfil_str = empleado['fotoperfil']
                if isinstance(fotoperfil_str, str):
                    # Si contiene delimitador, tomar la parte de imagen (después del delimitador)
                    if '|||DELIMITER|||' in fotoperfil_str:
                        parts = fotoperfil_str.split('|||DELIMITER|||')
                        if len(parts) > 1:
                            image_part = parts[1]
                            if image_part.startswith('data:image'):
                                fotoperfil_data = image_part
                    # Si es solo imagen data:image, devolverla
                    elif fotoperfil_str.startswith('data:image'):
                        fotoperfil_data = fotoperfil_str
                    # Si no es imagen, no devolver nada (es descriptor)
                try:
                    # For legacy BLOB data, encode to base64 image URL
                    fotoperfil_bytes = bytes(empleado['fotoperfil'])
                    fotoperfil_b64 = base64.b64encode(fotoperfil_bytes).decode('utf-8')
                    fotoperfil_data = f"data:image/jpeg;base64,{fotoperfil_b64}"
                except Exception as e:
                    # If encoding fails, skip
                    print(f"Error encoding fotoperfil: {e}")

            return jsonify({
                'success': True,
                'empleado': {
                    'id': empleado['id_empleado'],
                    'nombre': empleado['nombre'],
                    'apellido1': empleado['apellido1'],
                    'apellido2': empleado['apellido2'] or '',
                    'hora_entrada': str(empleado['hora_entrada_puesto']) if empleado['hora_entrada_puesto'] else '',
                    'hora_salida': str(empleado['hora_salida_puesto']) if empleado['hora_salida_puesto'] else '',
                    'comida_entrada': str(empleado['hora_comida_entrada']) if empleado['hora_comida_entrada'] else '',
                    'comida_salida': str(empleado['hora_comida_salida']) if empleado['hora_comida_salida'] else '',
                    'id_puesto': empleado['id_puestos'],
                    'puesto': empleado['puesto_nombre'],
                    'id_sucursal': empleado['id_sucursal'],
                    'sucursal': empleado['sucursal_nombre'],
                    'fotoperfil': fotoperfil_data
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Empleado no encontrado.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/actualizar_empleado', methods=['POST'])
def actualizar_empleado():
    data = request.json
    empleado_id = data.get('id')

    if not empleado_id:
        return jsonify({'success': False, 'message': 'ID de empleado requerido.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor()
    try:
        # Verificar que el empleado existe
        mycursor.execute("SELECT nombre FROM empleados WHERE id_empleado = %s", (empleado_id,))
        empleado_actual = mycursor.fetchone()
        if not empleado_actual:
            return jsonify({'success': False, 'message': 'Empleado no encontrado.'}), 404

        # Construir consulta de actualización dinámica
        campos_actualizar = []
        valores = []

        # Solo actualizar campos que se enviaron
        if 'nombre' in data:
            campos_actualizar.append("nombre = %s")
            valores.append(data['nombre'])

        if 'apellidoP' in data:
            campos_actualizar.append("apellido1 = %s")
            valores.append(data['apellidoP'])

        if 'apellidoM' in data:
            campos_actualizar.append("apellido2 = %s")
            valores.append(data['apellidoM'] or None)

        if 'sucursal' in data:
            campos_actualizar.append("id_sucursal = %s")
            valores.append(data['sucursal'])

        if 'puesto' in data:
            # Obtener ID del puesto por nombre
            mycursor.execute("SELECT id_puestos FROM puestos WHERE nombre_puestos = %s", (data['puesto'],))
            puesto_row = mycursor.fetchone()
            if not puesto_row:
                return jsonify({'success': False, 'message': 'Puesto no encontrado.'}), 400
            campos_actualizar.append("id_puestos = %s")
            valores.append(puesto_row[0])

        if 'horaEntrada' in data:
            campos_actualizar.append("hora_entrada_puesto = %s")
            valores.append(data['horaEntrada'] or None)

        if 'horaSalida' in data:
            campos_actualizar.append("hora_salida_puesto = %s")
            valores.append(data['horaSalida'] or None)

        if 'comidaEntrada' in data:
            campos_actualizar.append("hora_comida_entrada = %s")
            valores.append(data['comidaEntrada'] or None)

        if 'comidaSalida' in data:
            campos_actualizar.append("hora_comida_salida = %s")
            valores.append(data['comidaSalida'] or None)

        if not campos_actualizar:
            return jsonify({'success': False, 'message': 'No hay campos para actualizar.'}), 400

        # Construir y ejecutar consulta
        sql = f"UPDATE empleados SET {', '.join(campos_actualizar)} WHERE id_empleado = %s"
        valores.append(empleado_id)

        mycursor.execute(sql, valores)
        mydb.commit()

        if mycursor.rowcount > 0:
            return jsonify({
                'success': True,
                'message': f'Empleado actualizado correctamente.'
            })
        else:
            return jsonify({'success': False, 'message': 'No se pudo actualizar el empleado.'}), 404

    except Exception as err:
        mydb.rollback()
        return jsonify({'success': False, 'message': f'Error al actualizar: {str(err)}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/refresh_session', methods=['POST'])
def refresh_session():
    data = request.json
    user_id = data.get('user_id')

    print(f'🔄 Petición refresh_session recibida para user_id: {user_id}')

    if not user_id:
        print('❌ No se recibió user_id')
        return jsonify({'success': False, 'message': 'ID de usuario requerido.'}), 400

    # Verificar que el usuario existe en la base de datos
    mydb = get_db_connection()
    if not mydb:
        print('❌ Error de conexión DB')
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        print(f'🔍 Buscando empleado con ID: {user_id}')
        mycursor.execute("SELECT id_empleado, nombre, id_puestos FROM empleados WHERE id_empleado = %s", (user_id,))
        empleado = mycursor.fetchone()

        if empleado:
            print(f'✅ Empleado encontrado: {empleado["nombre"]}')
            # Recrear la sesión de Flask
            session.clear()
            session['logged_in'] = True
            session['user_id'] = empleado['id_empleado']
            session['username'] = empleado['nombre']
            session['puesto'] = str(empleado['id_puestos'])

            print('✅ Sesión recreada exitosamente')
            return jsonify({'success': True, 'message': 'Sesión refrescada.'})
        else:
            print(f'❌ Empleado no encontrado con ID: {user_id}')
            return jsonify({'success': False, 'message': 'Usuario no encontrado.'}), 404

    except mysql.connector.Error as err:
        print(f'❌ Error DB: {err}')
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_empleado_facial_actual', methods=['GET'])
def get_empleado_facial_actual():
    # Intentar obtener user_id de la sesión primero
    user_id = session.get('user_id')

    # Si no hay sesión, intentar obtener user_id del parámetro de query
    if not user_id:
        user_id = request.args.get('user_id')

    # Si aún no hay user_id, intentar obtenerlo del header personalizado
    if not user_id:
        user_id = request.headers.get('X-User-ID')

    if not user_id:
        return jsonify({'success': False, 'message': 'Usuario no autenticado o ID no proporcionado.'}), 401

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error de conexión DB.'}), 503

    mycursor = mydb.cursor(dictionary=True)
    try:
        mycursor.execute("SELECT id_empleado, nombre, fotoperfil FROM empleados WHERE id_empleado = %s AND fotoperfil IS NOT NULL", (user_id,))
        empleado = mycursor.fetchone()

        if empleado:
            # Extraer el descriptor del fotoperfil (parámetro antes de delimitador)
            descriptor = empleado['fotoperfil'].split('|||DELIMITER|||')[0] if '|||DELIMITER|||' in empleado['fotoperfil'] else empleado['fotoperfil']
            empleado_result = {
                'id_empleado': empleado['id_empleado'],
                'nombre': empleado['nombre'],
                'fotoperfil': descriptor  # Solo el descriptor para reconocimiento facial
            }
            return jsonify({'success': True, 'empleado': empleado_result})
        else:
            return jsonify({'success': False, 'message': 'Empleado no encontrado o sin datos faciales.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_notificaciones_retrasos', methods=['POST'])
def get_notificaciones_retrasos():
    data = request.json
    filtro = data.get('filtro')  # 'hoy', 'semana', 'quincena'

    hoy = date.today()
    fecha_inicio = hoy
    fecha_fin = hoy

    # 1. Definir rangos de fecha
    if filtro == 'hoy':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif filtro == 'semana':
        # Asumiendo que la semana empieza el Lunes (0)
        start_delta = hoy.weekday()
        fecha_inicio = hoy - timedelta(days=start_delta)
        fecha_fin = fecha_inicio + timedelta(days=6)
    elif filtro == 'quincena':
        # Lógica corregida: Mostrar la quincena pasada completa
        if hoy.day > 15:
            # Estamos en segunda quincena, mostrar primera quincena del mes actual
            fecha_inicio = date(hoy.year, hoy.month, 1)
            fecha_fin = date(hoy.year, hoy.month, 15)
        else:
            # Estamos en primera quincena, mostrar segunda quincena del mes anterior
            primer_dia_mes = date(hoy.year, hoy.month, 1)
            ultimo_dia_mes_anterior = primer_dia_mes - timedelta(days=1)
            fecha_inicio = date(ultimo_dia_mes_anterior.year, ultimo_dia_mes_anterior.month, 16)
            fecha_fin = ultimo_dia_mes_anterior

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error DB'}), 500

    mycursor = mydb.cursor(dictionary=True)

    try:
        # Consulta para obtener retrasos de llegada (sin duplicados)
        sql = """
            SELECT DISTINCT
                e.id_empleado,
                CONCAT(e.nombre, ' ', COALESCE(e.apellido1, ''), ' ', COALESCE(e.apellido2, '')) as nombre_completo,
                COALESCE(p.nombre_puestos, 'Sin puesto') as puesto,
                COALESCE(s.nombre, 'Sin sucursal') as sucursal,
                ra.fecha,
                ra.hora as hora_entrada_real,
                e.hora_entrada_puesto as hora_entrada_oficial,
                TIMESTAMPDIFF(MINUTE, e.hora_entrada_puesto, ra.hora) as minutos_retraso
            FROM empleados e
            LEFT JOIN puestos p ON e.id_puestos = p.id_puestos
            LEFT JOIN sucursal s ON e.id_sucursal = s.id_sucursal
            INNER JOIN registros_asistencia ra ON ra.id_empleado = e.id_empleado
                AND ra.tipo = 'entrada'
                AND ra.fecha BETWEEN %s AND %s
            WHERE ra.hora IS NOT NULL
                AND e.hora_entrada_puesto IS NOT NULL
                AND ra.hora > e.hora_entrada_puesto
            ORDER BY ra.fecha DESC, minutos_retraso DESC
        """

        mycursor.execute(sql, (fecha_inicio, fecha_fin))
        retrasos = mycursor.fetchall()

        # Formatear fechas para enviarlas al frontend
        rango_texto = f"{fecha_inicio.strftime('%d/%m/%Y')}"
        if filtro != 'hoy':
            rango_texto += f" al {fecha_fin.strftime('%d/%m/%Y')}"

        # Formatear retrasos para el frontend
        retrasos_formateados = []
        for retraso in retrasos:
            horas_retraso = retraso['minutos_retraso'] // 60
            minutos_retraso = retraso['minutos_retraso'] % 60

            tiempo_retraso_texto = ""
            if horas_retraso > 0:
                tiempo_retraso_texto += f"{horas_retraso}h "
            if minutos_retraso > 0:
                tiempo_retraso_texto += f"{minutos_retraso}min"

            retrasos_formateados.append({
                'id_empleado': retraso['id_empleado'],
                'nombre': retraso['nombre_completo'].strip(),
                'puesto': retraso['puesto'],
                'sucursal': retraso['sucursal'],
                'fecha': retraso['fecha'].strftime('%d/%m/%Y') if retraso['fecha'] else '',
                'hora_entrada_real': str(retraso['hora_entrada_real']) if retraso['hora_entrada_real'] else '',
                'hora_entrada_oficial': str(retraso['hora_entrada_oficial']) if retraso['hora_entrada_oficial'] else '',
                'minutos_retraso': retraso['minutos_retraso'],
                'tiempo_retraso': tiempo_retraso_texto.strip()
            })

        return jsonify({
            'success': True,
            'retrasos': retrasos_formateados,
            'rango_fecha': rango_texto,
            'total_retrasos': len(retrasos_formateados)
        })

    except Exception as err:
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_retrasos_rango', methods=['POST'])
def get_retrasos_rango():
    data = request.json
    fecha_inicio = data.get('fecha_inicio')
    fecha_fin = data.get('fecha_fin')

    if not fecha_inicio or not fecha_fin:
        return jsonify({'success': False, 'message': 'Fechas requeridas.'}), 400

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error DB'}), 500

    mycursor = mydb.cursor(dictionary=True)

    try:
        # Consulta para obtener retrasos en el rango de fechas
        sql = """
            SELECT DISTINCT
                e.id_empleado,
                CONCAT(e.nombre, ' ', COALESCE(e.apellido1, ''), ' ', COALESCE(e.apellido2, '')) as nombre_completo,
                COALESCE(p.nombre_puestos, 'Sin puesto') as puesto,
                COALESCE(s.nombre, 'Sin sucursal') as sucursal,
                ra.fecha,
                ra.hora as hora_entrada_real,
                e.hora_entrada_puesto as hora_entrada_oficial,
                TIMESTAMPDIFF(MINUTE, e.hora_entrada_puesto, ra.hora) as minutos_retraso,
                0 as marcado  -- Campo para marcar retrasos
            FROM empleados e
            LEFT JOIN puestos p ON e.id_puestos = p.id_puestos
            LEFT JOIN sucursal s ON e.id_sucursal = s.id_sucursal
            INNER JOIN registros_asistencia ra ON ra.id_empleado = e.id_empleado
                AND ra.tipo = 'entrada'
                AND ra.fecha BETWEEN %s AND %s
            WHERE ra.hora IS NOT NULL
                AND e.hora_entrada_puesto IS NOT NULL
                AND ra.hora > e.hora_entrada_puesto
            ORDER BY ra.fecha DESC, minutos_retraso DESC
        """

        mycursor.execute(sql, (fecha_inicio, fecha_fin))
        retrasos = mycursor.fetchall()

        # Formatear fechas y tiempos
        retrasos_formateados = []
        for retraso in retrasos:
            horas_retraso = retraso['minutos_retraso'] // 60
            minutos_retraso = retraso['minutos_retraso'] % 60

            tiempo_retraso_texto = ""
            if horas_retraso > 0:
                tiempo_retraso_texto += f"{horas_retraso}h "
            if minutos_retraso > 0:
                tiempo_retraso_texto += f"{minutos_retraso}min"

            retrasos_formateados.append({
                'id_empleado': retraso['id_empleado'],
                'nombre_completo': retraso['nombre_completo'].strip(),
                'puesto': retraso['puesto'],
                'sucursal': retraso['sucursal'],
                'fecha': retraso['fecha'].strftime('%d/%m/%Y') if retraso['fecha'] else '',
                'hora_entrada_real': str(retraso['hora_entrada_real']) if retraso['hora_entrada_real'] else '',
                'hora_entrada_oficial': str(retraso['hora_entrada_oficial']) if retraso['hora_entrada_oficial'] else '',
                'minutos_retraso': retraso['minutos_retraso'],
                'tiempo_retraso': tiempo_retraso_texto.strip(),
                'marcado': retraso['marcado']
            })

        return jsonify({
            'success': True,
            'retrasos': retrasos_formateados
        })

    except Exception as err:
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

@app.route('/get_asistencia_filtrada', methods=['POST'])
def get_asistencia_filtrada():
    data = request.json
    filtro = data.get('filtro')  # 'hoy', 'semana', 'quincena'

    hoy = date.today()
    fecha_inicio = hoy
    fecha_fin = hoy

    # 1. Definir rangos de fecha
    if filtro == 'hoy':
        fecha_inicio = hoy
        fecha_fin = hoy
    elif filtro == 'semana':
        # Asumiendo que la semana empieza el Lunes (0)
        start_delta = hoy.weekday()
        fecha_inicio = hoy - timedelta(days=start_delta)
        fecha_fin = fecha_inicio + timedelta(days=6)
    elif filtro == 'quincena':
        # Lógica corregida: Mostrar la quincena pasada completa
        if hoy.day > 15:
            # Estamos en segunda quincena, mostrar primera quincena del mes actual
            fecha_inicio = date(hoy.year, hoy.month, 1)
            fecha_fin = date(hoy.year, hoy.month, 15)
        else:
            # Estamos en primera quincena, mostrar segunda quincena del mes anterior
            primer_dia_mes = date(hoy.year, hoy.month, 1)
            ultimo_dia_mes_anterior = primer_dia_mes - timedelta(days=1)
            fecha_inicio = date(ultimo_dia_mes_anterior.year, ultimo_dia_mes_anterior.month, 16)
            fecha_fin = ultimo_dia_mes_anterior

    mydb = get_db_connection()
    if not mydb:
        return jsonify({'success': False, 'message': 'Error DB'}), 500

    mycursor = mydb.cursor(dictionary=True)

    try:
        # 2. Obtener datos básicos y calcular en Python
        # Primero obtener empleados
        sql_empleados = """
            SELECT
                e.id_empleado,
                CONCAT(e.nombre, ' ', COALESCE(e.apellido1, ''), ' ', COALESCE(e.apellido2, '')) as nombre_completo,
                COALESCE(p.nombre_puestos, 'Sin puesto') as puesto,
                COALESCE(s.nombre, 'Sin sucursal') as sucursal,
                e.hora_entrada_puesto,
                e.hora_salida_puesto,
                e.hora_comida_entrada,
                e.hora_comida_salida
            FROM empleados e
            LEFT JOIN puestos p ON e.id_puestos = p.id_puestos
            LEFT JOIN sucursal s ON e.id_sucursal = s.id_sucursal
        """

        mycursor.execute(sql_empleados)
        empleados = mycursor.fetchall()

        # Segundo obtener registros de asistencia en el rango
        sql_asistencia = """
            SELECT
                id_empleado,
                fecha,
                tipo,
                hora
            FROM registros_asistencia
            WHERE fecha BETWEEN %s AND %s
            ORDER BY id_empleado, fecha, tipo
        """

        mycursor.execute(sql_asistencia, (fecha_inicio, fecha_fin))
        registros = mycursor.fetchall()

        # Procesar datos en Python
        from collections import defaultdict
        asistencia_por_empleado = defaultdict(lambda: {'registros': {}, 'info': {}})

        # Organizar empleados
        for emp in empleados:
            asistencia_por_empleado[emp['id_empleado']]['info'] = {
                'nombre': emp['nombre_completo'].strip(),
                'puesto': emp['puesto'],
                'sucursal': emp['sucursal'],
                'hora_entrada': emp['hora_entrada_puesto'],
                'hora_salida': emp['hora_salida_puesto'],
                'comida_entrada': emp['hora_comida_entrada'],
                'comida_salida': emp['hora_comida_salida']
            }

        # Organizar registros por empleado y fecha
        for reg in registros:
            emp_id = reg['id_empleado']
            fecha = reg['fecha']
            tipo = reg['tipo']
            hora = reg['hora']

            if emp_id not in asistencia_por_empleado:
                continue

            # Crear entrada para esta fecha si no existe
            fecha_key = str(fecha)
            if fecha_key not in asistencia_por_empleado[emp_id]['registros']:
                asistencia_por_empleado[emp_id]['registros'][fecha_key] = {'fecha': fecha_key, 'entrada': None, 'salida': None}

            # Asignar hora según tipo
            if tipo == 'entrada':
                asistencia_por_empleado[emp_id]['registros'][fecha_key]['entrada'] = hora
            elif tipo == 'salida':
                asistencia_por_empleado[emp_id]['registros'][fecha_key]['salida'] = hora

        # Calcular horas trabajadas
        resultados = []
        for emp_id, data in asistencia_por_empleado.items():
            info = data['info']
            registros_emp = data['registros']

            total_horas = 0.0

            for fecha_key, reg in registros_emp.items():
                entrada = reg['entrada']
                salida = reg['salida']

                if entrada and salida:
                    # Convertir strings de tiempo a objetos time para comparación
                    from datetime import datetime
                    entrada_time = datetime.strptime(str(entrada), '%H:%M:%S').time()
                    salida_time = datetime.strptime(str(salida), '%H:%M:%S').time()

                    # Usar horas oficiales como límites
                    hora_entrada_oficial = info['hora_entrada']
                    hora_salida_oficial = info['hora_salida']

                    if hora_entrada_oficial and hora_salida_oficial:
                        entrada_oficial_time = datetime.strptime(str(hora_entrada_oficial), '%H:%M:%S').time()
                        salida_oficial_time = datetime.strptime(str(hora_salida_oficial), '%H:%M:%S').time()

                        # Calcular horas trabajadas
                        entrada_trabajo = max(entrada_time, entrada_oficial_time)
                        salida_trabajo = min(salida_time, salida_oficial_time)

                        # Calcular diferencia en horas
                        entrada_dt = datetime.combine(datetime.today(), entrada_trabajo)
                        salida_dt = datetime.combine(datetime.today(), salida_trabajo)

                        if salida_dt > entrada_dt:
                            horas_dia = (salida_dt - entrada_dt).total_seconds() / 3600.0

                            # Restar comida si aplica
                            comida_entrada = info['comida_entrada']
                            comida_salida = info['comida_salida']

                            if (comida_entrada and comida_salida and
                                entrada_time <= datetime.strptime(str(comida_entrada), '%H:%M:%S').time() and
                                salida_time >= datetime.strptime(str(comida_salida), '%H:%M:%S').time()):

                                horas_dia -= 1.0  # Restar 1 hora de comida

                            total_horas += horas_dia

            resultados.append({
                'id_empleado': emp_id,
                'nombre_completo': info['nombre'],
                'puesto': info['puesto'],
                'sucursal': info['sucursal'],
                'horas_trabajadas': round(total_horas, 2)
            })

        # Formatear fechas para enviarlas al frontend
        rango_texto = f"{fecha_inicio.strftime('%d/%m/%Y')}"
        if filtro != 'hoy':
            rango_texto += f" al {fecha_fin.strftime('%d/%m/%Y')}"

        # Formatear empleados para el frontend
        empleados_formateados = []
        for emp in resultados:
            empleados_formateados.append({
                'id': emp['id_empleado'],
                'nombre': emp['nombre_completo'].strip(),
                'puesto': emp['puesto'],
                'sucursal': emp['sucursal'],
                'horas_trabajadas': round(float(emp['horas_trabajadas']), 2) if emp['horas_trabajadas'] else 0
            })

        return jsonify({
            'success': True,
            'empleados': empleados_formateados,
            'rango_fecha': rango_texto
        })

    except Exception as err:
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

# ----------------------------------------------------------------------
# RUTAS PARA SERVIR ARCHIVOS ESTÁTICOS
# ----------------------------------------------------------------------

@app.route('/')
def index():
    response = send_from_directory('.', 'index.html')
    # Headers para permitir acceso a cámara y multimedia
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    return response

@app.route('/<path:path>')
def static_file(path):
    response = send_from_directory('.', path)
    # Headers para permitir acceso a cámara y multimedia en todas las páginas
    if path.endswith(('.html', '.htm')):
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    return response

# ----------------------------------------------------------------------
# RUTA PARA INICIAR SERVIDOR CON CONFIGURACIÓN ESPECÍFICA
# ----------------------------------------------------------------------

@app.after_request
def after_request(response):
    # Headers CORS adicionales para desarrollo
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-User-ID')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    # Headers para multimedia y cámara
    if request.path.endswith(('.html', '.htm', '.js')):
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    return response


if __name__ == '__main__':
    print("Servidor Flask corriendo en http://127.0.0.1:5000/")
    app.run(debug=True, port=5000, host='0.0.0.0')
