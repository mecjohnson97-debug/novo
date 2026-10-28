"""
Script para criar ou promover usuário para ADMIN
Execute este script para ter acesso ao Dashboard Administrativo
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import bcrypt
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

MONGO_URL = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.getenv('DB_NAME', 'test_database')

async def create_admin_user():
    """Cria um novo usuário administrador"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("🔐 CRIAR USUÁRIO ADMINISTRADOR - WATIZAT")
    print("=" * 60)
    print()
    
    # Dados do admin
    print("Por favor, forneça os dados do administrador:")
    print()
    
    username = (await asyncio.to_thread(input, "👤 Nome de usuário (ex: admin): ")).strip()
    if not username:
        print("❌ Nome de usuário é obrigatório!")
        return
    
    # Verificar se já existe
    existing = await db.users.find_one({"username": username})
    if existing:
        print(f"⚠️  Usuário '{username}' já existe!")
        promote = (await asyncio.to_thread(input, "Deseja promover este usuário para admin? (s/n): ")).strip().lower()
        if promote == 's':
            result = await db.users.update_one(
                {"username": username},
                {"$set": {"role": "admin"}}
            )
            if result.modified_count > 0:
                print(f"✅ Usuário '{username}' promovido para ADMIN com sucesso!")
                print()
                print("🎉 Agora você pode acessar o dashboard em:")
                print("   👉 /admin")
                print()
            else:
                print("⚠️  Usuário já é admin!")
        return
    
    email = (await asyncio.to_thread(input, "📧 Email: ")).strip()
    full_name = (await asyncio.to_thread(input, "📝 Nome completo: ")).strip() or username
    password = (await asyncio.to_thread(input, "🔒 Senha (mínimo 6 caracteres): ")).strip()
    
    if len(password) < 6:
        print("❌ Senha deve ter no mínimo 6 caracteres!")
        return
    
    # Hash da senha
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Criar admin
    admin_user = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password": hashed_password.decode('utf-8'),
        "role": "admin",
        "created_at": datetime.utcnow(),
        "categories": [],
        "location": {
            "lat": 48.8566,  # Paris
            "lng": 2.3522
        }
    }
    
    try:
        result = await db.users.insert_one(admin_user)
        print()
        print("=" * 60)
        print("✅ ADMINISTRADOR CRIADO COM SUCESSO!")
        print("=" * 60)
        print()
        print(f"👤 Usuário: {username}")
        print(f"📧 Email: {email}")
        print(f"👑 Função: ADMINISTRADOR")
        print()
        print("🎉 Agora você pode fazer login e acessar:")
        print("   👉 Dashboard Admin: /admin")
        print()
        print("📊 No Dashboard você pode:")
        print("   • Ver estatísticas em tempo real")
        print("   • Gerenciar usuários")
        print("   • Gerenciar posts")
        print("   • Criar anúncios e divulgações")
        print("   • Gerenciar vagas de emprego")
        print("   • Ver lista de voluntários")
        print()
    except Exception as e:
        print(f"❌ Erro ao criar administrador: {e}")
    finally:
        client.close()

async def list_users():
    """Lista todos os usuários e seus roles"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("👥 USUÁRIOS CADASTRADOS")
    print("=" * 60)
    print()
    
    users = await db.users.find({}).to_list(length=100)
    
    if not users:
        print("Nenhum usuário encontrado.")
    else:
        for i, user in enumerate(users, 1):
            role_emoji = "👑" if user.get('role') == 'admin' else "👤"
            print(f"{i}. {role_emoji} {user.get('username')} - {user.get('role', 'migrant')} ({user.get('email', 'sem email')})")
    
    print()
    client.close()

async def promote_user():
    """Promove um usuário existente para admin"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 60)
    print("⬆️  PROMOVER USUÁRIO PARA ADMIN")
    print("=" * 60)
    print()
    
    username = (await asyncio.to_thread(input, "Digite o nome de usuário para promover: ")).strip()
    
    result = await db.users.update_one(
        {"username": username},
        {"$set": {"role": "admin"}}
    )
    
    if result.matched_count == 0:
        print(f"❌ Usuário '{username}' não encontrado!")
    elif result.modified_count == 0:
        print(f"⚠️  Usuário '{username}' já é admin!")
    else:
        print(f"✅ Usuário '{username}' promovido para ADMIN com sucesso!")
        print()
        print("🎉 Agora este usuário pode acessar /admin")
    
    print()
    client.close()

async def main():
    """Menu principal"""
    while True:
        print()
        print("=" * 60)
        print("🎯 GERENCIAMENTO DE ADMINISTRADORES - WATIZAT")
        print("=" * 60)
        print()
        print("1. 👑 Criar novo administrador")
        print("2. ⬆️  Promover usuário existente para admin")
        print("3. 👥 Listar todos os usuários")
        print("4. ❌ Sair")
        print()
        
        choice = (await asyncio.to_thread(input, "Escolha uma opção: ")).strip()
        
        if choice == '1':
            await create_admin_user()
        elif choice == '2':
            await promote_user()
        elif choice == '3':
            await list_users()
        elif choice == '4':
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Saindo...")
        sys.exit(0)
