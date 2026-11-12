# roadmap

## la idea

cosknot es un marketplace de cosplay. Los creadores publican ropa, props, pelucas y
accesorios de juegos, series, anime y mundos parecidos, y la gente les compra piezas o
les pide un encargo. Nosotros somos el intermediario entre las dos partes.

La decisión de producto ya está tomada: es un marketplace, no un directorio ni un feed.
Lo que queda por construir es la parte que convierte la web en marketplace de verdad:
que el creador publique su pieza, que el comprador pida encargo, y que el dinero pase
por aquí con una comisión nuestra.

## el orden que seguimos

1. Que el catálogo se pueda mantener sin tocar la base de datos a mano.
2. Que un comprador pueda pedir un encargo desde la ficha de la obra.
3. Que el pago se haga dentro de la web.
4. Que quede claro cuánto cobramos por venta.

Los cuatro pasos van en ese orden porque cada uno necesita el anterior. Sin cuentas de
usuario no hay forma de saber quién publica ni quién compra. Sin encargos no hay nada
que cobrar. Sin cobro no hay comisión.

## reparto del trabajo

### en general

- dejar claro qué problema resuelve la web y para quién (hecho: marketplace de cosplay)
- mirar comunidades parecidas y competidores de marketplace
- preparar un SWOT corto y una idea del mercado
- escribir las normas de qué se puede publicar y qué no

### Daniel Barrasa (CEO y CMO)

- llevar el repositorio de GitHub
- mantener el README
- organizar el tablero
- pensar el posicionamiento y las primeras pruebas de crecimiento
- buscar los primeros creadores reales que publiquen piezas

### Jesús Larrazabal (CTO)

- elegir el stack
- definir el modelo de datos y la arquitectura
- pruebas y despliegue
- llevar las cuentas de usuario, los encargos y el pago dentro de la web
- valorar si la IA aporta algo de verdad o es adorno

### Daniel Torres (CFO)

- ver de dónde pueden salir ingresos
- calcular costes iniciales y de mantenimiento
- separar gastos puntuales de gastos fijos
- fijar la comisión por venta y el coste de la pasarela de pago
- apuntar los supuestos en vez de presentarlos como hechos

### diseño

- decidir el nombre y el logo
- proponer eslóganes
- aprobar los colores exactos
- elegir tipografía y jerarquía visual
- que el diseño se note pero no estorbe para encontrar cosas

## stack

### para la primera versión

- Python, porque es lo que estamos aprendiendo
- Flask, un servidor pequeño y fácil de seguir
- Jinja para generar el HTML en el servidor
- HTML y CSS para la interfaz
- JavaScript normalito para el filtro
- SQLite para el prototipo local
- pytest para las pruebas
- Git y GitHub para el control de versiones

### más adelante, si la web se usa

- un servicio de almacenamiento para las imágenes de las piezas
- una pasarela de pago para cobrar dentro de la web
- AWS solo cuando haga falta de verdad
- IA solo si hay un caso claro, como etiquetar o ayudar a los creadores

## por qué este stack

Es sencillo de entender de principio a fin, no esconde lo básico detrás de un framework
de frontend y se puede ampliar sin tirar el prototipo.

## decisiones pendientes

- porcentaje exacto de comisión y quién paga la pasarela
- qué pasarela de pago usamos
- color terracota final
- tipografía
- normas de privacidad, moderación y propiedad del contenido
- si la IA entra en el producto
- ~~el primer usuario y el primer problema~~ (decidido: marketplace de cosplay)
- ~~si la primera versión es un directorio, un feed o una tienda~~ (decidido: marketplace)
- ~~proveedor de despliegue y dominio~~ (decidido en `decisions/0001-stack-despliegue-dominio.md`)
