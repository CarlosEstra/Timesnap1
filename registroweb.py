from flask import Flask, request, jsonify
from datetime import datetime
import base64
import io
from flask_cors import CORS
from db_connection import get_db_connection

# Inicialización de la aplicación Flask para registro web
app = Flask(__name__)
CORS(app)

# ----------------------------------------------------------------------
# RUTAS PARA REGISTRO DE EMPLEADOS
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

@app.route('/registrar_empleado', methods=['POST'])
def registrar_empleado():
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
    # foto = data.get('foto')  # Para futuras implementaciones

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

        sql = """
        INSERT INTO empleados
        (id_empleado, nombre, apellido1, apellido2, hora_comida_entrada, hora_comida_salida,
         hora_entrada_puesto, hora_salida_puesto, id_puestos, id_sucursal, contraseña)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        val = (id_empleado, nombre, apellido1, apellido2 or None, hora_comida_entrada or None,
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

if __name__ == '__main__':
    print("Servidor Flask para registro web corriendo en http://127.0.0.1:5001/")
    app.run(debug=True, port=5001)
