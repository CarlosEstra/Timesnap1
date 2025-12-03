document.addEventListener("DOMContentLoaded", () => {

  const preview = document.getElementById("preview");
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const btnTakePhoto = document.getElementById("btnTakePhoto");

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
// CÁMARA Y CAPTURA DE FOTO
  // --------------------------
  let faceDescriptor = null;
  let modelsLoaded = false;

  // Inicializar cámara
  async function startCamera() {
    try {
      // Verificar soporte básico
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('❌ Tu navegador no soporta el acceso a la cámara.\n\nPor favor, actualiza tu navegador a una versión más reciente.');
        return false;
      }

      // Solicitar acceso a la cámara (el navegador mostrará el prompt nativo)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'  // Cámara frontal
        }
      });

      video.srcObject = stream;
      video.style.display = 'block';
      await video.play();
      console.log('✅ Cámara iniciada correctamente');
      return true;

    } catch (err) {
      console.error('Error accediendo a la cámara:', err);

      // Solo mostrar errores críticos, no problemas de permisos (el navegador ya los maneja)
      if (err.name === 'NotFoundError') {
        alert('📷 No se encontró ninguna cámara conectada a tu dispositivo.');
      } else if (err.name === 'NotReadableError') {
        alert('📹 La cámara está siendo usada por otra aplicación. Cierra otras aplicaciones que puedan estar usando la cámara.');
      } else if (err.name !== 'NotAllowedError') {
        // NotAllowedError ya es manejado por el navegador, no mostrar mensaje adicional
        alert('❌ Error al acceder a la cámara: ' + err.message);
      }

      return false;
    }
  }

  // Iniciar aplicación
  console.log('Iniciando aplicación de registro...');

  // Esperar a que se carguen los modelos de face-api.js
  async function initializeApp() {
    // Intentar cargar modelos si no están cargados
    if (typeof faceapi !== 'undefined') {
      try {
        // Cargar modelos de face-api.js
        const urls = [
          'https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/weights/',
          'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.2.0/model/',
          'https://raw.githubusercontent.com/justadudewhohacks/face-api.js/master/weights/'
        ];

        let modelsLoadedSuccessfully = false;
        for (const baseUrl of urls) {
          try {
            console.log('Intentando cargar modelos desde:', baseUrl);
            await Promise.all([
              faceapi.nets.tinyFaceDetector.loadFromUri(baseUrl),
              faceapi.nets.faceLandmark68Net.loadFromUri(baseUrl),
              faceapi.nets.faceRecognitionNet.loadFromUri(baseUrl)
            ]);
            console.log('✅ Modelos de face-api.js cargados exitosamente desde:', baseUrl);
            modelsLoadedSuccessfully = true;
            break;
          } catch (urlError) {
            console.warn('URL falló:', baseUrl, urlError);
            continue;
          }
        }

        if (!modelsLoadedSuccessfully) {
          console.error('❌ No se pudieron cargar los modelos desde ninguna URL');
          return;
        }
        modelsLoaded = true;
        console.log('✅ Modelos de face-api.js cargados exitosamente');
      } catch (error) {
        console.warn('⚠️ Modelos de face-api.js no se pudieron cargar:', error);
      }
    } else {
      console.warn('⚠️ face-api.js no está disponible');
    }

    // Iniciar cámara
    await startCamera();
  }

  // Esperar un poco para que se cargue face-api.js
  setTimeout(initializeApp, 1000);

  // Botón para tomar foto
  btnTakePhoto.addEventListener('click', async () => {
    // Configurar canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (ctx) {
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Mostrar preview y ocultar video
      preview.src = canvas.toDataURL('image/jpeg', 0.8);
      preview.style.display = 'block';
      video.style.display = 'none';

      if (modelsLoaded) {
        try {
          // Detectar rostro y calcular descriptor
          const detection = await faceapi.detectSingleFace(canvas, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();

          if (detection) {
            faceDescriptor = detection.descriptor;
            alert('✅ Foto tomada correctamente. Rostro detectado y procesado.');
            console.log('Descriptor facial calculado:', faceDescriptor);
          } else {
            alert('❌ No se detectó ningún rostro en la imagen. Por favor, toma una foto clara del rostro.');
            faceDescriptor = null;
            // Reset a video
            preview.style.display = 'none';
            video.style.display = 'block';
          }
        } catch (error) {
          console.error('Error procesando imagen:', error);
          alert('❌ Error procesando la imagen facial.');
          faceDescriptor = null;
          // Reset a video
          preview.style.display = 'none';
          video.style.display = 'block';
        }
      } else {
        // Modo sin reconocimiento facial
        faceDescriptor = null;
        alert('✅ Foto tomada correctamente.\n\nNota: El reconocimiento facial no está disponible porque los modelos de IA no se pudieron cargar.');
        console.log('Foto tomada sin procesamiento facial (modelos no disponibles)');
      }
    } else {
      alert('❌ Error al capturar la imagen.');
    }
  });

  // --------------------------
// CARGAR SUCURSALES Y PUESTOS DESDE BACKEND
  // --------------------------
  async function loadSucursales() {
    try {
      const response = await fetch('http://127.0.0.1:5000/get_sucursales');
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
      const response = await fetch('http://127.0.0.1:5000/get_puestos');
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
      const response = await fetch('http://127.0.0.1:5000/agregar_sucursal', {
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
      const response = await fetch('http://127.0.0.1:5000/agregar_puesto', {
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
      faceDescriptor: faceDescriptor ? Array.from(faceDescriptor) : null  // Convertir a array para JSON
    };

    console.log('📤 Enviando datos al backend:', {
      ...data,
      faceDescriptor: data.faceDescriptor ? 'Presente (' + data.faceDescriptor.length + ' valores)' : 'Nulo'
    });

    // Validación básica
    if (!data.nombre || !data.apellidoP || !data.sucursal || !data.puesto) {
      alert("Por favor, completa todos los campos obligatorios.");
      return;
    }

    try {
      const response = await fetch('http://127.0.0.1:5000/registrar_empleado_real', {
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
        // Reset camera view
        preview.style.display = 'none';
        video.style.display = 'block';
        faceDescriptor = null;  // Reset descriptor
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
