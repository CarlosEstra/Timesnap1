// 👉 Cuando conecten el backend, aquí recibirán los datos.
// Ejemplo de estructura que deberá consumir:
//
// fetch("api/empleados")
//   .then(res => res.json())
//   .then(data => cargarTabla(data));

const empleadosBody = document.getElementById("empleadosBody");

// Función para insertar la info en la tabla
function cargarTabla(listaEmpleados) {
  empleadosBody.innerHTML = "";

  listaEmpleados.forEach(emp => {
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><input type="checkbox" class="rowCheck"></td>
      <td>${emp.nombre}</td>
      <td>${emp.puesto}</td>
      <td>${emp.sucursal}</td>
      <td>${emp.fecha}</td>
      <td>${emp.horas}</td>

      <td>
        <span class="badge ${statusColor(emp.estado)}">${emp.estado}</span>
      </td>

      <td>${emp.observaciones ?? "-"}</td>
      <td class="actions-dots">⋮</td>
    `;

    empleadosBody.appendChild(tr);
  });
}

// Define color según estado
function statusColor(estado) {
  switch (estado.toLowerCase()) {
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

// 👉 Esto quedará vacío hasta que conecten backend
// cargarTabla([]); 
