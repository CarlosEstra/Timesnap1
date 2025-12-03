from flask import Flask, request, jsonify, session, send_from_directory
from datetime import datetime
import base64
import io
from flask_cors import CORS
from db_connection import get_db_connection

# Inicialización de la aplicación Flask
app = Flask(__name__)

# --- CONFIGURACIÓN CORS CON COOKIES ---
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:5500', 'http://localhost:5500'])

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
        sql = "SELECT id_empleado, nombre, id_puestos FROM empleados WHERE id_empleado = %s AND contraseña = %s"
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

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
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

    print(f'📥 Datos recibidos - faceDescriptor: {"Presente" if face_descriptor else "Nulo"}')
    if face_descriptor:
        print(f'   Longitud del descriptor: {len(face_descriptor)}')

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

        # Contraseña por defecto
        contraseña = '1234'

        # Preparar descriptor facial como JSON
        import json
        fotoperfil = json.dumps(face_descriptor) if face_descriptor else None

        sql = """
        INSERT INTO empleados
        (id_empleado, fotoperfil, nombre, apellido1, apellido2, hora_comida_entrada, hora_comida_salida,
         hora_entrada_puesto, hora_salida_puesto, id_puestos, id_sucursal, contraseña)
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
        empleados = mycursor.fetchall()
        return jsonify({'success': True, 'empleados': empleados})
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
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
            return jsonify({'success': True, 'empleado': empleado})
        else:
            return jsonify({'success': False, 'message': 'Empleado no encontrado o sin datos faciales.'}), 404

    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': f'Error DB: {err.msg}'}), 500
    finally:
        if mycursor: mycursor.close()
        if mydb.is_connected(): mydb.close()

# ----------------------------------------------------------------------
# RUTAS PARA SERVIR ARCHIVOS ESTÁTICOS
# ----------------------------------------------------------------------

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_file(path):
    return send_from_directory('.', path)


if __name__ == '__main__':
    print("Servidor Flask corriendo en http://127.0.0.1:5000/")
    app.run(debug=True, port=5000, host='0.0.0.0')
