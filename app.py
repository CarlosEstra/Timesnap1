from flask import Flask, request, jsonify, session
import mysql.connector
from datetime import datetime
import base64
import io
from flask_cors import CORS

# Inicialización de la aplicación Flask
app = Flask(__name__)
CORS(app) 

# --- CONFIGURACIÓN DE SESIÓN ---
# ⚠️ Cambia esta clave. Necesaria para Flask Sessions.
app.secret_key = '123456789' 

# --- 1. CONFIGURACIÓN Y CONEXIÓN A MYSQL ---
DB_CONFIG = {
    # ⚠️ ASEGÚRATE de que estos datos son correctos.
    'user': 'root',
    'password': '140223',
    'host': 'localhost',
    'database': 'timesnapbd' 
}


def get_db_connection():
    """Establece y devuelve una nueva conexión a la DB."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar a MySQL: {err}")
        return None

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
            
            return jsonify({
                'success': True, 
                'message': f'Bienvenido(a), {empleado["nombre"]}.', 
                'user_id': empleado['id_empleado']
            })
        
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

@app.route('/checar_salida', methods=['POST'])
def checar_salida():
    # Requiere login
    if not session.get('logged_in'):
        return jsonify({'success': False, 'message': 'Acceso denegado. Inicia sesión.'}), 403 

    # Lógica de chequeo de salida...
    hora_salida = datetime.now().strftime('%H:%M:%S')
    return jsonify({
        'success': True, 
        'message': 'Salida registrada correctamente.',
        'empleado_id': session.get('user_id', 'ID_TEST'),
        'hora': hora_salida
    })
    
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Sesión cerrada.'})


if __name__ == '__main__':
    print("Servidor Flask corriendo en http://127.0.0.1:5500/")
    app.run(debug=True, port=5000)