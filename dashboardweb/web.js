// Conectar con el backend para obtener empleados
const empleadosBody = document.getElementById("empleadosBody");
const filtroFechaSelect = document.getElementById("filtroFecha");
const filtroPuestoSelect = document.getElementById("filtroPuesto");
const filtroSucursalSelect = document.getElementById("filtroSucursal");

// Variable para almacenar todos los empleados (sin filtrar)
let todosLosEmpleados = [];

// Función para cargar empleados desde el backend con filtro de tiempo
async function cargarEmpleados(filtroTiempo = 'hoy') {
  empleadosBody.innerHTML = '<tr><td colspan="9" style="text-align:center">Cargando...</td></tr>';

  try {
    console.log(`📡 Cargando asistencia filtrada (${filtroTiempo})...`);

    const response = await fetch('http://127.0.0.1:5000/get_asistencia_filtrada', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filtro: filtroTiempo })
    });

    const data = await response.json();

    if (data.success) {
      console.log(`✅ ${data.empleados.length} empleados cargados`);
      cargarTabla(data.empleados, data.rango_fecha);
    } else {
      console.error('❌ Error cargando empleados:', data.message);
      mostrarError('Error al cargar empleados: ' + data.message);
    }
  } catch (error) {
    console.error('❌ Error de conexión:', error);
    mostrarError('Error de conexión al cargar empleados');
  }
}



// Función para mostrar errores
function mostrarError(mensaje) {
  empleadosBody.innerHTML = `
    <tr>
      <td colspan="9" style="text-align: center; color: red; padding: 20px;">
        ❌ ${mensaje}
      </td>
    </tr>
  `;
}

// Función para insertar la info en la tabla
function cargarTabla(listaEmpleados, rangoFecha = '') {
  empleadosBody.innerHTML = "";

  if (listaEmpleados.length === 0) {
    empleadosBody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; padding: 20px;">
          📝 No hay registros de asistencia en el período seleccionado
        </td>
      </tr>
    `;
    return;
  }

  listaEmpleados.forEach(emp => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><input type="checkbox" class="rowCheck" data-id="${emp.id}"></td>
      <td style="font-weight: bold;">${emp.nombre || 'N/A'}</td>
      <td style="font-weight: bold;">${emp.puesto || 'N/A'}</td>
      <td style="font-weight: bold;">${emp.sucursal || 'N/A'}</td>
      <td style="font-weight: bold;">${rangoFecha}</td>
      <td style="font-weight: bold;">${emp.horas_trabajadas || 0} hrs</td>
      <td>
        <span class="badge green">Activo</span>
      </td>
      <td>-</td>
      <td class="actions-dots">⋮</td>
    `;

    empleadosBody.appendChild(tr);
  });
}

// Define color según estado
function statusColor(estado) {
  if (!estado) return "gray";

  switch (estado.toLowerCase()) {
    case "registrado": return "green";
    case "sin registro facial": return "yellow";
    case "activo": return "green";
    case "inactivo": return "red";
    case "vacaciones": return "yellow";
    case "permiso": return "blue";
    case "incapacidad": return "red";
    default: return "blue";
  }
}

// Seleccionar todos
document.getElementById("selectAll").addEventListener("change", e => {
  document.querySelectorAll(".rowCheck").forEach(chk => {
    chk.checked = e.target.checked;
  });
});

// Función para eliminar empleados seleccionados
async function eliminarEmpleadosSeleccionados() {
  const checkboxesSeleccionados = document.querySelectorAll(".rowCheck:checked");

  if (checkboxesSeleccionados.length === 0) {
    alert('❌ Selecciona al menos un empleado para eliminar.');
    return;
  }

  // Obtener IDs de empleados seleccionados
  const empleadosIds = Array.from(checkboxesSeleccionados).map(chk => chk.getAttribute('data-id'));

  // Confirmación
  const nombresEmpleados = Array.from(checkboxesSeleccionados).map(chk => {
    const row = chk.closest('tr');
    const nombreCell = row.querySelector('td:nth-child(2)');
    return nombreCell ? nombreCell.textContent : 'Desconocido';
  }).join(', ');

  const confirmacion = confirm(`⚠️ ¿Estás seguro de eliminar los siguientes empleados?\n\n${nombresEmpleados}\n\nEsta acción no se puede deshacer y eliminará también todos sus registros de asistencia.`);

  if (!confirmacion) {
    return;
  }

  try {
    console.log('🗑️ Eliminando empleados:', empleadosIds);

    const response = await fetch('http://127.0.0.1:5000/eliminar_empleados', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        empleados_ids: empleadosIds
      })
    });

    const data = await response.json();

    if (data.success) {
      alert(`✅ ${data.message}`);
      // Recargar la lista de empleados respetando filtro de fecha actual
      const filtroActual = filtroFechaSelect.value;
      await cargarEmpleados(filtroActual);
      // Desmarcar el checkbox "Seleccionar todos"
      document.getElementById("selectAll").checked = false;
    } else {
      alert(`❌ Error: ${data.message}`);
    }

  } catch (error) {
    console.error('❌ Error al eliminar empleados:', error);
    alert('❌ Error de conexión al eliminar empleados.');
  }
}

// Event listener para el botón de eliminar
document.getElementById("deleteSelected").addEventListener("click", eliminarEmpleadosSeleccionados);

// Variables del modal
const editModal = document.getElementById('editModal');
const editForm = document.getElementById('editForm');
const closeModal = document.querySelector('.close');
const cancelEdit = document.getElementById('cancelEdit');

// Función para abrir modal de edición
async function editarEmpleadoSeleccionado() {
  const checkboxesSeleccionados = document.querySelectorAll(".rowCheck:checked");

  if (checkboxesSeleccionados.length === 0) {
    alert('❌ Selecciona un empleado para editar.');
    return;
  }

  if (checkboxesSeleccionados.length > 1) {
    alert('❌ Selecciona solo un empleado para editar.');
    return;
  }

  const empleadoId = checkboxesSeleccionados[0].getAttribute('data-id');

  try {
    console.log('📝 Cargando datos del empleado:', empleadoId);

    // Cargar datos del empleado
    const response = await fetch(`http://127.0.0.1:5000/get_empleado_detalle/${empleadoId}`);
    const data = await response.json();

    if (data.success) {
      // Llenar el formulario con los datos
      const emp = data.empleado;
      document.getElementById('editEmployeeId').value = emp.id;
      document.getElementById('editNombre').value = emp.nombre;
      document.getElementById('editApellidoP').value = emp.apellido1;
      document.getElementById('editApellidoM').value = emp.apellido2;
      document.getElementById('editHoraEntrada').value = emp.hora_entrada;
      document.getElementById('editHoraSalida').value = emp.hora_salida;
      document.getElementById('editComidaEntrada').value = emp.comida_entrada;
      document.getElementById('editComidaSalida').value = emp.comida_salida;

      // Cargar opciones de sucursales y puestos
      await cargarOpcionesModal();

      // Seleccionar valores actuales
      document.getElementById('editSucursal').value = emp.id_sucursal;
      document.getElementById('editPuesto').value = emp.puesto;

      // Mostrar modal
      editModal.style.display = 'block';
    } else {
      alert(`❌ Error: ${data.message}`);
    }

  } catch (error) {
    console.error('❌ Error al cargar empleado:', error);
    alert('❌ Error de conexión al cargar empleado.');
  }
}

// Función para cargar opciones en el modal
async function cargarOpcionesModal() {
  try {
    // Cargar sucursales
    const sucursalesResponse = await fetch('http://127.0.0.1:5000/get_sucursales');
    const sucursalesData = await sucursalesResponse.json();

    const sucursalSelect = document.getElementById('editSucursal');
    sucursalSelect.innerHTML = '<option value="">Selecciona una</option>';

    if (sucursalesData.success) {
      sucursalesData.sucursales.forEach(suc => {
        const option = document.createElement('option');
        option.value = suc.id_sucursal;
        option.textContent = suc.nombre;
        sucursalSelect.appendChild(option);
      });
    }

    // Cargar puestos
    const puestosResponse = await fetch('http://127.0.0.1:5000/get_puestos');
    const puestosData = await puestosResponse.json();

    const puestoSelect = document.getElementById('editPuesto');
    puestoSelect.innerHTML = '<option value="">Selecciona un puesto</option>';

    if (puestosData.success) {
      puestosData.puestos.forEach(puesto => {
        const option = document.createElement('option');
        option.value = puesto.nombre_puestos;
        option.textContent = puesto.nombre_puestos;
        puestoSelect.appendChild(option);
      });
    }

  } catch (error) {
    console.error('❌ Error cargando opciones:', error);
  }
}

// Función para guardar cambios
async function guardarCambiosEmpleado(event) {
  event.preventDefault();

  const formData = new FormData(editForm);
  const empleadoData = {
    id: document.getElementById('editEmployeeId').value,
    nombre: document.getElementById('editNombre').value,
    apellidoP: document.getElementById('editApellidoP').value,
    apellidoM: document.getElementById('editApellidoM').value,
    sucursal: document.getElementById('editSucursal').value,
    puesto: document.getElementById('editPuesto').value,
    horaEntrada: document.getElementById('editHoraEntrada').value,
    horaSalida: document.getElementById('editHoraSalida').value,
    comidaEntrada: document.getElementById('editComidaEntrada').value,
    comidaSalida: document.getElementById('editComidaSalida').value
  };

  try {
    console.log('💾 Guardando cambios del empleado:', empleadoData.id);

    const response = await fetch('http://127.0.0.1:5000/actualizar_empleado', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(empleadoData)
    });

    const data = await response.json();

    if (data.success) {
      alert(`✅ ${data.message}`);
      editModal.style.display = 'none';
      // Recargar la lista de empleados respetando filtro de fecha actual
      const filtroActual = filtroFechaSelect.value;
      await cargarEmpleados(filtroActual);
    } else {
      alert(`❌ Error: ${data.message}`);
    }

  } catch (error) {
    console.error('❌ Error al guardar cambios:', error);
    alert('❌ Error de conexión al guardar cambios.');
  }
}

// Función para cerrar modal
function cerrarModal() {
  editModal.style.display = 'none';
  editForm.reset();
}

// Event listeners para el modal
document.getElementById("editSelected").addEventListener("click", editarEmpleadoSeleccionado);
closeModal.addEventListener('click', cerrarModal);
cancelEdit.addEventListener('click', cerrarModal);
editForm.addEventListener('submit', guardarCambiosEmpleado);

// Cerrar modal al hacer clic fuera
window.addEventListener('click', (event) => {
  if (event.target === editModal) {
    cerrarModal();
  }
});

// Variables del modal de notificaciones
const notificationsModal = document.getElementById('notificationsModal');
const showNotificationsBtn = document.getElementById('showNotifications');
const closeNotificationsBtn = document.querySelector('.close-notifications');
const filtroNotificacionesSelect = document.getElementById('filtroNotificaciones');
const notificationsBody = document.getElementById('notificationsBody');
const totalRetrasosDiv = document.getElementById('totalRetrasos');

// Función para mostrar modal de notificaciones
async function mostrarNotificaciones(filtro = 'hoy') {
  notificationsBody.innerHTML = '<tr><td colspan="7" style="text-align:center">Cargando notificaciones...</td></tr>';

  try {
    console.log(`📡 Cargando notificaciones de retrasos (${filtro})...`);

    const response = await fetch('http://127.0.0.1:5000/get_notificaciones_retrasos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filtro: filtro })
    });

    const data = await response.json();

    if (data.success) {
      console.log(`✅ ${data.total_retrasos} retrasos encontrados`);
      cargarTablaNotificaciones(data.retrasos);
      totalRetrasosDiv.textContent = `Total: ${data.total_retrasos} retrasos`;
    } else {
      console.error('❌ Error cargando notificaciones:', data.message);
      mostrarErrorNotificaciones('Error al cargar notificaciones: ' + data.message);
    }
  } catch (error) {
    console.error('❌ Error de conexión:', error);
    mostrarErrorNotificaciones('Error de conexión al cargar notificaciones');
  }
}

// Función para mostrar errores en notificaciones
function mostrarErrorNotificaciones(mensaje) {
  notificationsBody.innerHTML = `
    <tr>
      <td colspan="7" style="text-align: center; color: red; padding: 20px;">
        ❌ ${mensaje}
      </td>
    </tr>
  `;
}

// Función para cargar la tabla de notificaciones
function cargarTablaNotificaciones(retrasos) {
  notificationsBody.innerHTML = "";

  if (retrasos.length === 0) {
    notificationsBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 20px;">
          ✅ No hay retrasos en el período seleccionado
        </td>
      </tr>
    `;
    return;
  }

  retrasos.forEach(retraso => {
    const tr = document.createElement("tr");

    // Determinar color según severidad del retraso
    let retrasoClass = 'normal';
    if (retraso.minutos_retraso > 60) {
      retrasoClass = 'severe'; // Más de 1 hora
    } else if (retraso.minutos_retraso > 30) {
      retrasoClass = 'moderate'; // Más de 30 minutos
    }

    tr.innerHTML = `
      <td style="font-weight: bold;">${retraso.nombre || 'N/A'}</td>
      <td>${retraso.puesto || 'N/A'}</td>
      <td>${retraso.sucursal || 'N/A'}</td>
      <td>${retraso.fecha}</td>
      <td>${retraso.hora_entrada_oficial}</td>
      <td style="color: #dc3545; font-weight: bold;">${retraso.hora_entrada_real}</td>
      <td>
        <span class="retraso-badge ${retrasoClass}">${retraso.tiempo_retraso}</span>
      </td>
    `;

    notificationsBody.appendChild(tr);
  });
}

// Función para abrir modal de notificaciones
function abrirModalNotificaciones() {
  notificationsModal.style.display = 'block';
  // Cargar notificaciones con el filtro actual
  const filtroActual = filtroNotificacionesSelect.value;
  mostrarNotificaciones(filtroActual);
}

// Función para cerrar modal de notificaciones
function cerrarModalNotificaciones() {
  notificationsModal.style.display = 'none';
}

// Event listeners para el modal de notificaciones
showNotificationsBtn.addEventListener('click', abrirModalNotificaciones);
closeNotificationsBtn.addEventListener('click', cerrarModalNotificaciones);

// Event listener para el filtro de notificaciones
filtroNotificacionesSelect.addEventListener('change', async (e) => {
  const filtroSeleccionado = e.target.value;
  await mostrarNotificaciones(filtroSeleccionado);
});

// Cerrar modal de notificaciones al hacer clic fuera
window.addEventListener('click', (event) => {
  if (event.target === notificationsModal) {
    cerrarModalNotificaciones();
  }
});

// Función para cargar opciones de filtros
async function cargarOpcionesFiltros() {
  try {
    // Cargar puestos
    const puestosResponse = await fetch('http://127.0.0.1:5000/get_puestos');
    const puestosData = await puestosResponse.json();

    if (puestosData.success) {
      filtroPuestoSelect.innerHTML = '<option value="">Todos los puestos</option>';
      puestosData.puestos.forEach(puesto => {
        const option = document.createElement('option');
        option.value = puesto.nombre_puestos;
        option.textContent = puesto.nombre_puestos;
        filtroPuestoSelect.appendChild(option);
      });
    }

    // Cargar sucursales
    const sucursalesResponse = await fetch('http://127.0.0.1:5000/get_sucursales');
    const sucursalesData = await sucursalesResponse.json();

    if (sucursalesData.success) {
      filtroSucursalSelect.innerHTML = '<option value="">Todas las sucursales</option>';
      sucursalesData.sucursales.forEach(sucursal => {
        const option = document.createElement('option');
        option.value = sucursal.nombre;
        option.textContent = sucursal.nombre;
        filtroSucursalSelect.appendChild(option);
      });
    }

  } catch (error) {
    console.error('❌ Error cargando opciones de filtros:', error);
  }
}

// Función para aplicar filtros
function aplicarFiltros() {
  const filtroPuesto = filtroPuestoSelect.value;
  const filtroSucursal = filtroSucursalSelect.value;

  // Filtrar empleados basados en los criterios seleccionados
  let empleadosFiltrados = todosLosEmpleados;

  if (filtroPuesto) {
    empleadosFiltrados = empleadosFiltrados.filter(emp => emp.puesto === filtroPuesto);
  }

  if (filtroSucursal) {
    empleadosFiltrados = empleadosFiltrados.filter(emp => emp.sucursal === filtroSucursal);
  }

  // Mostrar empleados filtrados
  const rangoFecha = document.querySelector('#empleadosTable tbody tr:first-child td:nth-child(5)')?.textContent || '';
  cargarTabla(empleadosFiltrados, rangoFecha);
}

// Event listeners para los filtros
filtroFechaSelect.addEventListener('change', async (e) => {
  const filtroSeleccionado = e.target.value;
  await cargarEmpleados(filtroSeleccionado);
});

filtroPuestoSelect.addEventListener('change', aplicarFiltros);
filtroSucursalSelect.addEventListener('change', aplicarFiltros);

// Modificar la función cargarEmpleados para almacenar los datos
const cargarEmpleadosOriginal = cargarEmpleados;
cargarEmpleados = async function(filtroTiempo = 'hoy') {
  empleadosBody.innerHTML = '<tr><td colspan="9" style="text-align:center">Cargando...</td></tr>';

  try {
    console.log(`📡 Cargando asistencia filtrada (${filtroTiempo})...`);

    const response = await fetch('http://127.0.0.1:5000/get_asistencia_filtrada', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filtro: filtroTiempo })
    });

    const data = await response.json();

    if (data.success) {
      console.log(`✅ ${data.empleados.length} empleados cargados`);
      // Almacenar todos los empleados para filtrado
      todosLosEmpleados = data.empleados;
      cargarTabla(data.empleados, data.rango_fecha);
    } else {
      console.error('❌ Error cargando empleados:', data.message);
      mostrarError('Error al cargar empleados: ' + data.message);
    }
  } catch (error) {
    console.error('❌ Error de conexión:', error);
    mostrarError('Error de conexión al cargar empleados');
  }
};

// Cargar empleados al iniciar la página
document.addEventListener('DOMContentLoaded', async () => {
  // Cargar opciones de filtros
  await cargarOpcionesFiltros();
  // Cargar datos iniciales (filtro 'hoy' por defecto)
  await cargarEmpleados('hoy');
});
