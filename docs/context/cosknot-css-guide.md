# guía de CSS de cosknot

## colores

Uso variables de CSS para poder cambiar la identidad visual sin tocar cada componente.
Todas están en `:root`, al principio de `static/css/styles.css`.

```css
:root {
  --color-white: #fff;
  --color-black: #222;
  --color-accent: #fa8072;
  --color-accent-dark: #b8443a;
  --color-accent-deep: #8a2f24;
  --color-accent-soft: #fde3de;
  --color-surface: #f5f5f5;
  --color-surface-deep: #ebebeb;
  --color-border: #e1e1e1;
  --color-border-strong: #c7c7c7;
  --color-ink-soft: #595959;
  --color-muted: #757575;
}
```

El peso lo llevan el negro y el blanco. El salmón terracota `#fa8072` es el terciario y
solo se usa para acentos: botones, etiquetas, la marca y las miniaturas con degradado.
Para texto sobre blanco uso la variante oscura `--color-accent-dark` (`#b8443a`) o
`--color-accent-deep` (`#8a2f24`), porque el salmón puro no tiene contraste suficiente.

## tipografía

No hay tipografía serif. Todo el sitio va en la sans del sistema, cuerpo y titulares,
con `--font-ui`: `system-ui`, `Segoe UI`, Roboto, Helvetica, Arial. Los titulares van en
peso 600 con un `letter-spacing` negativo pequeño, y el cuerpo en `0.9375rem` con
`line-height` 1.5. La jerarquía la marcan el tamaño y el color, no el tipo de letra: los
metadatos en `--color-muted` y los nombres en negro.

## piezas del sistema visual

El diseño copia el esqueleto de los marketplaces grandes. Cada pieza es una clase de
`styles.css`, y el ancho de página lo fija `.wrap` con `--wrap` a 1280px.

- **cabecera fija.** `.site-header` va con `position: sticky` arriba del todo y
  `z-index: 40`. Dentro, `.topbar` coloca el logo, el buscador central y `.topnav` con
  los enlaces de cuenta. El buscador es `.search`: un `input type="search"` que envía a
  `/buscar`.
- **barra de categorías.** `.catnav` es una fila con scroll horizontal justo debajo de
  la cabecera: todo, ropa, props, pelucas, accesorios, encargos y quiénes somos.
- **rejilla de producto.** `.product-grid` es un grid `auto-fill` con columnas de 210px
  mínimo. Cada `.product-card` es una tarjeta cuadrada: `.product-img` con
  `aspect-ratio: 1 / 1` y el degradado de acento, y debajo título, creador y precio.
- **listado con filtros.** `.listing` es un grid de dos columnas, 240px de `.sidebar` y
  el resto para el contenido. `.sidebar` es sticky y lleva los `.chip` de especialidad.
  Encima, `.toolbar` pone el contador a la izquierda y el criterio de orden a la
  derecha, con un borde inferior que lo separa de la rejilla.
- **ficha de obra.** `.work-detail` es un grid de dos columnas (1.15fr y 1fr): la imagen
  cuadrada y sticky a la izquierda, y a la derecha el título, el creador, el precio, la
  descripción y los botones de contacto.
- **pie de cuatro columnas.** `.footer-cols` reparte comprar, vender, cosknot y la marca
  con `auto-fit`. Debajo, `.footer-bottom` cierra con el copyright y los enlaces
  legales.

## qué hace cada cosa

- El modelo de caja controla el relleno, los bordes y el espacio de las tarjetas.
- Flexbox resuelve la navegación, los botones y la fila de filtros.
- Grid coloca la rejilla de creadores y de obras.
- Las variables mantienen el blanco, el negro y el salmón iguales en todo el sitio.
- Las media queries adaptan la rejilla y la navegación al móvil.
- Los estados `hover`, `focus` y `active` hacen que los controles se entiendan.
- `object-fit: cover` sirve para las imágenes que añadamos más adelante.
- La tipografía marca la diferencia entre nombre, precio, metadatos y descripción.
- `position: sticky` puede servir para dejar los filtros a la vista.
- Las transiciones tienen que ser suaves y no distraer.

## pantallas que hay que cubrir

1. Portada.
2. Listado de creadores.
3. Ficha de obra.
4. Perfil del creador.
5. Un formulario simple para publicar una obra.

## límite de la primera versión

Nada de pagos, chat, recomendaciones, reseñas ni moderación. Primero hay que demostrar
que una persona puede entrar, encontrar una pieza, abrir su ficha y saber quién la hace.
