from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import Creator, Work

SPECIALTIES = ("ropa", "props", "accesorios")

# Catálogo de momento. Son los perfiles del equipo; cuando tengamos los datos
# definitivos se cambian aquí y se vuelve a sembrar la base de datos.
SEED_CREATORS = [
    {
        "slug": "daniel-barrasa",
        "name": "Daniel Barrasa",
        "specialty": "ropa",
        "location": "España",
        "bio": (
            "Estudiante de 2º de SMR. Empecé cosiendo arreglos para amigos y ahora "
            "hago prendas completas de personaje. Antes de cortar la tela buena "
            "pruebo el patrón en una tela barata."
        ),
        "contact_email": "daniel.barrasa@cosknot.example",
        "accent": 0,
        "works": [
            {
                "slug": "chaqueta-de-personaje-con-forro",
                "title": "Chaqueta de personaje con forro",
                "description": (
                    "Chaqueta corta con forro interior, botones metálicos y remates "
                    "en los puños. Se hace con las medidas del cliente y una prueba "
                    "de ajuste antes de entregar."
                ),
                "price_note": "desde 90 €",
                "status": "disponible",
            },
            {
                "slug": "falda-plisada-a-medida",
                "title": "Falda plisada a medida",
                "description": (
                    "Falda con pliegues planchados uno a uno y cierre con cremallera "
                    "oculta. Se puede pedir en varios largos y colores."
                ),
                "price_note": None,
                "status": "encargo",
            },
        ],
    },
    {
        "slug": "jesus-larrazabal",
        "name": "Jesús Larrazabal",
        "specialty": "props",
        "location": "España",
        "bio": (
            "Vengo del modelismo de maquetas. Hago props ligeros en espuma y PLA, "
            "pintados a mano, para poder llevarlos todo el día en una convención "
            "sin que molesten."
        ),
        "contact_email": "jesus.larrazabal@cosknot.example",
        "accent": 1,
        "works": [
            {
                "slug": "espada-de-espuma-con-alma-de-fibra",
                "title": "Espada de espuma con alma de fibra",
                "description": (
                    "Hoja de espuma dura con alma de fibra de vidrio y punta "
                    "redondeada. Pesa menos de 900 g y la empuñadura va forrada en "
                    "cuero sintético."
                ),
                "price_note": "desde 70 €",
                "status": "disponible",
            },
            {
                "slug": "casco-impreso-en-3d",
                "title": "Casco impreso en 3D",
                "description": (
                    "Casco impreso en PLA, lijado en seco, imprimación y pintura en "
                    "capas finas. Lleva espuma dentro para que no baile en la cabeza."
                ),
                "price_note": "desde 120 €",
                "status": "disponible",
            },
        ],
    },
    {
        "slug": "daniel-torres",
        "name": "Daniel Torres",
        "specialty": "accesorios",
        "location": "España",
        "bio": (
            "Me gustan los detalles pequeños: hebillas, correas y piezas de resina. "
            "Todo va cosido o pegado a mano y lo pruebo antes de entregarlo, porque "
            "un accesorio mal rematado se nota a la hora de la verdad."
        ),
        "contact_email": "daniel.torres@cosknot.example",
        "accent": 2,
        "works": [
            {
                "slug": "arnes-de-cuero-sintetico",
                "title": "Arnés de cuero sintético",
                "description": (
                    "Arnés ajustable con remaches de latón y cuatro puntos de "
                    "regulación. Forro suave en los puntos donde roza."
                ),
                "price_note": "desde 60 €",
                "status": "disponible",
            },
            {
                "slug": "corona-de-resina",
                "title": "Corona de resina",
                "description": (
                    "Corona ligera de resina teñida, con cierre elástico regulable "
                    "y acabado mate para que no refleje los focos del salón."
                ),
                "price_note": "desde 40 €",
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
