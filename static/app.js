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

    // Sin sesión: se va al login. La promesa queda sin resolver porque la página se está yendo.
    // En el propio login, un 401 significa que la contraseña es incorrecta.
    if (respuesta.status === 401 && url !== "/api/login") {
        window.location.href = "login.html";
        return new Promise(() => {});
    }

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

// Convierte un dato en texto seguro para usarlo dentro de innerHTML:
// "<script>" se muestra como texto y no se ejecuta
function escaparHtml(valor) {
    const div = document.createElement("div");
    div.textContent = valor;
    return div.innerHTML;
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
        opcion.textContent = plan.nombre + " (" + plan.precio + ")";
        if (plan.id === planElegido) {
            opcion.selected = true;
        }
        select.appendChild(opcion);
    }
}


// ---------------------------------------------
// LOGIN Y USUARIOS (regla 15)
// ---------------------------------------------

// Iniciar sesión y entrar al sistema
async function iniciarSesion(evento) {
    evento.preventDefault();
    const datos = {
        usuario: document.getElementById("usuario").value,
        clave: document.getElementById("clave").value,
    };
    const resultado = await llamarApi("/api/login", "POST", datos);
    if (resultado.ok) {
        window.location.href = "index.html";
    } else {
        mostrarResultado(resultado);
    }
}

// Cerrar sesión y volver al login
async function cerrarSesion() {
    await llamarApi("/api/logout", "POST");
    window.location.href = "login.html";
}

// Muestra quién entró. La clase del rol oculta lo que ese rol no puede usar:
// es solo para no mostrarlo, quien lo hace cumplir es la API.
async function mostrarSesion() {
    const resultado = await llamarApi("/api/sesion");
    const usuario = resultado.datos;
    document.body.classList.add("rol-" + usuario.rol);
    document.getElementById("sesion").innerHTML = `
        ${escaparHtml(usuario.nombre)} · ${escaparHtml(usuario.rol)}
        <button onclick="cerrarSesion()">Salir</button>`;
}

// Carga el listado de usuarios
async function cargarUsuarios() {
    const resultado = await llamarApi("/api/usuarios");
    if (!resultado.ok) {
        mostrarResultado(resultado);
        return;
    }
    const tabla = document.getElementById("tabla-usuarios");
    tabla.innerHTML = "";
    for (const usuario of resultado.datos) {
        let estado = "Inactivo";
        let accion = "Activar";
        if (usuario.activo) {
            estado = "Activo";
            accion = "Desactivar";
        }
        tabla.innerHTML += `
            <tr>
                <td>${escaparHtml(usuario.nombre)}</td>
                <td>${escaparHtml(usuario.usuario)}</td>
                <td>${escaparHtml(usuario.rol)}</td>
                <td>${estado}</td>
                <td class="acciones"><button class="secundario" onclick="cambiarActivo(${usuario.id}, ${!usuario.activo})">${accion}</button></td>
            </tr>`;
    }
}

// Crear un usuario nuevo
async function crearUsuario(evento) {
    evento.preventDefault();
    const datos = {
        nombre: document.getElementById("usuario-nombre").value,
        usuario: document.getElementById("usuario-usuario").value,
        clave: document.getElementById("usuario-clave").value,
        rol: document.getElementById("usuario-rol").value,
    };
    const resultado = await llamarApi("/api/usuarios", "POST", datos);
    mostrarResultado(resultado);
    if (resultado.ok) {
        document.getElementById("form-usuario").reset();
        cargarUsuarios();
    }
}

// Activar o desactivar un usuario
async function cambiarActivo(id, activo) {
    const resultado = await llamarApi("/api/usuarios/" + id, "PATCH", { activo: activo });
    mostrarResultado(resultado);
    cargarUsuarios();
}


// ---------------------------------------------
// PÁGINA DE SOCIOS (index.html)
// ---------------------------------------------

// Buscar también funciona al pulsar Enter en el formulario.
function buscarSocios(evento) {
    evento.preventDefault();
    cargarSocios();
}

function limpiarBusqueda() {
    document.getElementById("form-busqueda").reset();
    cargarSocios();
}

// Carga la tabla usando los filtros actuales, también después de un alta o check-in.
async function cargarSocios() {
    const parametros = new URLSearchParams();
    const texto = document.getElementById("busqueda").value.trim();
    const estado = document.getElementById("estado-busqueda").value;
    if (texto) parametros.set("q", texto);
    if (estado) parametros.set("estado", estado);
    const resultado = await llamarApi("/api/socios?" + parametros.toString());
    if (!resultado.ok) {
        mostrarResultado(resultado);
        return;
    }
    const tabla = document.getElementById("tabla-socios");
    tabla.innerHTML = "";
    if (resultado.datos.length === 0) {
        tabla.innerHTML = '<tr><td colspan="6">No se encontraron socios</td></tr>';
        return;
    }
    for (const socio of resultado.datos) {
        // T10: si entró hoy y no salió, el botón es "Salida" en vez de "Entrada"
        let botonAcceso = `<button class="secundario" onclick="hacerEntrada(${socio.id})">Entrada</button>`;
        let adentro = "";
        if (socio.adentro) {
            botonAcceso = `<button onclick="hacerSalida(${socio.id})">Salida</button>`;
            adentro = ' <span class="adentro">Adentro</span>';
        }
        tabla.innerHTML += `
            <tr>
                <td>${escaparHtml(socio.nombre)}${adentro}</td>
                <td>${escaparHtml(socio.ci)}</td>
                <td>${escaparHtml(socio.plan)}</td>
                <td>${escaparHtml(formatearFecha(socio.fecha_vencimiento))}</td>
                <td>${etiquetaEstado(socio.estado)}</td>
                <td class="acciones">
                    ${botonAcceso}
                    <a class="boton" href="socio.html?id=${socio.id}">Ver ficha</a>
                    <button class="boton-eliminar solo-admin" onclick="eliminarSocio(${socio.id})">Eliminar</button>
                </td>
            </tr>`;
    }
}

// Carga la tabla para editar los precios de los planes
async function cargarPrecios() {
    const resultado = await llamarApi("/api/planes");
    const tabla = document.getElementById("tabla-precios");
    tabla.innerHTML = "";
    for (const plan of resultado.datos) {
        tabla.innerHTML += `
            <tr>
                <td>${escaparHtml(plan.nombre)}</td>
                <td>${plan.duracion_dias}</td>
                <td><input id="precio-${plan.id}" type="number" step="0.01" value="${plan.precio}"></td>
                <td class="acciones"><button class="secundario" onclick="guardarPrecio(${plan.id})">Guardar</button></td>
            </tr>`;
    }
}

// Guarda el precio nuevo de un plan
async function guardarPrecio(id) {
    const datos = { precio: document.getElementById("precio-" + id).value };
    const resultado = await llamarApi("/api/planes/" + id, "PUT", datos);
    mostrarResultado(resultado);
    if (resultado.ok) {
        cargarPrecios();
        cargarPlanes("plan", null);
    }
}

// Check-in: el backend decide si puede entrar (regla 3)
async function hacerEntrada(id) {
    const resultado = await llamarApi("/api/socios/" + id + "/checkin", "POST");
    mostrarResultado(resultado);
    cargarSocios();
}

// Salida (T10): cierra la entrada de hoy, así deja de contar en la ocupación
async function hacerSalida(id) {
    const resultado = await llamarApi("/api/socios/" + id + "/salida", "POST");
    mostrarResultado(resultado);
    cargarSocios();
}

// Eliminar un socio
async function eliminarSocio(id) {
    const confirmar = confirm(
        "¿Estás seguro de que quieres eliminar este socio? " +
        "También se eliminarán sus asistencias y su historial de peso. " +
        "Esta acción no se puede deshacer."
    );

    if (!confirmar) {
        return;
    }

    const resultado = await llamarApi("/api/socios/" + id, "DELETE");
    mostrarResultado(resultado);

    if (resultado.ok) {
        await cargarSocios();
    }
}


// Alta de un socio nuevo
async function darDeAlta(evento) {
    evento.preventDefault(); // evita que el formulario recargue la página

    const datos = {
        nombre: document.getElementById("nombre").value,
        ci: document.getElementById("ci").value,
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
// DASHBOARD (dashboard.html)
// ---------------------------------------------

// Carga el dashboard: tarjetas, socios en riesgo (regla 10) y listas por estado
async function cargarDashboard() {
    const resultado = await llamarApi("/api/dashboard");
    if (!resultado.ok) {
        mostrarResultado(resultado);
        return;
    }
    const datos = resultado.datos;

    barrasPorEstado(datos.totales);
    medidorOcupacion(datos.adentro_ahora, datos.aforo);

    // Gráfico de ingresos: una barra por mes
    const ingresos = [];
    for (const mes of datos.ingresos_por_mes) {
        ingresos.push({ etiqueta: mes.mes, valor: mes.total, detalle: mes.mes + ": " + formatearNumero(mes.total) });
    }
    graficoDeBarras("grafico-ingresos", ingresos, 1);

    // Gráfico de entradas: una barra por día, con la fecha escrita cada 7 días
    const entradas = [];
    let entradasSemana = 0;
    datos.entradas_por_dia.forEach((dia, posicion) => {
        const fecha = formatearFecha(dia.fecha).slice(0, 5);  // "25/10/2026" -> "25/10"
        let texto = dia.cantidad + " entradas";
        if (dia.cantidad === 1) {
            texto = "1 entrada";
        }
        entradas.push({ etiqueta: fecha, valor: dia.cantidad, detalle: fecha + ": " + texto });
        if (posicion >= datos.entradas_por_dia.length - 7) {
            entradasSemana += dia.cantidad;
        }
    });
    graficoDeBarras("grafico-entradas", entradas, 7);

    document.getElementById("entradas-semana").textContent = entradasSemana;
    document.getElementById("socios-activos").textContent = datos.totales[0].cantidad;
    document.getElementById("mes").textContent = datos.mes;
    document.getElementById("ingresos-mes").textContent = formatearNumero(datos.ingresos_mes);
    if (datos.plan_mas_vendido === null) {
        document.getElementById("plan-mas-vendido").textContent = "Sin ventas";
    } else {
        document.getElementById("plan-mas-vendido").textContent =
            datos.plan_mas_vendido + " (" + datos.ventas_plan_mas_vendido + ")";
    }

    const riesgo = document.getElementById("tabla-riesgo");
    riesgo.innerHTML = "";
    if (datos.en_riesgo.length === 0) {
        riesgo.innerHTML = '<tr><td colspan="5">No hay socios en riesgo</td></tr>';
    }
    for (const socio of datos.en_riesgo) {
        // Sin entradas ni pagos no hay desde cuándo contar
        let dias = "Sin datos";
        if (socio.dias_sin_entrar !== null) {
            dias = socio.dias_sin_entrar;
        }
        riesgo.innerHTML += `
            <tr>
                <td>${escaparHtml(socio.nombre)}</td>
                <td>${escaparHtml(socio.plan)}</td>
                <td>${etiquetaEstado(socio.estado)}</td>
                <td>${dias}</td>
                <td><a class="boton" href="socio.html?id=${socio.id}">Ver ficha</a></td>
            </tr>`;
    }

    const listas = document.getElementById("listas-estado");
    listas.innerHTML = "";
    for (const lista of datos.listas) {
        listas.innerHTML += `
            <section>
                <h2>${etiquetaEstado(lista.estado)} ${lista.socios.length}</h2>
                ${tablaDeSocios(lista.socios)}
            </section>`;
    }
}

// 14000 -> "14.000" (separador de miles, sin decimales si no hacen falta)
function formatearNumero(numero) {
    return numero.toLocaleString("es", { maximumFractionDigits: 2, useGrouping: "always" });
}

// Medio círculo que se llena según cuánta gente hay adentro sobre el aforo (T10).
// El arco de color es el mismo camino que el de fondo, pero dibujado solo en parte con stroke-dasharray.
function medidorOcupacion(adentro, aforo) {
    const porcentaje = Math.min(adentro / aforo, 1);
    const radio = 90;
    const largo = Math.PI * radio;  // largo del medio círculo
    const arco = `M10,100 A${radio},${radio} 0 0 1 190,100`;

    let nivel = "Tranquilo";
    if (porcentaje >= 0.85) {
        nivel = "Lleno";
    } else if (porcentaje >= 0.5) {
        nivel = "Moderado";
    }

    document.getElementById("ocupacion").innerHTML = `
        <svg viewBox="0 0 200 110" role="img" aria-label="${adentro} personas adentro de ${aforo}">
            <path class="medidor-fondo" d="${arco}"></path>
            <path class="medidor-valor" d="${arco}" stroke-dasharray="${largo * porcentaje} ${largo}"></path>
        </svg>
        <div class="medidor-texto">
            <span class="medidor-numero">${adentro}</span>
            <span>de ${aforo} personas · ${Math.round(porcentaje * 100)}%</span>
            <strong>${nivel}</strong>
        </div>`;
}

// Una fila por estado: el nombre, una barra proporcional y la cantidad.
// Es HTML común: el ancho de la barra es el porcentaje sobre el total de socios.
function barrasPorEstado(totales) {
    let total = 0;
    for (const fila of totales) {
        total += fila.cantidad;
    }
    const contenedor = document.getElementById("barras-estado");
    contenedor.innerHTML = "";
    for (const fila of totales) {
        let porcentaje = 0;
        if (total > 0) {
            porcentaje = Math.round(fila.cantidad / total * 100);
        }
        contenedor.innerHTML += `
            <div class="barra-estado">
                ${etiquetaEstado(fila.estado)}
                <div class="pista"><div class="relleno" style="width: ${porcentaje}%"></div></div>
                <span class="cantidad">${fila.cantidad} <span class="porcentaje">${porcentaje}%</span></span>
            </div>`;
    }
}

// Gráfico de barras dibujado a mano con SVG (sin librerías).
// barras: lista de { etiqueta, valor, detalle }. cadaCuanto: cada cuántas barras se escribe la etiqueta abajo.
function graficoDeBarras(idContenedor, barras, cadaCuanto) {
    const contenedor = document.getElementById(idContenedor);
    const ancho = contenedor.clientWidth;
    const alto = 220;
    const izquierda = 48;  // lugar para los números del eje
    const abajo = 28;      // lugar para las etiquetas de abajo
    const arriba = 8;
    const altoUtil = alto - abajo - arriba;

    // El máximo del eje se redondea hacia arriba (ej: 9000 -> 10000) para que las líneas queden en números redondos
    let maximo = 0;
    for (const barra of barras) {
        maximo = Math.max(maximo, barra.valor);
    }
    maximo = redondearArriba(maximo);

    const anchoColumna = (ancho - izquierda) / barras.length;
    const anchoBarra = Math.max(2, Math.min(36, anchoColumna * 0.6));
    let svg = `<svg width="${ancho}" height="${alto}" role="img" aria-label="Gráfico de barras">`;

    // Tres líneas horizontales de referencia: 0, la mitad y el máximo
    for (const parte of [0, 0.5, 1]) {
        const y = arriba + altoUtil - parte * altoUtil;
        svg += `<line class="linea-guia" x1="${izquierda}" x2="${ancho}" y1="${y}" y2="${y}"></line>`;
        svg += `<text class="eje" x="${izquierda - 8}" y="${y + 4}" text-anchor="end">${formatearNumero(maximo * parte)}</text>`;
    }

    barras.forEach((barra, posicion) => {
        const x = izquierda + posicion * anchoColumna;
        const base = arriba + altoUtil;
        const altoBarra = barra.valor / maximo * altoUtil;
        const xBarra = x + (anchoColumna - anchoBarra) / 2;

        // Cada columna tiene un rectángulo invisible del alto completo: así es fácil pasarle el mouse
        svg += `<g class="columna" data-detalle="${escaparHtml(barra.detalle)}">`;
        svg += `<rect class="zona" x="${x}" y="${arriba}" width="${anchoColumna}" height="${altoUtil}"></rect>`;
        if (altoBarra > 0) {
            svg += `<path class="barra" d="${caminoBarra(xBarra, base, anchoBarra, altoBarra)}"></path>`;
        }
        svg += "</g>";

        if (posicion % cadaCuanto === 0) {
            svg += `<text class="eje" x="${x + anchoColumna / 2}" y="${alto - 8}" text-anchor="middle">${escaparHtml(barra.etiqueta)}</text>`;
        }
    });
    svg += "</svg>";

    contenedor.innerHTML = svg + '<div class="tooltip" hidden></div>';
    mostrarDetalleAlPasar(contenedor);
}

// Rectángulo con las dos esquinas de arriba redondeadas (las de abajo quedan rectas, apoyadas en el eje)
function caminoBarra(x, base, ancho, alto) {
    const radio = Math.min(4, ancho / 2, alto);
    const y = base - alto;
    return `M${x},${base} V${y + radio} Q${x},${y} ${x + radio},${y} ` +
        `H${x + ancho - radio} Q${x + ancho},${y} ${x + ancho},${y + radio} V${base} Z`;
}

// 0 -> 1, 3 -> 4, 7 -> 10, 9000 -> 10000, 14000 -> 20000: el primer número "redondo" que no es menor.
// Siempre da un número par, así la línea de la mitad no queda en 2,5
function redondearArriba(numero) {
    if (numero <= 2) {
        return 2;
    }
    const potencia = Math.pow(10, Math.floor(Math.log10(numero)));
    for (const paso of [1, 2, 4, 6, 10]) {
        if (paso * potencia >= numero) {
            return paso * potencia;
        }
    }
}

// Al pasar el mouse por una columna se muestra su detalle en un cartelito
function mostrarDetalleAlPasar(contenedor) {
    const tooltip = contenedor.querySelector(".tooltip");
    for (const columna of contenedor.querySelectorAll(".columna")) {
        columna.addEventListener("mousemove", (evento) => {
            const caja = contenedor.getBoundingClientRect();
            tooltip.textContent = columna.dataset.detalle;
            tooltip.hidden = false;
            tooltip.style.left = (evento.clientX - caja.left) + "px";
            tooltip.style.top = (evento.clientY - caja.top) + "px";
        });
        columna.addEventListener("mouseleave", () => {
            tooltip.hidden = true;
        });
    }
}

// Tabla simple de socios con enlace a su ficha (listas del dashboard)
function tablaDeSocios(socios) {
    if (socios.length === 0) {
        return "<p>Ninguno</p>";
    }
    let filas = "";
    for (const socio of socios) {
        filas += `
            <tr>
                <td>${escaparHtml(socio.nombre)}</td>
                <td>${escaparHtml(socio.plan)}</td>
                <td>${escaparHtml(formatearFecha(socio.fecha_vencimiento))}</td>
                <td><a class="boton" href="socio.html?id=${socio.id}">Ver ficha</a></td>
            </tr>`;
    }
    return `
        <div class="tabla-scroll">
            <table>
                <thead>
                    <tr><th>Nombre</th><th>Plan</th><th>Vencimiento</th><th></th></tr>
                </thead>
                <tbody>${filas}</tbody>
            </table>
        </div>`;
}


// ---------------------------------------------
// FICHA DEL SOCIO (socio.html)
// ---------------------------------------------

// Lee el id de la URL: socio.html?id=3 -> "3"
function idDeLaUrl() {
    const parametros = new URLSearchParams(window.location.search);
    return parametros.get("id");
}

// Carga la ficha completa y reparte los datos en cada bloque
async function cargarFicha() {
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl());
    if (!resultado.ok) {
        mostrarMensaje(resultado.datos.error, true);
        return;
    }
    const socio = resultado.datos;

    mostrarDatos(socio);
    mostrarPlan(socio);
    mostrarSalud(socio);
    mostrarProgreso(socio);
    mostrarHistorial(socio);
    mostrarPagos(socio);
    mostrarAuditoria(socio);
    mostrarSeguimiento(socio);
}

// Cabecera, datos personales y formulario de edición con los valores actuales
function mostrarDatos(socio) {
    document.getElementById("nombre").textContent = socio.nombre;
    document.getElementById("estado").innerHTML = etiquetaEstado(socio.estado);
    document.getElementById("ci").textContent = socio.ci;
    document.getElementById("telefono").textContent = socio.telefono;
    document.getElementById("objetivo").textContent = socio.objetivo;
    document.getElementById("nivel").textContent = socio.nivel;

    document.getElementById("editar-nombre").value = socio.nombre;
    document.getElementById("editar-ci").value = socio.ci;
    document.getElementById("editar-telefono").value = socio.telefono;
    document.getElementById("editar-altura").value = socio.altura;
    document.getElementById("editar-objetivo").value = socio.objetivo;
    document.getElementById("editar-nivel").value = socio.nivel;
}

// Plan, vencimiento y entradas de la semana (regla 1 y 3)
function mostrarPlan(socio) {
    document.getElementById("plan").textContent = socio.plan;
    document.getElementById("vencimiento").textContent = formatearFecha(socio.fecha_vencimiento);
    document.getElementById("entradas").textContent = socio.entradas_semana + " / " + socio.dias_por_semana;
    cargarPlanes("plan-renovar", socio.plan_id);

    // Cada acción solo aparece cuando el estado la permite (reglas 8 y 9)
    const enUso = socio.estado === "Activo" || socio.estado === "Por vencer";
    const congelado = socio.estado === "Congelado";
    document.getElementById("acciones-congelar").hidden = !enUso;
    document.getElementById("boton-descongelar").hidden = !congelado;
    document.getElementById("acciones-renovar").hidden = congelado;
    document.getElementById("boton-cancelar").hidden = congelado || socio.estado === "Cancelado";
}

// Peso, altura, IMC (regla 4) y rutina (regla 5)
function mostrarSalud(socio) {
    document.getElementById("peso").textContent = socio.peso;
    document.getElementById("altura").textContent = socio.altura;
    // T9: el IMC manual se indica como tal y se puede volver al calculado
    let imc = socio.imc + " (" + socio.categoria_imc + ")";
    if (socio.imc_manual) {
        imc += " - manual";
    }
    document.getElementById("imc").textContent = imc;
    document.getElementById("boton-imc-calculado").hidden = !socio.imc_manual;
    // Un socio con datos antiguos puede no tener una rutina que le corresponda
    if (socio.rutina === null) {
        document.getElementById("rutina-nombre").textContent = "Sin rutina asignada";
        document.getElementById("rutina-descripcion").textContent = "";
        return;
    }
    document.getElementById("rutina-nombre").textContent = socio.rutina.nombre;
    document.getElementById("rutina-descripcion").textContent = socio.rutina.descripcion;
}

// Progreso (regla 6)
function mostrarProgreso(socio) {
    const progreso = document.getElementById("progreso");
    if (socio.progreso.resultado === "Faltan datos") {
        progreso.textContent = "Faltan datos";
        progreso.className = "";
        return;
    }

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

// Tabla con el historial de peso
function mostrarHistorial(socio) {
    const tabla = document.getElementById("tabla-pesos");
    tabla.innerHTML = "";
    for (const registro of socio.historial_peso) {
        tabla.innerHTML += `<tr><td>${escaparHtml(formatearFecha(registro.fecha))}</td><td>${escaparHtml(registro.peso)}</td></tr>`;
    }
}

// Tabla con el historial de pagos y el desglose de días (regla 7)
function mostrarPagos(socio) {
    const tabla = document.getElementById("tabla-pagos");
    tabla.innerHTML = "";
    for (const pago of socio.pagos) {
        tabla.innerHTML += `
            <tr>
                <td>${escaparHtml(formatearFecha(pago.fecha))}</td>
                <td>${escaparHtml(pago.plan)}</td>
                <td>${pago.monto}</td>
                <td>${pago.dias_plan} + ${pago.dias_restantes}</td>
                <td>${escaparHtml(formatearFecha(pago.vencimiento_nuevo))}</td>
            </tr>`;
    }
}

// Cambios de plan/vencimiento registrados por el trigger (T4).
function mostrarAuditoria(socio) {
    const tabla = document.getElementById("tabla-auditoria");
    tabla.innerHTML = "";
    if (socio.auditoria.length === 0) {
        tabla.innerHTML = '<tr><td colspan="5">Sin cambios de plan o vencimiento</td></tr>';
    }
    for (const cambio of socio.auditoria) {
        tabla.innerHTML += `
            <tr>
                <td>${escaparHtml(cambio.fecha_hora)}</td>
                <td>${escaparHtml(cambio.nombre_plan_anterior)}</td>
                <td>${escaparHtml(cambio.nombre_plan_nuevo)}</td>
                <td>${escaparHtml(formatearFecha(cambio.vencimiento_anterior))}</td>
                <td>${escaparHtml(formatearFecha(cambio.vencimiento_nuevo))}</td>
            </tr>`;
    }
}

// Rutina por día: lo que le toca, lo que hizo y sus porcentajes (reglas 11 a 14)
function mostrarSeguimiento(socio) {
    const seguimiento = socio.seguimiento;
    document.getElementById("cumplimiento").textContent = seguimiento.cumplimiento + "%";
    document.getElementById("asistencia").textContent = seguimiento.asistencia + "%";

    const sugerencia = document.getElementById("sugerencia-nivel");
    sugerencia.hidden = seguimiento.nivel_sugerido === null;
    document.getElementById("nivel-sugerido").textContent = seguimiento.nivel_sugerido;

    const dia = document.getElementById("dia-actual");
    const lista = document.getElementById("ejercicios-del-dia");
    lista.innerHTML = "";
    if (seguimiento.dia_actual === null) {
        dia.textContent = "Sin rutina asignada";
    } else {
        dia.textContent = "Le toca el Día " + seguimiento.dia_actual;
        for (const ejercicio of seguimiento.ejercicios_del_dia) {
            lista.innerHTML += `<li>${escaparHtml(ejercicio.nombre)} (${escaparHtml(ejercicio.series_repeticiones)})</li>`;
        }
    }

    const tabla = document.getElementById("tabla-entradas");
    tabla.innerHTML = "";
    if (seguimiento.entradas.length === 0) {
        tabla.innerHTML = '<tr><td colspan="3">Sin entradas en los últimos 28 días</td></tr>';
    }
    for (const entrada of seguimiento.entradas) {
        tabla.innerHTML += `
            <tr>
                <td>${escaparHtml(formatearFecha(entrada.fecha))}</td>
                <td>${escaparHtml(entrada.rutina)}, Día ${entrada.dia}</td>
                <td>${ejerciciosDeLaEntrada(entrada)}</td>
            </tr>`;
    }
}

// Casillas de una entrada: marcadas las que hizo, sin marcar las que no
function ejerciciosDeLaEntrada(entrada) {
    let html = "";
    for (const ejercicio of entrada.ejercicios) {
        let marcado = "";
        let clase = "no-hecho";
        if (ejercicio.hecho) {
            marcado = "checked";
            clase = "hecho";
        }
        html += `
            <label class="casilla ${clase}">
                <input type="checkbox" ${marcado} onchange="marcarEjercicio(${entrada.id}, ${ejercicio.id}, this.checked)">
                ${escaparHtml(ejercicio.nombre)} (${escaparHtml(ejercicio.series_repeticiones)})
            </label>`;
    }
    return html;
}

// Marcar o desmarcar un ejercicio de una entrada (regla 12)
async function marcarEjercicio(asistenciaId, ejercicioId, hecho) {
    let metodo = "DELETE";
    if (hecho) {
        metodo = "POST";
    }
    const url = "/api/socios/" + idDeLaUrl() + "/asistencias/" + asistenciaId + "/ejercicios/" + ejercicioId;
    const resultado = await llamarApi(url, metodo);
    mostrarResultado(resultado);
    cargarFicha();
}

// Confirmar la subida de nivel sugerida (regla 14)
async function subirNivel() {
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/subir-nivel", "POST");
    mostrarResultado(resultado);
    cargarFicha();
}

// Guardar los datos editados del socio
async function guardarEdicion(evento) {
    evento.preventDefault();

    const datos = {
        nombre: document.getElementById("editar-nombre").value,
        ci: document.getElementById("editar-ci").value,
        telefono: document.getElementById("editar-telefono").value,
        altura: document.getElementById("editar-altura").value,
        objetivo: document.getElementById("editar-objetivo").value,
        nivel: document.getElementById("editar-nivel").value,
    };

    const resultado = await llamarApi("/api/socios/" + idDeLaUrl(), "PUT", datos);
    mostrarResultado(resultado);
    if (resultado.ok) {
        cargarFicha();
    }
}

// Renovar el plan (regla 1)
async function renovar() {
    const datos = { plan_id: document.getElementById("plan-renovar").value };
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/renovar", "POST", datos);
    mostrarResultado(resultado);
    cargarFicha();
}

// Cancelar un socio (regla 8)
async function cancelarSocio() {
    const confirmar = confirm(
        "¿Cancelar este socio? Se conserva su historial. " +
        "Si vuelve, al renovar el plan contará desde ese día, sin los días que le quedaban."
    );
    if (!confirmar) {
        return;
    }
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/cancelar", "POST");
    mostrarResultado(resultado);
    cargarFicha();
}

// Congelar el plan (regla 9)
async function congelarPlan() {
    const datos = { dias: document.getElementById("dias-congelar").value };
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/congelar", "POST", datos);
    mostrarResultado(resultado);
    cargarFicha();
}

// Terminar el congelamiento antes de tiempo (regla 9)
async function descongelarPlan() {
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/descongelar", "POST");
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

// Guardar un IMC manual (T9, solo administrador)
async function guardarImcManual() {
    const datos = { imc: document.getElementById("imc-manual").value };
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/imc", "PUT", datos);
    mostrarResultado(resultado);
    if (resultado.ok) {
        document.getElementById("imc-manual").value = "";
        cargarFicha();
    }
}

// Volver al IMC calculado con el peso y la altura (T9)
async function volverImcCalculado() {
    const resultado = await llamarApi("/api/socios/" + idDeLaUrl() + "/imc", "DELETE");
    mostrarResultado(resultado);
    cargarFicha();
}
