function checkIn() {
    alert("Entrada registrada correctamente.");
    // Aquí haces fetch o AJAX hacia tu backend si deseas guardar el registro
}

function checkOut() {
    alert("Salida registrada correctamente.");
    // Aquí haces fetch o AJAX hacia tu backend si deseas guardar el registro
}

// Ejemplo de cómo llenar datos con JS dinámicamente:
function cargarDatos(usuario) {
    document.getElementById("nombre").textContent = usuario.nombre;
    document.getElementById("puesto").textContent = usuario.puesto;
    document.getElementById("sucursal").textContent = usuario.sucursal;
    document.getElementById("fecha").textContent = usuario.fecha;
    document.getElementById("idUser").textContent = usuario.id;
    document.getElementById("horario").innerHTML = `${usuario.dias}<br>${usuario.horario}`;
    document.getElementById("horaEntrada").textContent = usuario.entrada;
    document.getElementById("horaSalida").textContent = usuario.salida;
}




cargarDatos(ejemploDB);
