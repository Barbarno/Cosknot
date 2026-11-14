# diseño

## nombre

**cosknot.** De *cos* (cosplay) y *knot* (nudo).

Un nudo es lo que se hace al terminar una costura y también lo que ata a un creador con
su comprador. Dos sílabas, se lee igual en español y en inglés, sin guion, sin número y
sin tilde. Un nombre que hay que explicar es un nombre malo; este se entiende al verlo
escrito.

## eslogan

**«cosplay, pieza a pieza».**

Dice las dos cosas: qué se vende (cosplay) y cómo se hace (a mano, por partes). Para
cartelería corta: «tu personaje, pieza a pieza».

## logo

Dos ficheros SVG escritos a mano, menos de 2 KB entre los dos, que escalan sin perderse:

| fichero | para qué |
|---|---|
| [`static/img/logo.svg`](../static/img/logo.svg) | marca + palabra «Cosknot», para cabecera, pie y correo |
| [`static/img/logo-mark.svg`](../static/img/logo-mark.svg) | solo la marca en cuadrado, para favicon, avatar y redes |

**Qué es:** una **C** negra sobre un cuadrado salmón, atravesada por una **aguja** con su
**hilo** en crema; el hilo sale suelto hacia la derecha hasta enlazar con las letras.

```
C   = cosknot
aguja = el oficio
hilo  = la unión entre creador y comprador
```

## tipografía

Dos, y ninguna se descarga:

| uso | tipografía | por qué |
|---|---|---|
| logotipo | Arial Black, peso 900, interletra −3,4 | letra gruesa que aguanta tamaño pequeño |
| texto e interfaz | Segoe UI con reserva en system-ui y Arial | la del sistema: cero descargas, cero parpadeo |

## colores

Tres papeles: dos mates y un acento llamativo. El fondo no compite y el salmón sí.

| papel | color | hex | dónde |
|---|---|---|---|
| primario (mate) | crema cálido | `#f7f1e8` | fondos amplios, cabecera |
| primario (mate) | gris superficie | `#f5f5f5` | tarjetas y secciones |
| secundario (mate) | grafito | `#222222` | texto, bordes, logotipo |
| secundario (mate) | gris tinta | `#595959` | texto secundario |
| **acento (llamativo)** | **salmón** | `#fa8072` | botones, precios, marca |
| acento profundo | salmón quemado | `#b8443a` | enlaces y hover |
| acento suave | salmón claro | `#fde3de` | etiquetas y avisos |

Degradado de acento para cabeceras y botones destacados:

```css
background: linear-gradient(135deg, #fa8072 0%, #b8443a 100%);
```

## el criterio, en una frase

**Todo lo que el usuario tiene que pulsar es salmón; todo lo demás es crema, gris o
grafito.** Nunca hay dos acentos en la misma pantalla.

## la marca aplicada

| pieza | uso del color | uso de la tipografía |
|---|---|---|
| cabecera | crema de fondo, logo a la izquierda | logotipo en Arial Black |
| tarjeta de pieza | blanco sobre gris superficie | título en Segoe UI 600, precio en salmón |
| botón principal | salmón con texto blanco | Segoe UI 600 |
| etiqueta «premium» | salmón con texto blanco | Segoe UI 600, 12 px |
| avisos | salmón claro de fondo, salmón quemado de texto | Segoe UI 400 |
