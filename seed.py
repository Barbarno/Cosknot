from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Creator, Work

SPECIALTIES = ("ropa", "props", "pelucas", "accesorios")

# Catálogo de ejemplo: perfiles de creadores verificados que venden en la web.
# Los datos son inventados; cuando haya creadores reales se sustituyen aquí.
SEED_CREATORS = [
    {
        "slug": "marisol-vega",
        "name": "Marisol Vega",
        "specialty": "ropa",
        "location": "Valencia, España",
        "bio": (
            "Costurera de formación y cosplayer desde 2014. Trabajo sobre todo con "
            "tejidos técnicos y patrones propios para personajes de anime y fantasía. "
            "Cada encargo empieza con una prueba de patrón en tela barata antes de "
            "tocar el material bueno."
        ),
        "contact_email": "marisol@cosknot.example",
        "accent": 0,
        "verified": True,
        "works": [
            {
                "slug": "abrigo-de-invierno-fantasia",
                "title": "Abrigo de invierno de fantasía",
                "description": (
                    "Abrigo largo con capucha forrada, broches metálicos y bordado "
                    "en los puños. Patrón ajustado al cuerpo y apertura lateral para "
                    "poder caminar durante el evento."
                ),
                "price_note": "desde 180 €",
                "status": "disponible",
            },
            {
                "slug": "vestido-de-gala-anime",
                "title": "Vestido de gala de personaje de anime",
                "description": (
                    "Vestido de dos piezas con corsé interno, falda con vuelo y "
                    "aplicaciones de encaje. Se entrega con instrucciones de lavado "
                    "y una bolsa de tela para el transporte."
                ),
                "price_note": "desde 240 €",
                "status": "encargo",
            },
        ],
    },
    {
        "slug": "tomas-iriarte",
        "name": "Tomás Iriarte",
        "specialty": "props",
        "location": "Bilbao, España",
        "bio": (
            "Vengo del modelismo de maquetas. Hago armas de fantasía y ciencia "
            "ficción en espuma, resina y PLA, con acabados pintados a mano. Todo lo "
            "que sale del taller es ligero y seguro para llevar en evento."
        ),
        "contact_email": "tomas@cosknot.example",
        "accent": 1,
        "verified": True,
        "works": [
            {
                "slug": "espada-de-caballero-de-fantasia",
                "title": "Espada de caballero de fantasía",
                "description": (
                    "Hoja de espuma dura con alma de fibra de vidrio, guarda en resina "
                    "y empuñadura forrada en cuero sintético. Peso inferior a 900 g y "
                    "punta redondeada."
                ),
                "price_note": "desde 130 €",
                "status": "disponible",
            },
            {
                "slug": "pistola-de-ciencia-ficcion",
                "title": "Pistola de ciencia ficción",
                "description": (
                    "Prop pintado con aerógrafo, luces led alimentadas por una pila "
                    "de botón y acabado desgastado. Incluye soporte de pared."
                ),
                "price_note": "desde 85 €",
                "status": "agotado",
            },
        ],
    },
    {
        "slug": "lucia-ferrer",
        "name": "Lucía Ferrer",
        "specialty": "pelucas",
        "location": "Ciudad de México, México",
        "bio": (
            "Hago pelucas, tocados y extensiones de personaje. Me interesa que las "
            "piezas aguanten un día entero de convención sin pinchar ni pesar. "
            "Trabajo con encargo cerrado y envío a todo el país."
        ),
        "contact_email": "lucia@cosknot.example",
        "accent": 2,
        "verified": True,
        "works": [
            {
                "slug": "peluca-estilizada-personaje",
                "title": "Peluca estilizada de personaje",
                "description": (
                    "Peluca de fibra térmica cortada, cardada y fijada con laca de "
                    "fijación fuerte. Se entrega en su soporte de cabeza para que "
                    "llegue sin deformarse."
                ),
                "price_note": "desde 110 €",
                "status": "disponible",
            },
            {
                "slug": "extensiones-de-color-a-medida",
                "title": "Extensiones de color a medida",
                "description": (
                    "Juego de extensiones de fibra térmica teñidas en el color que "
                    "pidas, con pinzas cosidas a mano. Se pueden lavar con cuidado y "
                    "volver a peinar."
                ),
                "price_note": "desde 35 €",
                "status": "encargo",
            },
        ],
    },
    {
        "slug": "iker-zabaleta",
        "name": "Iker Zabaleta",
        "specialty": "props",
        "location": "San Sebastián, España",
        "bio": (
            "Taller pequeño especializado en armaduras ligeras y cascos. Imprimo en "
            "3D, lijado en seco y pintura en capas finas. No hago piezas metálicas "
            "reales: todo es material blando para uso escénico."
        ),
        "contact_email": "iker@cosknot.example",
        "accent": 3,
        "verified": True,
        "works": [
            {
                "slug": "casco-de-soldado-espacial",
                "title": "Casco de soldado espacial",
                "description": (
                    "Casco impreso en PLA, imprimación y pintura envejecida. Visor "
                    "de plástico ahumado y ventilación interior con espuma."
                ),
                "price_note": "desde 150 €",
                "status": "disponible",
            },
            {
                "slug": "hombreras-de-cuero-sintetico",
                "title": "Hombreras de cuero sintético",
                "description": (
                    "Par de hombreras con remaches decorativos y forro interior. "
                    "Se ajustan con correas cruzadas en la espalda."
                ),
                "price_note": "desde 70 €",
                "status": "disponible",
            },
        ],
    },
    {
        "slug": "valentina-ortiz",
        "name": "Valentina Ortiz",
        "specialty": "ropa",
        "location": "Bogotá, Colombia",
        "bio": (
            "Diseñadora textil. Me especializo en capas, abrigos y prendas de varias "
            "piezas para personajes de videojuegos. Trabajo con algodón, lino y "
            "mezclas que aguantan el calor de las convenciones."
        ),
        "contact_email": "valentina@cosknot.example",
        "accent": 4,
        "verified": True,
        "works": [
            {
                "slug": "capa-con-capucha-bordada",
                "title": "Capa con capucha bordada",
                "description": (
                    "Capa de lino con capucha y bordado floral en el borde inferior. "
                    "Cierre con broche de metal y forro parcial en los hombros."
                ),
                "price_note": "desde 140 €",
                "status": "disponible",
            },
            {
                "slug": "armadura-textil-acolchada",
                "title": "Armadura textil acolchada",
                "description": (
                    "Chaqueta acolchada con pespuntes en rombo, pensada para llevar "
                    "debajo de piezas de espuma. Transpirable y lavable a mano."
                ),
                "price_note": "desde 120 €",
                "status": "encargo",
            },
        ],
    },
    {
        "slug": "diego-salazar",
        "name": "Diego Salazar",
        "specialty": "accesorios",
        "location": "Lima, Perú",
        "bio": (
            "Trabajo cuero vegetal y sintético: cinturones, fundas, brazales y "
            "arneses. Todo cosido a mano con hilo encerado. Hago muestras de color "
            "antes de cortar la pieza final."
        ),
        "contact_email": "diego@cosknot.example",
        "accent": 5,
        "verified": True,
        "works": [
            {
                "slug": "arnes-de-cuero-con-remaches",
                "title": "Arnés de cuero con remaches",
                "description": (
                    "Arnés ajustable de cuero vegetal curtido a mano, con remaches "
                    "de latón y cuatro puntos de regulación. Forro suave en los "
                    "puntos de roce."
                ),
                "price_note": "desde 160 €",
                "status": "disponible",
            },
            {
                "slug": "funda-de-daga-de-fantasia",
                "title": "Funda de daga de fantasía",
                "description": (
                    "Funda de cuero cosida a mano con broche y anilla para colgar "
                    "del cinturón. Ajustada a una daga de espuma de 45 cm."
                ),
                "price_note": "desde 65 €",
                "status": "disponible",
            },
            {
                "slug": "guantes-de-armadura-fantasia",
                "title": "Guantes de armadura de fantasía",
                "description": (
                    "Guantes de goma espuma forrada con dedos articulados y correas "
                    "de velcro. Se pueden llevar encima de un guante normal."
                ),
                "price_note": None,
                "status": "encargo",
            },
        ],
    },
    {
        "slug": "sofia-bianchi",
        "name": "Sofía Bianchi",
        "specialty": "accesorios",
        "location": "Rosario, Argentina",
        "bio": (
            "Ilustradora y propmaker. Convierto diseños en piezas físicas: cascos, "
            "garras, alas pequeñas y objetos de escena. Me interesa el detalle "
            "pintado más que el tamaño."
        ),
        "contact_email": "sofia@cosknot.example",
        "accent": 6,
        "verified": True,
        "works": [
            {
                "slug": "garras-de-criatura",
                "title": "Garras de criatura",
                "description": (
                    "Juego de cinco garras de resina teñida con base de guante "
                    "elástico. Se ajustan a mano izquierda o derecha."
                ),
                "price_note": "desde 40 €",
                "status": "disponible",
            },
            {
                "slug": "mascara-de-criatura-del-bosque",
                "title": "Máscara de criatura del bosque",
                "description": (
                    "Máscara de resina pintada a mano con hojas secas tratadas y "
                    "acabado mate. Acolchado interior y correa ajustable."
                ),
                "price_note": "desde 75 €",
                "status": "disponible",
            },
        ],
    },
]


def seed_database(session: Session) -> bool:
    """Mete el catálogo de ejemplo, pero solo si la tabla de creadores está vacía."""
    existing = session.scalar(select(func.count()).select_from(Creator))
    if existing:
        return False

    for entry in SEED_CREATORS:
        works = entry["works"]
        creator = Creator(
            slug=entry["slug"],
            name=entry["name"],
            specialty=entry["specialty"],
            location=entry["location"],
            bio=entry["bio"],
            contact_email=entry["contact_email"],
            accent=entry["accent"],
            verified=entry["verified"],
        )
        creator.works = [
            Work(
                slug=work["slug"],
                title=work["title"],
                description=work["description"],
                price_note=work["price_note"],
                status=work["status"],
            )
            for work in works
        ]
        session.add(creator)

    session.commit()
    return True
