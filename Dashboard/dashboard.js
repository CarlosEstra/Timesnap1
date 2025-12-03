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

// Función para cargar datos del usuario desde localStorage
function cargarDatosUsuario() {
    const userName = localStorage.getItem('user_name') || 'Usuario';
    const userId = localStorage.getItem('user_id') || 'N/A';
    const userPuesto = localStorage.getItem('user_puesto') || 'N/A';

    // Crear objeto con datos del usuario
    const usuario = {
        nombre: userName,
        puesto: userPuesto === '1' ? 'Gerente' : userPuesto === '2' ? 'Empleado' : 'Administrador',
        sucursal: 'Sucursal Central', // Podrías obtener esto del backend también
        fecha: new Date().toLocaleDateString(),
        id: userId,
        dias: 'LUNES - SABADO',
        horario: '9:00 AM - 6:00 PM',
        entrada: '9:00 AM',
        salida: '6:00 PM'
    };

    // Llenar datos en la UI
    document.getElementById("nombre").textContent = usuario.nombre;
    document.getElementById("puesto").textContent = usuario.puesto;
    document.getElementById("sucursal").textContent = usuario.sucursal;
    document.getElementById("fecha").textContent = usuario.fecha;
    document.getElementById("idUser").textContent = usuario.id;
    document.getElementById("horario").innerHTML = `${usuario.dias}<br>${usuario.horario}`;
    document.getElementById("horaEntrada").textContent = usuario.entrada;
    document.getElementById("horaSalida").textContent = usuario.salida;
}

// Inicializar dashboard
document.addEventListener('DOMContentLoaded', function() {
    if (checkSession()) {
        cargarDatosUsuario();
    }
});
