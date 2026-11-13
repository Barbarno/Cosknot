(() => {
  const bloque = document.querySelector("[data-sugerencias]");
  if (!bloque) return;

  const url = bloque.dataset.url;
  const entrada = bloque.querySelector("#sugerencia-foto");
  const boton = bloque.querySelector("[data-sugerir]");
  const estado = bloque.querySelector("[data-sugerir-estado]");
  const etiquetas = bloque.querySelector("[data-sugerir-etiquetas]");
  const lista = bloque.querySelector("[data-sugerir-lista]");
  const anadir = bloque.querySelector("[data-sugerir-anadir]");
  const titulo = document.querySelector("#titulo");
  const descripcion = document.querySelector("#descripcion");
  const csrf = document.querySelector('input[name="csrf_token"]');

  if (!url || !entrada || !boton || !estado) return;

  let propuestas = [];

  const decir = (texto) => {
    estado.textContent = texto;
  };

  boton.addEventListener("click", async () => {
    const archivo = entrada.files && entrada.files[0];
    if (!archivo) {
      decir("elige antes una foto.");
      return;
    }

    const datos = new FormData();
    datos.append("foto", archivo);
    if (csrf) datos.append("csrf_token", csrf.value);
    if (titulo && titulo.value.trim()) datos.append("pista", titulo.value.trim());

    boton.disabled = true;
    decir("mirando la foto...");

    try {
      const respuesta = await fetch(url, {
        method: "POST",
        body: datos,
        headers: { "X-Requested-With": "fetch" },
        credentials: "same-origin",
      });
      const cuerpo = await respuesta.json().catch(() => ({}));

      if (!respuesta.ok) {
        decir(cuerpo.error || "no se pudo pedir la sugerencia.");
        return;
      }

      const sugerencia = cuerpo.sugerencia || {};
      if (titulo && sugerencia.titulo) titulo.value = sugerencia.titulo;
      if (descripcion && sugerencia.descripcion) descripcion.value = sugerencia.descripcion;

      propuestas = Array.isArray(sugerencia.etiquetas) ? sugerencia.etiquetas : [];
      if (lista && etiquetas) {
        lista.textContent = propuestas.join(", ");
        etiquetas.hidden = propuestas.length === 0;
      }
      decir("propuesta aplicada: revísala y cámbiala si hace falta.");
    } catch (error) {
      decir("la petición falló: " + (error && error.message ? error.message : "sin red"));
    } finally {
      boton.disabled = false;
    }
  });

  if (anadir) {
    anadir.addEventListener("click", () => {
      if (!descripcion || propuestas.length === 0) return;
      const linea = "etiquetas: " + propuestas.join(", ");
      const actual = descripcion.value.trimEnd();
      descripcion.value = actual ? actual + "\n\n" + linea : linea;
      decir("etiquetas añadidas a la descripción.");
    });
  }
})();
