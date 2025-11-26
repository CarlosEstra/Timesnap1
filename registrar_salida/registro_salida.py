from flask import Flask, request, jsonify
import mysql.connector
from datetime import datetime
import base64
import io

# Inicialización de la aplicación Flask
app = Flask(__name__)

# --- 1. CONFIGURACIÓN Y CONEXIÓN A MYSQL ---

DB_CONFIG = {
    'user': 'root',
    'password': '140223',
    'host': 'localhost',
    'database': 'timesnapbd' # Usando el nombre de base de datos que especificaste
}

def get_db_connection():
    """Establece y devuelve una nueva conexión a la DB."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar a MySQL: {err}")
        return None

# --- 2. LÓGICA DE RECONOCIMIENTO FACIAL (Simulación) ---

def realizar_reconocimiento_facial(foto_base64):
    """
    SIMULACIÓN de la API de reconocimiento facial. 
    Devuelve un ID de empleado en formato CHAR(8).
    """
    try:
        # Decodificación de la imagen Base64 para simular el procesamiento
        header, encoded = foto_base64.split(",", 1)
        image_data = base64.b64decode(encoded)
    except Exception as e:
        print(f"Error al decodificar Base64: {e}")
        return False, None

    # ⚠️ Lógica de SIMULACIÓN: 
    # Si hay una imagen válida, devolvemos un ID de ejemplo CHAR(8).
    if len(image_data) > 1000:
        empleado_id_reconocido = 'EMP00012' 
        return True, empleado_id_reconocido
    else:
        return False, None

# --- 3. RUTA DE REGISTRO (Chequeo de Salida) ---

@app.route('/checar_salida', methods=['POST'])
def checar_salida():
    """Maneja la solicitud POST para registrar la hora de salida."""
    
    data = request.json
    foto_base64 = data.get('photo_base64', '')
    
    if not foto_base64:
        return jsonify({'success': False, 'message': 'No se recibió la foto para el reconocimiento.'}), 400

    # 1. Reconocimiento Facial
    reconocimiento_ok, empleado_id = realizar_reconocimiento_facial(foto_base64)
    
    if not reconocimiento_ok:
        return jsonify({'success': False, 'message': '❌ Identidad no verificada. Intente de nuevo.'}), 401 

    # 2. Registrar la Salida
    now = datetime.now()
    fecha_hoy = now.strftime('%Y-%m-%d')
    hora_salida = now.strftime('%H:%M:%S')
    
    mydb = get_db_connection()
    if mydb:
        mycursor = None
        try:
            mycursor = mydb.cursor()
            
            # ⚠️ Paso 2a: Buscar el registro de ENTRADA de hoy que aún no tenga salida.
            # Se requiere que la tabla 'asistencia' tenga la columna 'fecha_registro'.
            mycursor.execute("""
                SELECT id_asistencia FROM asistencia 
                WHERE id_empleado = %s AND fecha_registro = %s 
                AND hora_entrada_puesto IS NOT NULL
                AND hora_salida_puesto IS NULL
            """, (empleado_id, fecha_hoy))
            
            registro_asistencia = mycursor.fetchone()
            
            if not registro_asistencia:
                return jsonify({'success': False, 'message': 'No se encontró una entrada previa para hoy o la salida ya fue registrada.'}), 409
            
            id_asistencia_a_actualizar = registro_asistencia[0]
            
            # ⚠️ Paso 2b: Ejecutar la actualización (UPDATE) de la hora de salida
            sql = """
            UPDATE asistencia 
            SET hora_salida_puesto = %s 
            WHERE id_asistencia = %s
            """
            val = (hora_salida, id_asistencia_a_actualizar) 
            
            mycursor.execute(sql, val)
            mydb.commit()
            
            # 3. Éxito
            return jsonify({
                'success': True, 
                'message': 'Salida registrada correctamente.',
                'empleado_id': empleado_id,
                'hora': hora_salida
            })
            
        except mysql.connector.Error as err:
            return jsonify({'success': False, 'message': f'Error al actualizar la DB: {err.msg}'}), 500
            
        finally:
            if mycursor:
                mycursor.close()
            if mydb.is_connected():
                mydb.close()
            
    return jsonify({'success': False, 'message': 'No se pudo establecer conexión con la base de datos.'}), 503


if __name__ == '__main__':
    print("Servidor Flask corriendo en http://127.0.0.1:5000/")
    app.run(debug=True, port=5000)