document.addEventListener("DOMContentLoaded", () => {

  const preview = document.getElementById("preview");
  const photoInput = document.getElementById("photoInput");

  const sucursalSelect = document.getElementById("sucursal");
  const puestoSelect = document.getElementById("puesto");

  const addSucursal = document.getElementById("addSucursal");
  const addPuesto = document.getElementById("addPuesto");

  const form = document.getElementById("employeeForm");

  // --------------------------
  // PREVIEW DE FOTO
  // --------------------------
  photoInput.addEventListener("change", () => {
    const file = photoInput.files[0];
    if (!file) return;
    preview.src = URL.createObjectURL(file);
  });

  // --------------------------
  // AGREGAR SUCURSAL
  // --------------------------
  addSucursal.addEventListener("click", () => {
    const nombre = prompt("Nombre de la nueva sucursal:");
    if (!nombre) return;
    const opt = document.createElement("option");
    opt.value = nombre;
    opt.textContent = nombre;
    sucursalSelect.appendChild(opt);
    sucursalSelect.value = nombre;
  });

  // --------------------------
  // AGREGAR PUESTO
  // --------------------------
  addPuesto.addEventListener("click", () => {
    const puesto = prompt("Nombre del nuevo puesto:");
    if (!puesto) return;
    const opt = document.createElement("option");
    opt.value = puesto;
    opt.textContent = puesto;
    puestoSelect.appendChild(opt);
    puestoSelect.value = puesto;
  });

  // --------------------------
  // CAPTURAR FORMULARIO (listo para backend)
  // --------------------------
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const data = {
      nombre: document.getElementById("nombre").value,
      apellidoP: document.getElementById("apellidoP").value,
      apellidoM: document.getElementById("apellidoM").value,
      sucursal: sucursalSelect.value,
      puesto: puestoSelect.value,
      horaEntrada: document.getElementById("horaEntrada").value,
      horaSalida: document.getElementById("horaSalida").value,
      comidaEntrada: document.getElementById("comidaEntrada").value,
      comidaSalida: document.getElementById("comidaSalida").value,
      foto: preview.src
    };

    console.log("ENVIAR AL BACKEND →", data);

    alert("Empleado registrado correctamente ✔");
  });

});
