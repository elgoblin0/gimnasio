// =============================================
// Frontend del gimnasio
// Toda la lógica de las reglas está en el backend (app.py).
// Aquí solo se llama a la API y se muestra lo que devuelve.
// =============================================


// ---------------------------------------------
// FUNCIONES DE AYUDA
// ---------------------------------------------

// Llama a la API y devuelve { ok: true/false, datos: el JSON de la respuesta }
async function llamarApi(url, metodo = "GET", datos = null) {
    const opciones = {
        method: metodo,
        headers: { "Content-Type": "application/json" },
    };
    if (datos !== null) {
        opciones.body = JSON.stringify(datos);
    }
    const respuesta = await fetch(url, opciones);
    const json = await respuesta.json();
    return { ok: respuesta.ok, datos: json };
}

// Muestra la franja de mensaje: verde si va bien, roja si es error
function mostrarMensaje(texto, esError) {
    const div = document.getElementById("mensaje");
    div.textContent = texto;
    if (esError) {
        div.className = "mensaje error";
    } else {
        div.className = "mensaje ok";
    }
}

// Muestra el mensaje o el error que devolvió la API
function mostrarResultado(resultado) {
    if (resultado.ok) {
        mostrarMensaje(resultado.datos.mensaje, false);
    } else {
        mostrarMensaje(resultado.datos.error, true);
    }
}

// "2026-10-25" -> "25/10/2026"
function formatearFecha(fecha) {
    const partes = fecha.split("-");
    return partes[2] + "/" + partes[1] + "/" + partes[0];
}

// Etiqueta de color para el estado: "Por vencer" -> clase "por-vencer"
function etiquetaEstado(estado) {
    const clase = estado.toLowerCase().replace(" ", "-");
    return '<span class="estado ' + clase + '">' + estado + "</span>";
}

// Rellena un desplegable con los planes y marca el elegido (si hay)
async function cargarPlanes(idSelect, planElegido) {
    const resultado = await llamarApi("/api/planes");
    const select = document.getElementById(idSelect);
    select.innerHTML = "";
    for (const plan of resultado.datos) {
        const opcion = document.createElement("option");
        opcion.value = plan.id;
        opcion.textContent = plan.nombre;
        if (plan.id === planElegido) {
            opcion.selected = true;
        }
        select.appendChild(opcion);
    }
}


// ---------------------------------------------
// PÁGINA DE SOCIOS (index.html)
// ---------------------------------------------

// Carga la tabla de socios
async function cargarSocios() {
    const resultado = await llamarApi("/api/socios");
    const tabla = document.getElementById("tabla-socios");
    tabla.innerHTML = "";
    for (const socio of resultado.datos) {
        tabla.innerHTML +=
            "<tr>" +
            "<td>" + socio.nombre + "</td>" +
            "<td>" + socio.dni + "</td>" +
            "<td>" + socio.plan + "</td>" +
            "<td>" + formatearFecha(socio.fecha_vencimiento) + "</td>" +
            "<td>" + etiquetaEstado(socio.estado) + "</td>" +
            "<td class='acciones'>" +
            "<button onclick='hacerEntrada(" + socio.id + ")'>Entrada</button> " +
            "<a class='boton' href='socio.html?id=" + socio.id + "'>Ver ficha</a>" +
            "</td>" +
            "</tr>";
    }
}

// Check-in: el backend decide si puede entrar (regla 3)
async function hacerEntrada(id) {
    const resultado = await llamarApi("/api/socios/" + id + "/checkin", "POST");
    mostrarResultado(resultado);
    cargarSocios();
}

// Alta de un socio nuevo
async function darDeAlta(evento) {
    evento.preventDefault(); // evita que el formulario recargue la página

    const datos = {
        nombre: document.getElementById("nombre").value,
        dni: document.getElementById("dni").value,
        telefono: document.getElementById("telefono").value,
        peso: document.getElementById("peso").value,
        altura: document.getElementById("altura").value,
        objetivo: document.getElementById("objetivo").value,
        nivel: document.getElementById("nivel").value,
        plan_id: document.getElementById("plan").value,
    };

    const resultado = await llamarApi("/api/socios", "POST", datos);
    mostrarResultado(resultado);
    if (resultado.ok) {
        document.getElementById("form-alta").reset();
        cargarSocios();
    }
}


// ---------------------------------------------
// FICHA DEL SOCIO (socio.html)
// ---------------------------------------------

// Lee el id de la URL: socio.html?id=3 -> "3"
function idDeLaUrl() {
    const parametros = new URLSearchParams(window.location.search);
    return parametros.get("id");
}

// Carga todos los datos de la ficha
async function cargarFicha() {
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl());
    if (!resultado.ok) {
        mostrarMensaje(resultado.datos.error, true);
        return;
    }
    const socio = resultado.datos;

    // Cabecera y datos
    document.getElementById("nombre").textContent = socio.nombre;
    document.getElementById("estado").innerHTML = etiquetaEstado(socio.estado);
    document.getElementById("dni").textContent = socio.dni;
    document.getElementById("telefono").textContent = socio.telefono;
    document.getElementById("objetivo").textContent = socio.objetivo;
    document.getElementById("nivel").textContent = socio.nivel;

    // Plan
    document.getElementById("plan").textContent = socio.plan;
    document.getElementById("vencimiento").textContent = formatearFecha(socio.fecha_vencimiento);
    document.getElementById("entradas").textContent = socio.entradas_semana + " / " + socio.dias_por_semana;
    cargarPlanes("plan-renovar", socio.plan_id);

    // Salud (regla 4)
    document.getElementById("peso").textContent = socio.peso;
    document.getElementById("altura").textContent = socio.altura;
    document.getElementById("imc").textContent = socio.imc + " (" + socio.categoria_imc + ")";

    // Rutina (regla 5)
    document.getElementById("rutina-nombre").textContent = socio.rutina.nombre;
    document.getElementById("rutina-descripcion").textContent = socio.rutina.descripcion;

    // Progreso (regla 6)
    const progreso = document.getElementById("progreso");
    if (socio.progreso.resultado === "Faltan datos") {
        progreso.textContent = "Faltan datos";
        progreso.className = "";
    } else {
        let diferencia = socio.progreso.diferencia;
        if (diferencia > 0) {
            diferencia = "+" + diferencia;
        }
        progreso.textContent = diferencia + " kg → " + socio.progreso.resultado;
        if (socio.progreso.resultado === "Va bien") {
            progreso.className = "va-bien";
        } else {
            progreso.className = "va-mal";
        }
    }

    // Historial de peso
    const tabla = document.getElementById("tabla-pesos");
    tabla.innerHTML = "";
    for (const registro of socio.historial_peso) {
        tabla.innerHTML +=
            "<tr><td>" + formatearFecha(registro.fecha) + "</td><td>" + registro.peso + "</td></tr>";
    }
}

// Renovar el plan (regla 1)
async function renovar() {
    const datos = { plan_id: document.getElementById("plan-renovar").value };
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/renovar", "POST", datos);
    mostrarResultado(resultado);
    cargarFicha();
}

// Registrar un nuevo peso
async function registrarPeso() {
    const datos = { peso: document.getElementById("nuevo-peso").value };
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/peso", "POST", datos);
    mostrarResultado(resultado);
    if (resultado.ok) {
        document.getElementById("nuevo-peso").value = "";
        cargarFicha();
    }
}
