window.addEventListener('DOMContentLoaded', () => {
    // 1. Obtener referencias a los elementos del DOM
    // NO se usa 'as' ni '!' de TypeScript.
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const btnCamera = document.getElementById('btnCamera');
    const btnConfirm = document.getElementById('btnConfirm');
    const btnCancel = document.getElementById('btnCancel');
    const currentDateElem = document.getElementById('currentDate');
    const currentTimeElem = document.getElementById('currentTime');

    // --- Verificación de Elementos Clave ---
    // Si falta algún elemento crucial, detenemos la ejecución.
    if (!video || !canvas || !btnCamera || !btnConfirm || !btnCancel || !currentDateElem || !currentTimeElem) {
        console.error("Error: Faltan elementos HTML necesarios. Verifica tus IDs.");
        alert("Error de inicialización. Revisa la consola.");
        return;
    }

    // Para usar los elementos de forma más limpia, los convertimos a constantes ya verificadas.
    const videoElement = video;
    const canvasElement = canvas;
    const currentDateElement = currentDateElem;
    const currentTimeElement = currentTimeElem;

    let employeeNumber = null; // ID del empleado reconocido
    let knownFaces = []; // Almacenar rostros conocidos
    let recognitionSuccessful = false; // Estado del reconocimiento

    // --- Funciones de Utilidad ---

    // Función para refrescar la sesión de Flask
    async function refreshFlaskSession() {
        const userId = localStorage.getItem('user_id');
        console.log('🔄 Intentando refrescar sesión para userId:', userId);

        if (!userId) {
            console.error('❌ No hay userId en localStorage');
            return false;
        }

        try {
            console.log('📡 Enviando petición a /refresh_session...');
            const response = await fetch('http://127.0.0.1:5000/refresh_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ user_id: userId })
            });

            console.log('📡 Respuesta de /refresh_session:', response.status);
            const data = await response.json();
            console.log('📡 Datos de respuesta:', data);

            if (data.success) {
                console.log('✅ Sesión refrescada exitosamente');
                return true;
            } else {
                console.error('❌ Error refrescando sesión:', data.message);
                return false;
            }
        } catch (error) {
            console.error('❌ Error de red refrescando sesión:', error);
            return false;
        }
    }

    // Función para cargar el rostro del empleado logueado
    async function loadCurrentUserFace() {
        // Primero verificar si hay información del usuario en localStorage
        const userLoggedIn = localStorage.getItem('user_logged_in');
        const userId = localStorage.getItem('user_id');

        if (!userLoggedIn || !userId) {
            alert('❌ Debes iniciar sesión primero para usar esta función.');
            window.location.href = '/';
            return false;
        }

        // Refrescar la sesión de Flask
        const sessionRefreshed = await refreshFlaskSession();
        if (!sessionRefreshed) {
            alert('❌ Error al refrescar la sesión. Vuelve a iniciar sesión.');
            window.location.href = '/';
            return false;
        }

        // Esperar un poco para que la sesión se establezca
        await new Promise(resolve => setTimeout(resolve, 500));

        try {
            console.log('📡 Solicitando datos faciales del empleado actual...');
            // Enviar user_id como parámetro de query para asegurar que llegue
            const userId = localStorage.getItem('user_id');
            const response = await fetch(`http://127.0.0.1:5000/get_empleado_facial_actual?user_id=${userId}`, {
                credentials: 'include'
            });
            console.log('📡 Respuesta de get_empleado_facial_actual:', response.status);

            const data = await response.json();
            console.log('📡 Datos recibidos:', data);
            if (data.success) {
                const emp = data.empleado;
                knownFaces = [{
                    id_empleado: emp.id_empleado,
                    nombre: emp.nombre,
                    descriptor: emp.fotoperfil ? new Float32Array(JSON.parse(emp.fotoperfil)) : null
                }].filter(emp => emp.descriptor !== null);

                console.log(`✅ Cargado rostro del empleado actual: ${emp.nombre}`);
                return true;
            } else {
                console.error('Error cargando empleado actual:', data.message);
                alert('❌ Error: No se encontraron datos faciales. Registra tu foto primero.');
                // Redirigir al dashboard
                window.location.href = '../Dashboard/dashboard.html';
                return false;
            }
        } catch (error) {
            console.error('Error cargando rostro del empleado actual:', error);
            alert('❌ Error de conexión. Debes iniciar sesión primero.');
            window.location.href = '/';
            return false;
        }
    }

    // Función para reconocer rostro
    async function recognizeFace(canvas) {
        if (knownFaces.length === 0) {
            console.warn('No hay rostros conocidos para comparar');
            return null;
        }

        try {
            // Detectar rostro en la imagen capturada
            const detection = await faceapi.detectSingleFace(canvas, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();

            if (!detection) {
                console.log('No se detectó ningún rostro en la imagen');
                return null;
            }

            const capturedDescriptor = detection.descriptor;
            let bestMatch = null;
            let bestDistance = Infinity;

            // Comparar con todos los rostros conocidos
            for (const knownFace of knownFaces) {
                if (!knownFace.descriptor) continue;

                const distance = faceapi.euclideanDistance(capturedDescriptor, knownFace.descriptor);

                // Umbral de similitud (menor distancia = más similar)
                if (distance < 0.6 && distance < bestDistance) {
                    bestDistance = distance;
                    bestMatch = knownFace;
                }
            }

            if (bestMatch) {
                console.log(`👤 Rostro reconocido: ${bestMatch.nombre} (distancia: ${bestDistance.toFixed(3)})`);
                return bestMatch;
            } else {
                console.log('No se encontró coincidencia con rostros conocidos');
                return null;
            }

        } catch (error) {
            console.error('Error en reconocimiento facial:', error);
            return null;
        }
    }

    function updateDateTime() {
        const now = new Date();
        currentDateElement.textContent = now.toLocaleDateString();
        currentTimeElement.textContent = now.toLocaleTimeString();
    }

    // Inicializa y actualiza la hora cada segundo
    setInterval(updateDateTime, 1000);
    updateDateTime();

    // --- Control de la Cámara ---

    async function startCamera() {
        try {
            // Verifica soporte para getUserMedia
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                alert('Tu navegador no soporta el acceso a la cámara.');
                return;
            }
            
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            videoElement.srcObject = stream;
            videoElement.style.display = 'block';
            await videoElement.play();
        } catch (err) {
            console.error('No se puede acceder a la cámara', err);
            // Mensaje de ayuda para el usuario
            alert('No se puede acceder a la cámara. Asegúrate de estar en un servidor local (Live Server) y de haber otorgado los permisos.');
        }
    }
    
    // Inicializar aplicación
    async function initializeApp() {
        await startCamera();
        await loadCurrentUserFace();
    }

    initializeApp();

    // --- Inicializar estado de botones ---
    function initializeButtons() {
        btnConfirm.disabled = true;
        btnConfirm.style.opacity = '0.5';
        btnConfirm.style.cursor = 'not-allowed';
        recognitionSuccessful = false;
        employeeNumber = null;
    }

    // --- Actualizar estado de botones ---
    function updateButtonState() {
        if (recognitionSuccessful && employeeNumber) {
            btnConfirm.disabled = false;
            btnConfirm.style.opacity = '1';
            btnConfirm.style.cursor = 'pointer';
        } else {
            btnConfirm.disabled = true;
            btnConfirm.style.opacity = '0.5';
            btnConfirm.style.cursor = 'not-allowed';
        }
    }

    // Llamar al inicializar
    initializeButtons();

    // --- Manejo de Eventos ---

    // 📸 Botón para tomar la foto y hacer reconocimiento
    btnCamera.addEventListener('click', async () => {
        // Reset estado anterior
        recognitionSuccessful = false;
        employeeNumber = null;
        updateButtonState();

        // Asignamos el tamaño del canvas al tamaño del video actual
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        // Obtenemos el contexto 2D
        const ctx = canvasElement.getContext('2d');

        if (ctx) {
            ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            canvasElement.style.display = 'block';

            // Intentar reconocimiento facial
            try {
                const recognizedEmployee = await recognizeFace(canvasElement);
                if (recognizedEmployee) {
                    // ✅ RECONOCIMIENTO EXITOSO
                    employeeNumber = recognizedEmployee.id_empleado;
                    recognitionSuccessful = true;
                    updateButtonState();

                    alert(`✅ RECONOCIMIENTO EXITOSO\n\n👤 Empleado identificado: ${recognizedEmployee.nombre} (ID: ${employeeNumber})\n\nAhora puedes confirmar tu entrada.`);
                } else {
                    // ❌ RECONOCIMIENTO FALLIDO
                    recognitionSuccessful = false;
                    employeeNumber = null;
                    updateButtonState();

                    alert('❌ RECONOCIMIENTO FALLIDO\n\nNo se pudo identificar tu rostro.\n\nRazones posibles:\n• No estás registrado\n• La iluminación es insuficiente\n• Tu rostro no está completamente visible\n\nInténtalo de nuevo.');
                }
            } catch (error) {
                console.error('Error en reconocimiento facial:', error);
                recognitionSuccessful = false;
                employeeNumber = null;
                updateButtonState();

                alert('❌ ERROR EN RECONOCIMIENTO\n\nOcurrió un error técnico.\n\nInténtalo de nuevo.');
            }
        } else {
            console.error('No se pudo obtener el contexto 2D del canvas.');
            alert('❌ Error al capturar la imagen.');
        }
    });

    // ✅ Botón de Confirmar (Registrar Entrada)
    btnConfirm.addEventListener('click', async () => {
        // Verificar que el reconocimiento fue exitoso
        if (!recognitionSuccessful || !employeeNumber) {
            alert('❌ Debes completar el reconocimiento facial primero.');
            return;
        }

        // Deshabilitar botón mientras procesa
        btnConfirm.disabled = true;
        btnConfirm.textContent = 'Procesando...';

        try {
            // Asegurar que la sesión esté activa antes de registrar
            console.log('🔄 Asegurando sesión activa antes de registrar...');
            const sessionCheck = await fetch('http://127.0.0.1:5000/refresh_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({ user_id: localStorage.getItem('user_id') })
            });

            if (!sessionCheck.ok) {
                throw new Error('Sesión expirada. Vuelve a iniciar sesión.');
            }

            // Enviar datos a la base de datos
            console.log('📤 Enviando registro de asistencia...');
            const response = await fetch('http://127.0.0.1:5000/registrar_asistencia', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    tipo: 'entrada',  // Para entrada
                    empleado_id: employeeNumber,
                    user_id: localStorage.getItem('user_id')  // Agregar user_id para autenticación
                })
            });

            console.log('📡 Respuesta del servidor:', response.status);
            const result = await response.json();
            console.log('📡 Datos de respuesta:', result);

            if (result.success) {
                // ✅ REGISTRO EXITOSO EN BASE DE DATOS
                alert(`🎉 ¡REGISTRO COMPLETADO CON ÉXITO!\n\n✅ Entrada registrada para: ${result.empleado}\n📅 Fecha: ${result.fecha}\n🕐 Hora: ${result.hora}\n\nTu asistencia ha sido guardada correctamente.`);

                // Reset para nueva entrada si es necesario
                initializeButtons();
                canvasElement.style.display = 'none';

            } else {
                // ❌ ERROR AL GUARDAR
                alert(`❌ Error al guardar: ${result.message}`);
                btnConfirm.disabled = false;
                btnConfirm.textContent = 'Confirmar';
            }

        } catch (error) {
            console.error('Error al registrar asistencia:', error);
            alert(`❌ Error: ${error.message}`);
            btnConfirm.disabled = false;
            btnConfirm.textContent = 'Confirmar';
        }
    });

    // ❌ Botón de Cancelar
    btnCancel.addEventListener('click', () => {
        if (confirm('¿Estás seguro de que quieres cancelar? Se perderá el progreso actual.')) {
            initializeButtons();
            canvasElement.style.display = 'none';
            alert('Registro cancelado.');
        }
    });
});
