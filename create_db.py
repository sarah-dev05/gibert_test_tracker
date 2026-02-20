# create_db.py
from app import app, db, Projet, Module, Test
import os

db_path = "database.db"

# Supprime l'ancienne base si elle existe
if os.path.exists(db_path):
    os.remove(db_path)
    print("Ancienne base supprimée.")

with app.app_context():
    db.create_all()
    print("Tables créées avec succès !")

    inspector = db.inspect(db.engine)
    for table_name in ['projet', 'module', 'test']:
        cols = [c['name'] for c in inspector.get_columns(table_name)]
        print(f"Colonnes de {table_name} :", cols)