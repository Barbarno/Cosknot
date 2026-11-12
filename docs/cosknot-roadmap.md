# roadmap

## la idea

cosknot conecta a creadores de cosplay con gente que busca ropa, props, accesorios y
trabajo hecho a mano de juegos, series, anime y mundos parecidos.

La decisión importante de producto sigue abierta: si la primera versión es un
directorio de creadores, un feed de comunidad o una tienda. Lo que está claro es que
no se hacen las tres cosas a la vez.

## reparto del trabajo

### en general

- dejar claro qué problema resuelve la web y para quién
- mirar comunidades parecidas
- elegir el competidor más conocido
- preparar un SWOT corto y una idea del mercado

### Daniel B.

- llevar el repositorio de GitHub
- mantener el README
- organizar el tablero
- pensar el posicionamiento y las primeras pruebas de crecimiento

### Jesús

- elegir el stack
- definir el modelo de datos y la arquitectura
- pruebas y despliegue
- valorar si la IA aporta algo de verdad o es adorno

### Daniel T.

- ver de dónde pueden salir ingresos
- calcular costes iniciales y de mantenimiento
- separar gastos puntuales de gastos fijos
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

- PostgreSQL en vez de SQLite
- un servicio de almacenamiento para las imágenes
- AWS solo cuando haga falta de verdad
- IA solo si hay un caso claro, como etiquetar o ayudar a los creadores

## por qué este stack

Es sencillo de entender de principio a fin, no esconde lo básico detrás de un framework
de frontend y se puede ampliar sin tirar el prototipo.

## decisiones pendientes

- el primer usuario y el primer problema exactos
- si la primera versión es un directorio, un feed o una tienda
- color terracota final
- tipografía
- modelo de ingresos
- ~~proveedor de despliegue y dominio~~ (decidido en `decisions/0001-stack-despliegue-dominio.md`)
- normas de privacidad, moderación y propiedad del contenido
- si la IA entra en la primera versión
