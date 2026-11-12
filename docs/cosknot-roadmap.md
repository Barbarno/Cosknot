# roadmap del proyecto cosknot

## idea de producto

cosknot conecta a creadores de cosplay creadores y fans alrededor de ropa accesorios props y otro trabajo hecho a mano relacionado con juegos series anime y mundos de ficción similares

la primera decisión de producto sigue abierta
el equipo debe decidir si la primera versión se enfoca en descubrimiento de creadores portafolios interacción de comunidad o venta directa

no construir todo eso a la vez

## responsabilidades del equipo

### general

- aclarar la idea y el usuario objetivo
- investigar comunidades comparables
- identificar el competidor más reconocible
- preparar un swot corto y una visión de mercado

### ceo y cmo

- crear el repositorio de github
- mantener el readme
- coordinar el tablero del proyecto
- definir el posicionamiento y los primeros experimentos de crecimiento

### cto

- elegir el stack
- definir el modelo de datos y la arquitectura
- definir pruebas y despliegue
- evaluar funciones de ia sin añadir ia solo de adorno

### cfo

- identificar posibles fuentes de ingresos
- estimar costos iniciales y de mantenimiento
- separar costos puntuales de costos recurrentes
- registrar supuestos en lugar de presentar conjeturas como hechos

### diseño

- decidir el tratamiento del nombre y la dirección del logo
- definir opciones de eslogan
- aprobar los valores exactos de los colores
- definir tipografía y jerarquía visual
- mantener el diseño expresivo sin dificultar el descubrimiento

## stack recomendado para la primera versión

### primera versión

- python para el backend porque encaja con la ruta de aprendizaje actual del equipo
- flask para un servidor web pequeño y comprensible
- jinja para html renderizado en servidor
- html y css para la interfaz
- javascript vanilla para interacciones pequeñas
- sqlite para el primer prototipo local
- pytest para pruebas automatizadas
- git y github para control de versiones y colaboración

### más adelante cuando el producto tenga uso real

- postgresql en lugar de sqlite para datos de producción
- un servicio adecuado de almacenamiento de objetos para las imágenes
- aws solo después de conocer los requisitos de despliegue
- un servicio de ia solo para un caso de uso validado como etiquetado descubrimiento o soporte a creadores

## por qué este stack

es lo bastante simple para que un principiante lo entienda de punta a punta
evita esconder los fundamentos detrás de un framework de frontend
puede crecer hasta ser un producto real sin tirar el primer prototipo

## decisiones que todavía faltan

- el primer usuario y el primer problema exactos
- si la primera versión es un directorio de portafolios un feed de comunidad o un flujo de venta
- color terracota final
- tipografía
- modelo de ingresos inicial
- ~~proveedor de despliegue y dominio~~ → decidido en `docs/decisions/0001-stack-despliegue-dominio.md`
- reglas de privacidad moderación y propiedad del contenido
- si la ia entra en la versión uno
