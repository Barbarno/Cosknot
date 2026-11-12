# guía de CSS de cosknot

## colores

Uso variables de CSS para poder cambiar la identidad visual sin tocar cada componente.

```css
:root {
  --color-white: #fff;
  --color-black: #111;
  --color-terracotta: #d97757;
  --color-surface: #f7f3f1;
  --color-muted: #6f6764;
  --color-border: #ded6d2;
}
```

El terracota es `#d97757` y está aprobado en la nota de planificación del proyecto.

## qué hace cada cosa

- El modelo de caja controla el relleno, los bordes y el espacio de las tarjetas.
- Flexbox resuelve la navegación, los botones y la fila de filtros.
- Grid coloca la rejilla de creadores y de obras.
- Las variables mantienen el blanco, el negro y el terracota iguales en todo el sitio.
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
