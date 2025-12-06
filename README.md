# 🎯 TimeSnap - Sistema de Control de Asistencia

Sistema completo de control de asistencia con reconocimiento facial, desarrollado con Flask, JavaScript y MySQL.

## 🚀 Inicio Rápido

### 1. Instalar Dependencias
```bash
pip install flask flask-cors mysql-connector-python
```

### 2. Configurar Base de Datos
Asegúrate de tener MySQL corriendo y configura la conexión en `db_connection.py`.

### 3. Iniciar Servidor
```bash
# Opción 1: Script automático (recomendado)
python start_server.py

# Opción 2: Manual
python app.py
```

### 4. Acceder a la Aplicación
- **URL Principal**: http://127.0.0.1:5000/
- **Dashboard**: http://127.0.0.1:5000/dashboardweb/web.html
- **Registro**: http://127.0.0.1:5000/registrosweb/registrar.html

## 🎥 Solución al Problema de la Cámara

### ❌ Error Común
```
"No se puede acceder a la cámara. Asegúrate de estar en un servidor local (Live Server) y de haber otorgado los permisos."
```

### ✅ Solución
**El servidor Flask YA incluye configuración completa para cámara:**

1. **Inicia el servidor correctamente:**
   ```bash
   python start_server.py
   ```

2. **Abre en navegador:**
   - ✅ http://127.0.0.1:5000/ (funciona)
   - ❌ file:///ruta/a/index.html (NO funciona)

3. **Otorga permisos de cámara:**
   - El navegador pedirá acceso a la cámara
   - Haz click en "Permitir" cuando aparezca el popup

### 🔧 Configuración Técnica
El servidor incluye headers especiales para multimedia:
- `Cross-Origin-Embedder-Policy: require-corp`
- `Cross-Origin-Opener-Policy: same-origin`
- Soporte CORS completo para desarrollo local

## 📋 Características

### 👥 Gestión de Empleados
- ✅ Registro con reconocimiento facial
- ✅ Edición completa de datos
- ✅ Eliminación masiva
- ✅ Filtros por puesto y sucursal

### 📊 Dashboard Administrativo
- ✅ Vista completa de empleados
- ✅ Filtros dinámicos en encabezados
- ✅ Edición rápida de puestos
- ✅ Estadísticas y reportes

### 🎯 Control de Asistencia
- ✅ Registro de entrada/salida
- ✅ Reconocimiento facial automático
- ✅ Validación de horarios
- ✅ Historial completo

### 🔐 Sistema de Autenticación
- ✅ Login seguro por ID/contraseña
- ✅ Sesiones persistentes
- ✅ Control de permisos

## 🗂️ Estructura del Proyecto

```
Timesnap1/
├── app.py                    # Servidor Flask principal
├── start_server.py          # Script de inicio
├── db_connection.py          # Configuración BD
├── index.html               # Página principal
├── login.js                 # Lógica de autenticación
├── global.css               # Estilos globales
├── dashboardweb/            # Dashboard administrativo
│   ├── web.html
│   ├── web.js
│   └── web.css
├── registrosweb/            # Sistema de registro
│   ├── registrar.html
│   ├── registrar.js
│   └── registrar.css
├── registrar_entrada/       # Registro de entrada
├── registrar_salida/        # Registro de salida
└── Dashboard/               # Dashboard usuario
```

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **Base de Datos**: MySQL
- **Reconocimiento Facial**: face-api.js
- **Multimedia**: WebRTC, MediaDevices API

## 🔧 Configuración Avanzada

### Base de Datos
Edita `db_connection.py` para configurar tu conexión MySQL:

```python
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="tu_usuario",
        password="tu_password",
        database="timesnap"
    )
```

### Puertos Personalizados
Para cambiar el puerto del servidor, modifica `app.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
```

## 🐛 Solución de Problemas

### "Error de conexión DB"
- Verifica que MySQL esté corriendo
- Revisa credenciales en `db_connection.py`
- Asegúrate de que la base de datos existe

### "No se puede acceder a la cámara"
- ✅ Usa servidor local (NO archivos locales)
- ✅ Otorga permisos cuando el navegador lo pida
- ✅ Verifica que no haya otras aplicaciones usando la cámara

### "Página no carga"
- Verifica que el servidor esté corriendo en puerto 5000
- Revisa la consola del navegador (F12) por errores
- Asegúrate de que no haya firewall bloqueando el puerto

## 📞 Soporte

Si encuentras problemas:
1. Revisa los logs del servidor en la terminal
2. Verifica la consola del navegador (F12)
3. Asegúrate de tener todas las dependencias instaladas

---

**Desarrollado con ❤️ para control eficiente de asistencia laboral**
