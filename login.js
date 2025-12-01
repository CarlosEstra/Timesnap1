const loginForm = document.getElementById('loginForm');
const employeeNumberInput = document.getElementById('employeeNumber');
const passwordInput = document.getElementById('password');

// ⚠️ El HTML no contiene un elemento con ID 'message-display',
// por lo que DEBES añadir un <div> debajo del <form> en tu HTML para que esto funcione.
const messageDisplay = document.getElementById('message-display'); 

/**
 * Limpia el área de visualización de mensajes y oculta el elemento.
 */
function clearMessage() {
    if (!messageDisplay) return;
    messageDisplay.textContent = '';
    messageDisplay.classList.add('hidden');
    messageDisplay.classList.remove('success-message', 'error-message');
}

/**
 * Muestra un mensaje de estado (éxito o error) en la UI.
 * @param {string} message - El texto a mostrar.
 * @param {boolean} isSuccess - True para éxito, false para error.
 */
function displayMessage(message, isSuccess) {
    if (!messageDisplay) return;
    clearMessage();
    messageDisplay.textContent = message;
    messageDisplay.classList.remove('hidden');

    if (isSuccess) {
        messageDisplay.classList.add('success-message');
    } else {
        messageDisplay.classList.add('error-message');
    }
}

/**
 * Maneja la lógica del intento de inicio de sesión comunicándose con el backend.
 */
async function onLogin(event) {
    event.preventDefault();
    clearMessage();

    const employeeNumber = employeeNumberInput.value.trim();
    const password = passwordInput.value.trim();
    
    // El número de empleado es CHAR(8) en la DB, no un número puro
    if (!employeeNumber || !password) {
        displayMessage('Por favor, completa todos los campos.', false);
        return;
    }

    // Deshabilitar botón mientras se procesa la solicitud
    const loginButton = loginForm.querySelector('button');
    loginButton.disabled = true;
    
    // 💡 CORRECCIÓN CRÍTICA: Usar la URL absoluta de Flask (puerto 5000)
    const FLASK_LOGIN_URL = 'http://127.0.0.1:5000/login'; 

    // 1. Realizar la solicitud al backend (Flask)
    try {
        // Usamos la URL absoluta de Flask para evitar el error 405/CORS
        const response = await fetch(FLASK_LOGIN_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // El backend Flask espera 'username' y 'password'
            body: JSON.stringify({
                username: employeeNumber, // Usamos el número de empleado como username
                password: password
            })
        });

        // ⚠️ Nota: response.json() debe hacerse ANTES de verificar el estado.
        // Si el servidor falla (ej: 503) pero envia un JSON de error, funciona.
        // Si el servidor falla y NO envia JSON (causa el 'Unexpected end of JSON input'), 
        // el catch lo manejará.

        // Intenta parsear la respuesta. Esto es el punto donde fallaba antes.
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            // Este catch maneja el 'Unexpected end of JSON input' si Flask no responde con JSON
            console.error('Error al parsear JSON (respuesta vacía o corrupta):', jsonError);
            displayMessage('Error interno del servidor. (Respuesta no JSON)', false);
            return; // Detenemos la ejecución aquí si el JSON es inválido
        }


        if (response.ok && data.success) {
            // INICIO DE SESIÓN EXITOSO
            console.log('Inicio de sesión exitoso ✅');

            // Verificar si es administrador (id_puestos = '3')
            const isAdmin = data.puesto === '3'; // Asumiendo que se devuelve como string

            if (isAdmin) {
                displayMessage(`¡Inicio de sesión exitoso! Redirigiendo al Dashboard...`, true);
                // Redirección al dashboard para administradores
                window.location.href = 'dashboardweb/web.html';
            } else {
                displayMessage(`¡Inicio de sesión exitoso! Redirigiendo a Registrar Entrada...`, true);
                // Redirección a la página HTML de registrar entrada para empleados normales
                window.location.href = 'registrar_entrada/registrar_entrada.html';
            }
            
        } else {
            // FALLO EN LA AUTENTICACIÓN (Código 401, 503, etc.)
            console.log(`Fallo de autenticación o DB. Código: ${response.status}`, data);
            displayMessage(data.message || 'Error de servidor. Inténtalo más tarde.', false);
            passwordInput.value = '';
            passwordInput.focus();
        }

    } catch (error) {
        // Este catch maneja errores de red (servidor Flask apagado)
        console.error('Error de red al intentar iniciar sesión:', error);
        displayMessage('Error de conexión con el servidor. Verifica que Flask esté corriendo en el puerto 5000.', false);
    } finally {
        loginButton.disabled = false; // Habilitar botón de nuevo
    }
}

// Adjuntar el listener de eventos
if (loginForm) {
    loginForm.addEventListener('submit', onLogin);
}
