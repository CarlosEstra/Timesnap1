// Función para cerrar sesión
function logout() {
    // Limpiar localStorage
    localStorage.removeItem('user_logged_in');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_name');
    localStorage.removeItem('user_puesto');

    // Redirigir al login
    window.location.href = '../index.html';
}

// Función para convertir hora de 24h a 12h con AM/PM
function formatTimeTo12Hour(timeString) {
    if (!timeString) return 'N/A';

    const [hours, minutes] = timeString.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const hour12 = hour % 12 || 12; // 0 becomes 12

    return `${hour12}:${minutes} ${ampm}`;
}

// Función para verificar sesión al cargar la página
function checkSession() {
    const userLoggedIn = localStorage.getItem('user_logged_in');
    const userId = localStorage.getItem('user_id');

    if (!userLoggedIn || !userId) {
        alert('Debes iniciar sesión primero.');
        window.location.href = '../index.html';
        return false;
    }
    return true;
}

// Función para cargar datos del usuario desde la base de datos
async function cargarDatosUsuario() {
    const userId = localStorage.getItem('user_id');

    if (!userId) {
        alert('No se encontró ID de usuario. Inicia sesión nuevamente.');
        window.location.href = '../index.html';
        return;
    }

    try {
        console.log('📡 Cargando datos del empleado:', userId);

        const response = await fetch(`http://127.0.0.1:5000/get_empleado_detalle/${userId}`);
        const data = await response.json();

        if (data.success) {
            const emp = data.empleado;

            // Llenar datos en la UI
            document.getElementById("nombre").textContent = emp.nombre || 'N/A';
            document.getElementById("puesto").textContent = emp.puesto || 'N/A';
            document.getElementById("sucursal").textContent = emp.sucursal || 'N/A';
            document.getElementById("fecha").textContent = new Date().toLocaleDateString();
            document.getElementById("idUser").textContent = emp.id;
            document.getElementById("horario").innerHTML = `LUNES - SABADO<br>${formatTimeTo12Hour(emp.hora_entrada)} - ${formatTimeTo12Hour(emp.hora_salida)}`;
            document.getElementById("horaEntrada").textContent = formatTimeTo12Hour(emp.hora_entrada) || 'N/A';
            document.getElementById("horaSalida").textContent = formatTimeTo12Hour(emp.hora_salida) || 'N/A';
        } else {
            console.error('❌ Error cargando datos del empleado:', data.message);
            alert('Error al cargar datos del empleado: ' + data.message);
        }
    } catch (error) {
        console.error('❌ Error de conexión:', error);
        alert('Error de conexión al cargar datos del empleado.');
    }
}

// Inicializar dashboard
document.addEventListener('DOMContentLoaded', function() {
    if (checkSession()) {
        cargarDatosUsuario();
    }
});
