# guía css de cosknot

## variables de color

usar variables css para que la identidad visual pueda cambiar sin reescribir cada componente

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

el valor terracota es #d97757, aprobado en la nota de planificación del proyecto

## qué hace cada concepto css en cosknot

- el modelo de caja controla el padding los bordes y el espaciado de las tarjetas
- flexbox maneja barras de navegación botones filas de filtros y acciones del vendedor
- grid maneja galerías de productos del marketplace y layouts de categorías
- las variables mantienen consistente la identidad de blanco negro y terracota
- las media queries hacen que las tarjetas de producto y la navegación funcionen en teléfonos
- los estados hover focus y active hacen que los controles sean comprensibles
- `object-fit: cover` mantiene alineadas las imágenes de producto en las tarjetas
- la tipografía controla la jerarquía entre nombres de producto precios metadatos y descripciones
- `position: sticky` puede mantener visibles los filtros o un panel de compra cuando sea útil
- las transiciones deben ser sutiles y apoyar el contenido no distraer de él

## primeras pantallas visuales

1. landing page
2. grid de descubrimiento de productos
3. página de detalle de producto
4. perfil de vendedor
5. formulario simple para publicar un listado

## límite del primer mvp

no empezar con pagos chat recomendaciones reseñas moderación ni una red social completa

primero demostrar que un visitante puede descubrir un artículo de cosplay abrir su página de detalle y entender quién lo vende
