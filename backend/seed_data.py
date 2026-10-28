import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def seed_services():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    services = [
        {
            'id': 'serv-1',
            'name': 'Secours Populaire - Distribution Alimentaire',
            'category': 'food',
            'description': 'Distribution gratuite de nourriture. Ouvert à tous sans condition.',
            'address': '9-11 Rue Froissart, 75003 Paris',
            'phone': '+33 1 44 78 21 00',
            'hours': 'Lun-Ven: 9h-17h',
            'location': {'lat': 48.8604, 'lng': 2.3656}
        },
        {
            'id': 'serv-2',
            'name': 'La Cimade - Aide Juridique',
            'category': 'legal',
            'description': 'Permanence juridique gratuite pour les étrangers. Conseil et accompagnement.',
            'address': '176 Rue de Grenelle, 75007 Paris',
            'phone': '+33 1 40 08 05 34',
            'hours': 'Mar-Jeu: 14h-18h',
            'location': {'lat': 48.8566, 'lng': 2.3120}
        },
        {
            'id': 'serv-3',
            'name': 'PASS - Permanence Santé',
            'category': 'health',
            'description': 'Soins médicaux gratuits sans conditions. Consultations générales.',
            'address': 'Hôpital Saint-Antoine, 184 Rue du Faubourg Saint-Antoine, 75012',
            'phone': '+33 1 49 28 20 00',
            'hours': 'Lun-Ven: 9h-16h',
            'location': {'lat': 48.8496, 'lng': 2.3936}
        },
        {
            'id': 'serv-4',
            'name': 'Emmaüs Solidarité - Hébergement',
            'category': 'housing',
            'description': "Centre d'hébergement d'urgence. Accueil de jour et hébergement.",
            'address': '15 Rue du Château Landon, 75010 Paris',
            'phone': '+33 1 42 03 38 38',
            'hours': '24h/24',
            'location': {'lat': 48.8780, 'lng': 2.3619}
        },
        {
            'id': 'serv-5',
            'name': 'Pôle Emploi Paris 11',
            'category': 'work',
            'description': 'Aide à la recherche d\'emploi, formation, inscription chômage.',
            'address': '55 Boulevard de la Villette, 75010 Paris',
            'phone': '+33 3 949',
            'hours': 'Lun-Ven: 8h30-16h30',
            'location': {'lat': 48.8739, 'lng': 2.3669}
        },
        {
            'id': 'serv-6',
            'name': 'Cours de Français - Solidarité Laïque',
            'category': 'education',
            'description': 'Cours de français gratuits pour adultes. Tous niveaux.',
            'address': '22 Rue Corvisart, 75013 Paris',
            'phone': '+33 1 45 35 13 13',
            'hours': 'Mar-Jeu: 18h-20h',
            'location': {'lat': 48.8295, 'lng': 2.3507}
        },
        {
            'id': 'serv-7',
            'name': 'Restos du Cœur - Distribution',
            'category': 'food',
            'description': 'Aide alimentaire et produits de première nécessité.',
            'address': '45 Rue de Charenton, 75012 Paris',
            'phone': '+33 1 53 32 23 23',
            'hours': 'Lun-Mer-Ven: 14h-17h',
            'location': {'lat': 48.8478, 'lng': 2.3771}
        },
        {
            'id': 'serv-8',
            'name': 'Médecins du Monde - Consultations',
            'category': 'health',
            'description': 'Consultations médicales gratuites. Sans rendez-vous.',
            'address': '62 Avenue Parmentier, 75011 Paris',
            'phone': '+33 1 44 92 15 15',
            'hours': 'Lun-Ven: 9h-12h',
            'location': {'lat': 48.8636, 'lng': 2.3751}
        }
    ]
    
    existing_count = await db.services.count_documents({})
    if existing_count == 0:
        await db.services.insert_many(services)
        print(f"✅ {len(services)} serviços inseridos!")
    else:
        print(f"ℹ️ Base já possui {existing_count} serviços")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_services())
