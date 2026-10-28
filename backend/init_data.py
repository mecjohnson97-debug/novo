import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def init_services():
    print("Inicializando serviços do Watizat...")
    
    services = [
        {
            "id": "1",
            "name": "Secours Catholique - Distribution Alimentaire",
            "category": "food",
            "description": "Distribuição de alimentos para pessoas em situação de vulnerabilidade",
            "address": "15 Rue de Maubeuge, 75009 Paris",
            "phone": "01 45 49 73 00",
            "hours": "Seg-Sex: 9h-17h"
        },
        {
            "id": "2",
            "name": "La Cimade - Aide Juridique",
            "category": "legal",
            "description": "Assistência jurídica gratuita para migrantes e refugiados",
            "address": "176 Rue de Grenelle, 75007 Paris",
            "phone": "01 40 08 05 34",
            "hours": "Ter-Qui: 14h-18h"
        },
        {
            "id": "3",
            "name": "PASS - Permanence d'Accès aux Soins",
            "category": "health",
            "description": "Atendimento médico gratuito para pessoas sem cobertura de saúde",
            "address": "Hôpital Saint-Louis, 1 Avenue Claude Vellefaux, 75010 Paris",
            "phone": "01 42 49 49 49",
            "hours": "Seg-Sex: 8h30-17h"
        },
        {
            "id": "4",
            "name": "France Terre d'Asile - Hébergement",
            "category": "housing",
            "description": "Centro de acolhimento para solicitantes de asilo",
            "address": "24 Rue Marc Seguin, 75018 Paris",
            "phone": "01 53 04 39 99",
            "hours": "Seg-Sex: 9h-18h"
        },
        {
            "id": "5",
            "name": "Pôle Emploi International",
            "category": "work",
            "description": "Ajuda na busca de emprego e orientação profissional",
            "address": "48 Boulevard de la Bastille, 75012 Paris",
            "phone": "39 49",
            "hours": "Seg-Sex: 8h30-16h30"
        },
        {
            "id": "6",
            "name": "CASNAV - Centre Académique",
            "category": "education",
            "description": "Escolarização de crianças migrantes recém-chegadas",
            "address": "12 Boulevard d'Indochine, 75019 Paris",
            "phone": "01 44 62 39 36",
            "hours": "Seg-Sex: 9h-17h"
        },
        {
            "id": "7",
            "name": "Emmaüs Solidarité",
            "category": "social",
            "description": "Apoio social e atividades comunitárias",
            "address": "4 Rue des Amandiers, 75020 Paris",
            "phone": "01 43 58 24 52",
            "hours": "Seg-Sex: 10h-18h"
        },
        {
            "id": "8",
            "name": "Croix-Rouge Française - Vestiaire",
            "category": "social",
            "description": "Distribuição de roupas e produtos de higiene",
            "address": "43 Rue de Valmy, 93100 Montreuil",
            "phone": "01 48 51 96 00",
            "hours": "Qua e Sex: 14h-17h"
        },
        {
            "id": "9",
            "name": "Restaurants du Coeur",
            "category": "food",
            "description": "Distribuição gratuita de refeições",
            "address": "42 Rue Championnet, 75018 Paris",
            "phone": "01 53 32 23 23",
            "hours": "Seg-Sex: 11h30-13h30"
        },
        {
            "id": "10",
            "name": "GISTI - Groupe d'Information",
            "category": "legal",
            "description": "Informação e apoio jurídico sobre direitos dos estrangeiros",
            "address": "3 Villa Marcès, 75011 Paris",
            "phone": "01 43 14 84 84",
            "hours": "Seg-Sex: 14h-18h (com agendamento)"
        }
    ]
    
    await db.services.delete_many({})
    
    await db.services.insert_many(services)
    
    print(f"✅ {len(services)} serviços inseridos com sucesso!")

if __name__ == "__main__":
    asyncio.run(init_services())
    print("Inicialização concluída!")
