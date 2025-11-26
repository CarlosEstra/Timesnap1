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

    let employeeNumber = 12;

    // --- Funciones de Utilidad ---

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
    
    startCamera();

    // --- Manejo de Eventos ---

    // 📸 Botón para tomar la foto
    btnCamera.addEventListener('click', () => {
        // Asignamos el tamaño del canvas al tamaño del video actual
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;
        
        // Obtenemos el contexto 2D
        const ctx = canvasElement.getContext('2d');
        
        if (ctx) {
            ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
            canvasElement.style.display = 'block';
            alert('Foto tomada correctamente');
        } else {
            console.error('No se pudo obtener el contexto 2D del canvas.');
            alert('Error al capturar la imagen.');
        }
    });

    // ✅ Botón de Confirmar (Registrar Salida)
    btnConfirm.addEventListener('click', () => {
        // Convertimos la imagen a Base64 para simular el envío
        const photoBase64 = canvasElement.toDataURL('image/jpeg', 0.8);
        
        console.log("--- Registro de Salida ---");
        console.log("Empleado:", employeeNumber);
        console.log("Tipo:", 'Salida');
        // Se recorta la cadena Base64 para no saturar la consola
        console.log("Photo Base64 (Recorte):", photoBase64.substring(0, 50) + '...'); 
        console.log("--------------------------");
        
        alert('Salida registrada ✅');
    });

    // ❌ Botón de Cancelar
    btnCancel.addEventListener('click', () => {
        alert('Registro cancelado');
    });
});