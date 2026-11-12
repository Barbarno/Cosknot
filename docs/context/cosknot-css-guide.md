# guía de CSS de cosknot

## colores

Uso variables de CSS para poder cambiar la identidad visual sin tocar cada componente.

```css
:root {
  --color-white: #fff;
  --color-black: #111;
  --color-accent: #fa8072;
  --color-surface: #f6f6f6;
  --color-muted: #6b6b6b;
  --color-border: #e0e0e0;
}
```

Los colores primarios son el negro y el blanco. El salmón terracota `#fa8072` es el
terciario y solo se usa para acentos: botones, enlaces, etiquetas y las miniaturas con
degradado. Para texto sobre blanco se usa la variante oscura `--color-accent-dark`
(`#b8443a`), porque el salmón puro no tiene contraste suficiente.

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
