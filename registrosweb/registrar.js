document.addEventListener("DOMContentLoaded", () => {

  const preview = document.getElementById("preview");
  const photoInput = document.getElementById("photoInput");

  const sucursalSelect = document.getElementById("sucursal");
  const puestoSelect = document.getElementById("puesto");

  const addSucursal = document.getElementById("addSucursal");
  const addPuesto = document.getElementById("addPuesto");

  const form = document.getElementById("employeeForm");

  // --------------------------
// PERSISTENCIA DE DATOS CON LOCALSTORAGE
  // --------------------------
  function saveFormData() {
    const formData = {
      nombre: document.getElementById("nombre").value,
      apellidoP: document.getElementById("apellidoP").value,
      apellidoM: document.getElementById("apellidoM").value,
      sucursal: sucursalSelect.value,
      puesto: puestoSelect.value,
      horaEntrada: document.getElementById("horaEntrada").value,
      horaSalida: document.getElementById("horaSalida").value,
      comidaEntrada: document.getElementById("comidaEntrada").value,
      comidaSalida: document.getElementById("comidaSalida").value
    };
    localStorage.setItem('employeeFormData', JSON.stringify(formData));
  }

  function loadFormData() {
    const savedData = localStorage.getItem('employeeFormData');
    if (savedData) {
      const formData = JSON.parse(savedData);
      document.getElementById("nombre").value = formData.nombre || '';
      document.getElementById("apellidoP").value = formData.apellidoP || '';
      document.getElementById("apellidoM").value = formData.apellidoM || '';
      // Sucursal y puesto se cargarán después de que se carguen las opciones
      setTimeout(() => {
        sucursalSelect.value = formData.sucursal || '';
        puestoSelect.value = formData.puesto || '';
      }, 500); // Esperar a que se carguen las sucursales
      document.getElementById("horaEntrada").value = formData.horaEntrada || '';
      document.getElementById("horaSalida").value = formData.horaSalida || '';
      document.getElementById("comidaEntrada").value = formData.comidaEntrada || '';
      document.getElementById("comidaSalida").value = formData.comidaSalida || '';
    }
  }

  function clearFormData() {
    localStorage.removeItem('employeeFormData');
  }

  // --------------------------
// PREVIEW DE FOTO
  // --------------------------
  photoInput.addEventListener("change", () => {
    const file = photoInput.files[0];
    if (!file) return;
    preview.src = URL.createObjectURL(file);
  });

  // --------------------------
// CARGAR SUCURSALES Y PUESTOS DESDE BACKEND
  // --------------------------
  async function loadSucursales() {
    try {
      const response = await fetch('http://127.0.0.1:5001/get_sucursales');
      const data = await response.json();
      if (data.success) {
        sucursalSelect.innerHTML = '<option value="">Selecciona una sucursal</option>';
        data.sucursales.forEach(suc => {
          const opt = document.createElement("option");
          opt.value = suc.id_sucursal;
          opt.textContent = suc.nombre;
          sucursalSelect.appendChild(opt);
        });
      } else {
        alert('Error al cargar sucursales: ' + data.message);
      }
    } catch (error) {
      console.error('Error cargando sucursales:', error);
      alert('Error de conexión al cargar sucursales');
    }
  }

  async function loadPuestos() {
    try {
      const response = await fetch('http://127.0.0.1:5001/get_puestos');
      const data = await response.json();
      if (data.success) {
        puestoSelect.innerHTML = '<option value="">Selecciona un puesto</option>';
        data.puestos.forEach(puesto => {
          const opt = document.createElement("option");
          opt.value = puesto.nombre_puestos;  // Usar el nombre como value
          opt.textContent = puesto.nombre_puestos;
          puestoSelect.appendChild(opt);
        });
      } else {
        alert('Error al cargar puestos: ' + data.message);
      }
    } catch (error) {
      console.error('Error cargando puestos:', error);
      alert('Error de conexión al cargar puestos');
    }
  }

  // Cargar sucursales y puestos al iniciar
  Promise.all([loadSucursales(), loadPuestos()]).then(() => {
    // Después de cargar opciones, cargar datos guardados
    loadFormData();
  });

  // --------------------------
// GUARDAR DATOS AL CAMBIAR CAMPOS
  // --------------------------
  const formFields = ['nombre', 'apellidoP', 'apellidoM', 'horaEntrada', 'horaSalida', 'comidaEntrada', 'comidaSalida'];
  formFields.forEach(fieldId => {
    const element = document.getElementById(fieldId);
    if (element) {
      element.addEventListener('input', saveFormData);
      element.addEventListener('change', saveFormData);
    }
  });

  sucursalSelect.addEventListener('change', saveFormData);
  puestoSelect.addEventListener('change', saveFormData);

  // --------------------------
// AGREGAR SUCURSAL
  // --------------------------
  addSucursal.addEventListener("click", async () => {
    const nombre = prompt("Nombre de la nueva sucursal:");
    if (!nombre || !nombre.trim()) return;

    try {
      const response = await fetch('http://127.0.0.1:5001/agregar_sucursal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ nombre: nombre.trim() })
      });

      const result = await response.json();
      if (result.success) {
        alert(result.message);
        // Recargar sucursales
        await loadSucursales();
        sucursalSelect.value = result.id_sucursal;
        saveFormData();
      } else {
        alert('Error: ' + result.message);
      }
    } catch (error) {
      console.error('Error agregando sucursal:', error);
      alert('Error de conexión al agregar sucursal');
    }
  });

  // --------------------------
// AGREGAR PUESTO
  // --------------------------
  addPuesto.addEventListener("click", async () => {
    const puesto = prompt("Nombre del nuevo puesto:");
    if (!puesto || !puesto.trim()) return;

    try {
      const response = await fetch('http://127.0.0.1:5001/agregar_puesto', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ nombre: puesto.trim() })
      });

      const result = await response.json();
      if (result.success) {
        alert(result.message);
        // Recargar puestos
        await loadPuestos();
        puestoSelect.value = puesto.trim();
        saveFormData();
      } else {
        alert('Error: ' + result.message);
      }
    } catch (error) {
      console.error('Error agregando puesto:', error);
      alert('Error de conexión al agregar puesto');
    }
  });

  // --------------------------
// ENVIAR FORMULARIO AL BACKEND
  // --------------------------
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      nombre: document.getElementById("nombre").value.trim(),
      apellidoP: document.getElementById("apellidoP").value.trim(),
      apellidoM: document.getElementById("apellidoM").value.trim(),
      sucursal: sucursalSelect.value,
      puesto: puestoSelect.value,
      horaEntrada: document.getElementById("horaEntrada").value,
      horaSalida: document.getElementById("horaSalida").value,
      comidaEntrada: document.getElementById("comidaEntrada").value,
      comidaSalida: document.getElementById("comidaSalida").value,
      // foto: preview.src  // Para futuras implementaciones
    };

    // Validación básica
    if (!data.nombre || !data.apellidoP || !data.sucursal || !data.puesto) {
      alert("Por favor, completa todos los campos obligatorios.");
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5001/registrar_empleado', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });

      const result = await response.json();
      if (result.success) {
        alert(result.message);
        form.reset();  // Limpiar formulario
        preview.src = "assets/user-default.png";  // Reset foto
        clearFormData();  // Limpiar datos guardados en localStorage
      } else {
        alert('Error: ' + result.message);
      }
    } catch (error) {
      console.error('Error enviando formulario:', error);
      alert('Error de conexión al registrar empleado');
    }
  });

});
