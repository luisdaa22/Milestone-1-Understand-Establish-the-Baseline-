from pathlib import Path

from sqlalchemy import func, select

from store import create_app
from store.db import get_session
from store.models import Product

PRODUCTS = [
    ("PLANT-100", "Monstera Deliciosa", "The classic split-leaf statement plant. Bright indirect light, water when the top 5 cm of soil is dry. 25 cm nursery pot.", 54900, 8, "/static/images/monstera.svg"),
    ("PLANT-110", "Snake Plant", "Nearly indestructible Sansevieria. Tolerates low light and missed waterings — ideal for a first plant.", 32900, 14, "/static/images/snake-plant.svg"),
    ("PLANT-120", "Golden Pothos", "Fast-growing trailing vine with marbled yellow-green leaves. Great on shelves or in hanging baskets.", 22900, 20, "/static/images/pothos.svg"),
    ("PLANT-130", "Succulent Trio", "Three small Echeveria and Graptopetalum in ceramic pots. Full sun, water every two weeks.", 27900, 16, "/static/images/succulents.svg"),
    ("PLANT-140", "Terracotta Pot Set", "Three breathable clay pots (10, 15 and 20 cm) with drainage holes and saucers.", 34900, 12, "/static/images/terracotta-pots.svg"),
    ("PLANT-150", "Brass Watering Can", "1.5 L brass-finish watering can with a long, narrow spout for precise watering.", 41900, 10, "/static/images/watering-can.svg"),
]


def seed() -> None:
    app = create_app()
    with app.app_context():
        db = get_session()
        count = db.scalar(select(func.count()).select_from(Product))
        if count:
            print(f"Database already contains {count} products; nothing changed.")
            return
        for sku, name, description, price, stock, image_url in PRODUCTS:
            db.add(Product(
                sku=sku,
                name=name,
                description=description,
                price_cents=price,
                stock_quantity=stock,
                image_url=image_url,
                active=1,
            ))
        db.commit()
        print(f"Seeded {len(PRODUCTS)} products.")


if __name__ == "__main__":
    seed()
