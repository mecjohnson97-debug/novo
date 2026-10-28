from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.responses import Response, RedirectResponse
import base64
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from openai import AsyncOpenAI
from pdf_processor import WatizatPDFProcessor
from auto_responses import get_auto_response, format_auto_response_post
from help_locations import HELP_LOCATIONS, get_all_help_locations, get_help_locations_by_category
import math
from urllib.parse import urlparse
import aiohttp
import re
import random
import asyncio
import json
import hashlib
from fastapi import UploadFile, File, Request
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId
from email_service import send_email, reset_code_email

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)

# Extrai o nome do banco de dados da URL ou usa DB_NAME
def get_database_name():
    db_name = os.environ.get('DB_NAME', '')
    if db_name and db_name != 'test_database':
        return db_name
    
    # Tenta extrair da MONGO_URL
    parsed = urlparse(mongo_url)
    if parsed.path and len(parsed.path) > 1:
        # Remove a barra inicial
        extracted_db = parsed.path.lstrip('/')
        # Remove parâmetros de query se existirem
        if '?' in extracted_db:
            extracted_db = extracted_db.split('?')[0]
        if extracted_db:
            return extracted_db
    
    # Fallback para o DB_NAME ou padrão
    return db_name if db_name else 'watizat_db'

db = client[get_database_name()]

app = FastAPI()

# CORS deve estar ANTES de tudo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas as origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

api_router = APIRouter(prefix="/api")

@api_router.get("/")
async def root():
    return {"message": "Watizat API - Bem-vindo!"}

security = HTTPBearer()
JWT_SECRET = os.environ.get('JWT_SECRET', 'default_secret')
ALGORITHM = "HS256"

pdf_processor = WatizatPDFProcessor()

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    display_name: Optional[str] = None
    use_display_name: bool = False
    role: str
    location: Optional[dict] = None
    bio: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    avatar_version: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AvatarUpload(BaseModel):
    image: str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str
    languages: List[str] = Field(default_factory=list)
    professional_area: Optional[str] = None
    professional_specialties: Optional[List[str]] = Field(default_factory=list)
    availability: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    certifications: Optional[List[str]] = Field(default_factory=list)
    professional_id: Optional[str] = None
    organization: Optional[str] = None
    years_experience: Optional[str] = None
    help_types: Optional[List[str]] = Field(default_factory=list)
    help_categories: Optional[List[str]] = Field(default_factory=list)  # Categorias de ajuda que voluntário oferece
    need_categories: Optional[List[str]] = Field(default_factory=list)  # Categorias de ajuda que migrante precisa
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[dict] = None  # {lat: float, lng: float, address: str}
    show_location: bool = False  # Se quer mostrar localização no feed

class UserLogin(BaseModel):
    email: str
    password: str

class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    category: str  # Categoria principal
    categories: List[str] = Field(default_factory=list)  # Múltiplas categorias
    title: str
    description: str
    location: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PostCreate(BaseModel):
    type: str
    category: str  # Categoria principal
    categories: Optional[List[str]] = Field(default_factory=list)  # Múltiplas categorias (até 3)
    title: str
    description: str
    location: Optional[dict] = None
    images: Optional[List[str]] = Field(default_factory=list)

class PostComment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    post_id: str
    user_id: str
    comment: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Advertisement(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # 'motivation', 'donation', 'sponsor'
    title: str
    content: str
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    link_text: Optional[str] = None
    is_active: bool = True
    priority: int = 0  # Higher = more important
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AdvertisementCreate(BaseModel):
    type: str
    title: str
    content: str
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    link_text: Optional[str] = None
    is_active: bool = True
    priority: int = 0


class PostCommentCreate(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)

class Service(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    description: str
    address: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[dict] = None
    hours: Optional[str] = None

class AIMessage(BaseModel):
    message: str
    language: str = "pt"

class Match(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    helper_id: str
    migrant_id: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Housing Models
class HousingListing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    listing_type: str  # 'offer' or 'need'
    title: str
    description: Optional[str] = None
    city: str
    address: Optional[str] = None
    accommodation_type: str = 'room'  # room, sofa, house, shared
    duration: str = 'temporary'  # emergency, temporary, long_term, exchange
    max_guests: int = 1
    amenities: List[str] = []
    pets_allowed: bool = False
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    exchange_services: Optional[str] = None
    photos: List[str] = []
    listing_status: str = 'active'  # active, matched, closed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HousingListingCreate(BaseModel):
    listing_type: str
    title: str
    description: Optional[str] = None
    city: str
    address: Optional[str] = None
    accommodation_type: str = 'room'
    duration: str = 'temporary'
    max_guests: int = 1
    amenities: List[str] = []
    pets_allowed: bool = False
    available_from: Optional[str] = None
    available_until: Optional[str] = None
    exchange_services: Optional[str] = None
    photos: List[str] = []

def create_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id = payload.get('user_id')
        
        user = await db.users.find_one({'id': user_id}, {'_id': 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def email_query(email: str):
    return {'$regex': f'^{re.escape(email.strip())}$', '$options': 'i'}

def is_admin_email(email: str) -> bool:
    admins = {e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()}
    return (email or '').strip().lower() in admins


@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    user_data.email = user_data.email.strip().lower()
    existing = await db.users.find_one({'email': email_query(user_data.email)}, {'_id': 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pw = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        role='admin' if is_admin_email(user_data.email) else user_data.role,
        languages=user_data.languages
    )
    
    user_dict = user.model_dump()
    user_dict['password'] = hashed_pw.decode()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    if user_data.role == 'volunteer':
        user_dict['professional_area'] = user_data.professional_area
        user_dict['professional_specialties'] = user_data.professional_specialties or []
        user_dict['availability'] = user_data.availability
        user_dict['experience'] = user_data.experience
        user_dict['education'] = user_data.education
        user_dict['certifications'] = user_data.certifications or []
        user_dict['professional_id'] = user_data.professional_id
        user_dict['organization'] = user_data.organization
        user_dict['years_experience'] = user_data.years_experience
        user_dict['help_types'] = user_data.help_types or []
        user_dict['help_categories'] = user_data.help_categories or []
        user_dict['phone'] = user_data.phone
        user_dict['linkedin'] = user_data.linkedin
        user_dict['location'] = user_data.location
        user_dict['show_location'] = user_data.show_location
    
    if user_data.role == 'migrant':
        user_dict['need_categories'] = user_data.need_categories or []
        user_dict['location'] = user_data.location
        user_dict['show_location'] = user_data.show_location
    
    if user_data.role == 'helper':
        user_dict['help_categories'] = user_data.help_categories or []
        user_dict['location'] = user_data.location
        user_dict['show_location'] = user_data.show_location
    
    await db.users.insert_one(user_dict)
    
    token = create_token(user.id, user.email)
    return {'token': token, 'user': user}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user_data = await db.users.find_one({'email': email_query(credentials.email)}, {'_id': 0})
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(credentials.password.encode(), user_data['password'].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_data.pop('password')
    if is_admin_email(user_data['email']) and user_data.get('role') != 'admin':
        user_data['role'] = 'admin'
        await db.users.update_one({'id': user_data['id']}, {'$set': {'role': 'admin'}})
    if isinstance(user_data['created_at'], str):
        user_data['created_at'] = datetime.fromisoformat(user_data['created_at'])
    
    user = User(**user_data)
    token = create_token(user.id, user.email)
    
    return {'token': token, 'user': user}

@api_router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user

AVATAR_MAX_BYTES = 600_000
AVATAR_MIMES = {'image/jpeg', 'image/png', 'image/webp'}

@api_router.put("/profile/avatar")
async def upload_avatar(payload: AvatarUpload, current_user: User = Depends(get_current_user)):
    if len(payload.image) > 820_000:
        raise HTTPException(status_code=413, detail='Imagem muito grande')
    header, _, data = payload.image.partition(',')
    mime = header[5:].split(';')[0] if header.startswith('data:') else ''
    if mime not in AVATAR_MIMES or not data:
        raise HTTPException(status_code=400, detail='Formato de imagem inválido')
    try:
        raw = base64.b64decode(data, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail='Imagem inválida')
    if len(raw) > AVATAR_MAX_BYTES:
        raise HTTPException(status_code=413, detail='Imagem muito grande')
    version = int(datetime.now(timezone.utc).timestamp() * 1000)
    await db.avatars.update_one({'user_id': current_user.id}, {'$set': {'data': raw, 'mime': mime, 'version': version}}, upsert=True)
    await db.users.update_one({'id': current_user.id}, {'$set': {'avatar_version': version}})
    return {'avatar_version': version}

@api_router.delete("/profile/avatar")
async def delete_avatar(current_user: User = Depends(get_current_user)):
    await db.avatars.delete_one({'user_id': current_user.id})
    await db.users.update_one({'id': current_user.id}, {'$unset': {'avatar_version': ''}})
    return {'avatar_version': None}

@api_router.get("/users/{user_id}/avatar")
async def get_avatar(user_id: str):
    doc = await db.avatars.find_one({'user_id': user_id}, {'_id': 0, 'data': 1, 'mime': 1})
    if not doc:
        raise HTTPException(status_code=404, detail='Sem foto')
    return Response(content=bytes(doc['data']), media_type=doc['mime'], headers={'Cache-Control': 'public, max-age=31536000, immutable'})

@api_router.put("/profile")
async def update_profile(updates: dict, current_user: User = Depends(get_current_user)):
    allowed_fields = ['name', 'bio', 'location', 'languages', 'categories', 'help_categories', 'need_categories', 'display_name', 'use_display_name']
    update_data = {k: v for k, v in updates.items() if k in allowed_fields}
    
    await db.users.update_one({'id': current_user.id}, {'$set': update_data})
    
    updated_user = await db.users.find_one({'id': current_user.id}, {'_id': 0, 'password': 0})
    if isinstance(updated_user['created_at'], str):
        updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
    
    return User(**updated_user)

@api_router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, current_user: User = Depends(get_current_user)):
    # Se não há categorias múltiplas, usar a categoria principal
    categories_list = post_data.categories if post_data.categories else [post_data.category]
    
    post = Post(
        user_id=current_user.id,
        type=post_data.type,
        category=post_data.category,
        categories=categories_list,
        title=post_data.title,
        description=post_data.description,
        location=post_data.location
    )
    
    post_dict = post.model_dump()
    post_dict['created_at'] = post_dict['created_at'].isoformat()
    post_dict['images'] = post_data.images or []
    
    await db.posts.insert_one(post_dict)
    
    # Enviar resposta automática para cada categoria selecionada
    if post_data.type == 'need':
        for cat in categories_list:
            auto_response = get_auto_response(cat)
            if auto_response:
                message_data = {
                    'id': str(uuid.uuid4()),
                    'from_user_id': 'system',
                    'to_user_id': current_user.id,
                    'message': f"{auto_response['title']}\n\n{auto_response['content']}",
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'is_auto_response': True
                }
                await db.messages.insert_one(message_data)
    
    return post

@api_router.post("/posts/{post_id}/comments")
async def add_comment(post_id: str, comment_data: PostCommentCreate, current_user: User = Depends(get_current_user)):
    if not await db.posts.find_one({'id': post_id}, {'_id': 1}):
        raise HTTPException(status_code=404, detail='Post não encontrado')
    comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        comment=comment_data.comment
    )
    
    comment_dict = comment.model_dump()
    comment_dict['created_at'] = comment_dict['created_at'].isoformat()
    
    await db.comments.insert_one(comment_dict)
    return comment

@api_router.get("/posts/{post_id}/comments")
async def get_comments(post_id: str):
    comments = await db.comments.find({'post_id': post_id}, {'_id': 0}).sort('created_at', 1).to_list(500)
    ids = list({c['user_id'] for c in comments})
    users = {u['id']: u async for u in db.users.find({'id': {'$in': ids}}, {'_id': 0, 'id': 1, 'name': 1, 'role': 1, 'avatar_version': 1})}
    for comment in comments:
        user = users.get(comment['user_id'])
        if user:
            comment['user'] = {'id': user['id'], 'name': user['name'], 'role': user['role'], 'avatar_version': user.get('avatar_version')}
    
    return comments

@api_router.get("/posts")
async def get_posts(
    type: Optional[str] = None,
    category: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 10,
    skip: int = 0,
    current_user: User = Depends(get_current_user)
):
    # Filtros aplicados no banco (antes eram aplicados em Python após carregar 100 posts com imagens base64)
    limit = max(1, min(limit, 50))
    skip = max(0, skip)
    conditions = [{'is_auto_response': {'$ne': True}}]
    if type:
        conditions.append({'type': type})
    if user_id:
        conditions.append({'user_id': user_id})
    if category:
        conditions.append({'$or': [{'category': category}, {'categories': category}]})

    if current_user.role in ['volunteer', 'helper']:
        user_data = await db.users.find_one({'id': current_user.id}, {'_id': 0, 'help_categories': 1})
        help_cats = (user_data or {}).get('help_categories') or []
        if help_cats:
            conditions.append({'$or': [
                {'type': {'$ne': 'need'}},
                {'category': {'$in': help_cats}},
                {'categories': {'$in': help_cats}}
            ]})

    # Imagens base64 NÃO vão no JSON do feed; são servidas por /posts/{id}/images/{idx}
    pipeline = [
        {'$match': {'$and': conditions}},
        {'$addFields': {'is_boosted': {'$gt': [{'$ifNull': ['$boosted_until', '']}, datetime.now(timezone.utc).isoformat()]}}},
        {'$sort': {'is_boosted': -1, 'created_at': -1}},
        {'$skip': skip},
        {'$limit': limit + 1},
        {'$addFields': {'image_count': {'$size': {'$ifNull': ['$images', []]}}}},
        {'$project': {'_id': 0, 'images': 0}}
    ]
    posts = await db.posts.aggregate(pipeline).to_list(limit + 1)
    has_more = len(posts) > limit
    posts = posts[:limit]

    post_ids = [p['id'] for p in posts]
    user_ids = list({p['user_id'] for p in posts if p.get('user_id') != 'system'})
    users_dict = {}
    if user_ids:
        async for u in db.users.find({'id': {'$in': user_ids}}, {'_id': 0, 'id': 1, 'name': 1, 'display_name': 1, 'use_display_name': 1, 'role': 1, 'avatar_version': 1}):
            users_dict[u['id']] = u
    comment_counts = {}
    if post_ids:
        async for c in db.comments.aggregate([
            {'$match': {'post_id': {'$in': post_ids}}},
            {'$group': {'_id': '$post_id', 'n': {'$sum': 1}}}
        ]):
            comment_counts[c['_id']] = c['n']

    for post in posts:
        if post.get('user_id') == 'system':
            post['user'] = {'name': 'Watizat Assistant', 'role': 'assistant'}
        else:
            u = users_dict.get(post.get('user_id'))
            if u:
                name = u.get('display_name') if u.get('use_display_name') and u.get('display_name') else u.get('name')
                post['user'] = {'id': u['id'], 'name': name, 'role': u.get('role'), 'avatar_version': u.get('avatar_version')}
        if not post.get('categories'):
            post['categories'] = [post['category']] if post.get('category') else []
        post['image_urls'] = [f"/api/posts/{post['id']}/images/{i}" for i in range(post.pop('image_count', 0))]
        post['video_url'] = f"/api/posts/{post['id']}/video" if post.get('has_video') else None
        post['comment_count'] = comment_counts.get(post['id'], 0)
        post['can_help'] = True

    return {'posts': posts, 'has_more': has_more, 'next_skip': skip + len(posts)}


@api_router.get("/posts/{post_id}/images/{idx}")
async def get_post_image(post_id: str, idx: int):
    doc = await db.posts.find_one({'id': post_id}, {'_id': 0, 'images': {'$slice': [idx, 1]}})
    if not doc or not doc.get('images'):
        raise HTTPException(status_code=404, detail='Imagem não encontrada')
    img = doc['images'][0]
    headers = {'Cache-Control': 'public, max-age=604800, immutable'}
    if isinstance(img, str) and img.startswith('data:'):
        header, _, data = img.partition(',')
        mime = header[5:].split(';')[0] or 'image/jpeg'
        return Response(content=base64.b64decode(data), media_type=mime, headers=headers)
    if isinstance(img, str) and img.startswith('http'):
        return RedirectResponse(img)
    raise HTTPException(status_code=404, detail='Imagem inválida')

@api_router.get("/services")
async def get_services(category: Optional[str] = None):
    query = {}
    if category:
        query['category'] = category
    
    services = await db.services.find(query, {'_id': 0}).to_list(100)
    return services

@api_router.post("/ai/chat")
async def ai_chat(message_data: AIMessage, current_user: User = Depends(get_current_user)):
    try:
        # Verificar se a chave OpenAI está configurada
        providers = [
            (os.environ.get('OPENROUTER_API_KEY'), "https://openrouter.ai/api/v1", os.environ.get('OPENROUTER_MODEL', 'google/gemma-4-31b-it:free')),
            (os.environ.get('GROQ_API_KEY'), "https://api.groq.com/openai/v1", os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')),
            (os.environ.get('OPENAI_API_KEY'), None, 'gpt-4o-mini'),
        ]
        providers = [p for p in providers if p[0]]
        
        if not providers:
            # Retornar resposta baseada no guia Watizat sem IA
            pdf_processor.load_index()
            relevant_chunks = pdf_processor.search(message_data.message, k=3)
            
            if relevant_chunks:
                context_response = f"""Encontrei as seguintes informações no Guia Watizat que podem ajudar:

{chr(10).join([f"• {chunk[:300]}..." if len(chunk) > 300 else f"• {chunk}" for chunk in relevant_chunks[:3]])}

Para mais informações, consulte o Guia Watizat completo ou entre em contato com um voluntário."""
            else:
                context_response = """Não encontrei informações específicas sobre sua pergunta no guia.

Você pode:
• Criar um post na seção "Preciso de Ajuda"
• Entrar em contato com voluntários disponíveis
• Consultar os locais de ajuda no mapa

Estamos aqui para ajudar!"""
            
            chat_record = {
                'id': str(uuid.uuid4()),
                'user_id': current_user.id,
                'message': message_data.message,
                'response': context_response,
                'language': message_data.language,
                'ai_enabled': False,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.ai_chats.insert_one(chat_record)
            
            return {'response': context_response, 'sources': relevant_chunks[:2] if relevant_chunks else [], 'ai_enabled': False}
        
        # Com chave OpenAI - usar IA
        pdf_processor.load_index()
        relevant_chunks = pdf_processor.search(message_data.message, k=3)
        
        context = "\n\n".join(relevant_chunks) if relevant_chunks else "Informação não encontrada no guia Watizat."
        
        system_message = f"""Você é um assistente especializado em ajudar migrantes em Paris. 
        Use as informações do guia Watizat abaixo para responder perguntas.
        Seja empático, claro e objetivo. Responda em {message_data.language}.
        
        Contexto do Watizat:
        {context}
        """
        
        # OpenRouter -> Groq -> OpenAI (fallback em caso de erro)
        ai_response = None
        last_error = None
        for key, base_url, model in providers:
            try:
                client_ai = AsyncOpenAI(api_key=key, base_url=base_url) if base_url else AsyncOpenAI(api_key=key)
                response = await client_ai.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": message_data.message}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                ai_response = response.choices[0].message.content
                break
            except Exception as e:
                last_error = e
                logging.warning(f"AI provider {base_url or 'openai'} failed: {e}")
        if ai_response is None:
            raise last_error
        
        chat_record = {
            'id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'message': message_data.message,
            'response': ai_response,
            'language': message_data.language,
            'ai_enabled': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        await db.ai_chats.insert_one(chat_record)
        
        return {'response': ai_response, 'sources': relevant_chunks[:2] if relevant_chunks else [], 'ai_enabled': True}
    
    except Exception as e:
        logging.error(f"AI Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing message")

@api_router.post("/matches")
async def create_match(helper_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != 'migrant':
        raise HTTPException(status_code=400, detail="Only migrants can create matches")
    
    match = Match(
        helper_id=helper_id,
        migrant_id=current_user.id,
        status='pending'
    )
    
    match_dict = match.model_dump()
    match_dict['created_at'] = match_dict['created_at'].isoformat()
    
    await db.matches.insert_one(match_dict)
    return match

@api_router.get("/matches")
async def get_matches(current_user: User = Depends(get_current_user)):
    query = {}
    if current_user.role == 'migrant':
        query['migrant_id'] = current_user.id
    else:
        query['helper_id'] = current_user.id
    
    matches = await db.matches.find(query, {'_id': 0}).to_list(100)
    return matches

@api_router.get("/admin/stats")
async def admin_stats(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    total_users = await db.users.count_documents({})
    total_posts = await db.posts.count_documents({})
    total_matches = await db.matches.count_documents({})
    total_volunteers = await db.users.count_documents({'role': 'volunteer'})
    total_migrants = await db.users.count_documents({'role': 'migrant'})
    total_messages = await db.messages.count_documents({})
    
    # Posts por categoria
    posts_by_category = {}
    categories = ['food', 'legal', 'health', 'housing', 'work', 'education', 'social', 'clothes', 'furniture', 'transport']
    for cat in categories:
        count = await db.posts.count_documents({'category': cat})
        posts_by_category[cat] = count
    
    # Posts por tipo
    needs_count = await db.posts.count_documents({'type': 'need'})
    offers_count = await db.posts.count_documents({'type': 'offer'})
    
    return {
        'total_users': total_users,
        'total_posts': total_posts,
        'total_matches': total_matches,
        'total_volunteers': total_volunteers,
        'total_migrants': total_migrants,
        'total_messages': total_messages,
        'posts_by_category': posts_by_category,
        'needs_count': needs_count,
        'offers_count': offers_count
    }

@api_router.get("/admin/users")
async def admin_get_users(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    users = await db.users.find({}, {'_id': 0, 'password': 0}).sort('created_at', -1).to_list(1000)
    
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return users

@api_router.get("/admin/posts")
async def admin_get_posts(current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    posts = await db.posts.find({}, {'_id': 0}).sort('created_at', -1).to_list(1000)
    
    # Batch fetch all unique user_ids to avoid N+1 queries
    user_ids = list(set(post['user_id'] for post in posts if post.get('user_id')))
    users_dict = {}
    if user_ids:
        users_cursor = db.users.find({'id': {'$in': user_ids}}, {'_id': 0, 'password': 0, 'email': 0})
        async for user in users_cursor:
            users_dict[user['id']] = user
    
    for post in posts:
        if isinstance(post.get('created_at'), str):
            post['created_at'] = datetime.fromisoformat(post['created_at'])
        # Get user info from batch
        user = users_dict.get(post.get('user_id'))
        if user:
            post['user'] = {'name': user['name'], 'role': user['role']}
    
    return posts

@api_router.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Don't allow deleting yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.users.delete_one({'id': user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Also delete user's posts and messages
    await db.posts.delete_many({'user_id': user_id})
    await db.messages.delete_many({'$or': [{'from_user_id': user_id}, {'to_user_id': user_id}]})
    
    return {'message': 'User deleted successfully'}

@api_router.delete("/admin/posts/{post_id}")
async def admin_delete_post(post_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await db.posts.delete_one({'id': post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Also delete comments
    await db.comments.delete_many({'post_id': post_id})
    
    return {'message': 'Post deleted successfully'}

@api_router.put("/admin/users/{user_id}/role")
async def admin_update_user_role(user_id: str, role_data: dict, current_user: User = Depends(get_current_user)):
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    new_role = role_data.get('role')
    if new_role not in ['migrant', 'volunteer', 'helper', 'admin']:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.users.update_one({'id': user_id}, {'$set': {'role': new_role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {'message': 'Role updated successfully'}

class DirectMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_user_id: str
    to_user_id: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DirectMessageCreate(BaseModel):
    to_user_id: str
    message: str
    location: Optional[dict] = None
    media: Optional[List[str]] = Field(default_factory=list)
    media_type: Optional[str] = None

@api_router.post("/messages")
async def send_message(msg_data: DirectMessageCreate, current_user: User = Depends(get_current_user)):
    message = DirectMessage(
        from_user_id=current_user.id,
        to_user_id=msg_data.to_user_id,
        message=msg_data.message
    )
    
    msg_dict = message.model_dump()
    msg_dict['created_at'] = msg_dict['created_at'].isoformat()
    msg_dict['location'] = msg_data.location
    msg_dict['media'] = msg_data.media or []
    msg_dict['media_type'] = msg_data.media_type
    
    await db.messages.insert_one(msg_dict)
    return message

@api_router.get("/messages/{other_user_id}")
async def get_messages(other_user_id: str, current_user: User = Depends(get_current_user)):
    messages = await db.messages.find({
        '$or': [
            {'from_user_id': current_user.id, 'to_user_id': other_user_id},
            {'from_user_id': other_user_id, 'to_user_id': current_user.id}
        ]
    }, {'_id': 0}).sort('created_at', 1).to_list(1000)
    
    for msg in messages:
        if isinstance(msg['created_at'], str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
        appt = msg.get('appointment')
        if appt and msg['to_user_id'] == current_user.id and appt.get('status') != 'accepted':
            appt['has_info'] = bool(appt.get('info'))
            appt['info'] = None
    
    return messages

@api_router.get("/conversations")
async def get_conversations(current_user: User = Depends(get_current_user)):
    messages = await db.messages.find({
        '$or': [
            {'from_user_id': current_user.id},
            {'to_user_id': current_user.id}
        ]
    }, {'_id': 0}).to_list(10000)
    
    user_ids = set()
    for msg in messages:
        if msg['from_user_id'] != current_user.id:
            user_ids.add(msg['from_user_id'])
        if msg['to_user_id'] != current_user.id:
            user_ids.add(msg['to_user_id'])
    
    # Batch fetch all users to avoid N+1 queries
    user_ids_list = list(user_ids)
    users_dict = {}
    if user_ids_list:
        users_cursor = db.users.find({'id': {'$in': user_ids_list}}, {'_id': 0, 'password': 0})
        async for user in users_cursor:
            users_dict[user['id']] = user
    
    # Get last messages for each conversation in batch
    last_messages = {}
    for uid in user_ids_list:
        relevant_msgs = [m for m in messages if 
            (m['from_user_id'] == uid and m['to_user_id'] == current_user.id) or
            (m['from_user_id'] == current_user.id and m['to_user_id'] == uid)]
        if relevant_msgs:
            # Sort by created_at and get last one
            sorted_msgs = sorted(relevant_msgs, key=lambda x: x.get('created_at', ''), reverse=True)
            last_messages[uid] = sorted_msgs[0]
    
    conversations = []
    for uid in user_ids:
        user = users_dict.get(uid)
        if user:
            if isinstance(user.get('created_at'), str):
                user['created_at'] = datetime.fromisoformat(user['created_at'])
            
            last_msg = last_messages.get(uid)
            conversations.append({
                'user': user,
                'last_message': last_msg['message'] if last_msg else '',
                'last_message_time': last_msg['created_at'] if last_msg else None
            })
    
    return conversations

@api_router.get("/users/{user_id}")
async def get_user_by_id(user_id: str, current_user: User = Depends(get_current_user)):
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'password': 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if isinstance(user.get('created_at'), str):
        user['created_at'] = datetime.fromisoformat(user['created_at'])
    
    return user

@api_router.get("/can-chat/{other_user_id}")
async def can_chat_with_user(other_user_id: str, current_user: User = Depends(get_current_user)):
    """
    Verifica se o usuário atual pode iniciar chat com outro usuário.
    Para voluntários e helpers, só podem conversar com migrantes se tiverem categorias de ajuda compatíveis.
    """
    other_user = await db.users.find_one({'id': other_user_id}, {'_id': 0})
    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    current_user_data = await db.users.find_one({'id': current_user.id}, {'_id': 0})
    
    # Migrantes podem conversar com qualquer voluntário ou helper
    if current_user.role == 'migrant':
        return {'can_chat': True, 'reason': 'allowed'}
    
    # Voluntários e helpers só podem conversar com migrantes se tiverem categorias compatíveis
    if current_user.role in ['volunteer', 'helper'] and other_user.get('role') == 'migrant':
        helper_categories = current_user_data.get('help_categories', []) if current_user_data else []
        
        if not helper_categories:
            # Se não definiu categorias, permitir chat (legacy)
            return {'can_chat': True, 'reason': 'no_categories_defined'}
        
        # Primeiro verificar need_categories do migrante
        migrant_need_categories = other_user.get('need_categories', [])
        
        if migrant_need_categories:
            # Verificar match entre need_categories do migrante e help_categories
            for cat in migrant_need_categories:
                if cat in helper_categories:
                    return {'can_chat': True, 'reason': 'category_match', 'matching_category': cat}
        
        # Se migrante não tem need_categories, verificar pelos posts
        migrant_posts = await db.posts.find({'user_id': other_user_id, 'type': 'need'}, {'_id': 0}).to_list(100)
        
        if not migrant_posts and not migrant_need_categories:
            # Se o migrante não tem posts nem need_categories, permitir chat
            return {'can_chat': True, 'reason': 'no_needs_defined'}
        
        # Verificar se há algum post do migrante em categoria que pode ajudar
        for post in migrant_posts:
            if post.get('category') in helper_categories:
                return {'can_chat': True, 'reason': 'category_match', 'matching_category': post.get('category')}
        
        return {'can_chat': False, 'reason': 'no_matching_categories'}
    
    # Outros casos: permitir
    return {'can_chat': True, 'reason': 'allowed'}

@api_router.get("/volunteers")
async def get_volunteers(area: Optional[str] = None):
    query = {'role': 'volunteer'}
    if area:
        query['professional_area'] = area
    
    volunteers = await db.users.find(query, {'_id': 0, 'password': 0, 'email': 0}).to_list(1000)
    
    for vol in volunteers:
        if isinstance(vol.get('created_at'), str):
            vol['created_at'] = datetime.fromisoformat(vol['created_at'])
    
    return volunteers

@api_router.get("/helpers-nearby")
async def get_helpers_nearby(
    lat: float, 
    lng: float, 
    category: Optional[str] = None,
    radius: float = 10.0,  # km
    current_user: User = Depends(get_current_user)
):
    """
    Busca helpers e voluntários próximos que podem ajudar em uma categoria específica.
    Usa fórmula de Haversine para calcular distância.
    """
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371  # Raio da Terra em km
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    # Buscar helpers e voluntários com localização visível
    query = {
        'role': {'$in': ['helper', 'volunteer']},
        'show_location': True,
        'location': {'$ne': None}
    }
    
    if category:
        query['help_categories'] = category
    
    users = await db.users.find(query, {'_id': 0, 'password': 0, 'email': 0}).to_list(1000)
    
    nearby_users = []
    for user in users:
        if user.get('location') and user['location'].get('lat') and user['location'].get('lng'):
            distance = haversine_distance(
                lat, lng,
                user['location']['lat'],
                user['location']['lng']
            )
            if distance <= radius:
                user['distance'] = round(distance, 2)
                if isinstance(user.get('created_at'), str):
                    user['created_at'] = datetime.fromisoformat(user['created_at'])
                nearby_users.append(user)
    
    # Ordenar por distância
    nearby_users.sort(key=lambda x: x['distance'])
    
    return nearby_users

@api_router.put("/profile/location")
async def update_location(location_data: dict, current_user: User = Depends(get_current_user)):
    """Atualiza a localização do usuário"""
    update = {
        'location': location_data.get('location'),
        'show_location': location_data.get('show_location', False)
    }
    
    await db.users.update_one({'id': current_user.id}, {'$set': update})
    return {'message': 'Location updated successfully'}

# ==================== HELP LOCATIONS ENDPOINTS ====================

def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calcula a distância em km entre duas coordenadas usando a fórmula de Haversine"""
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

class HelpLocationResponse(BaseModel):
    id: str
    name: str
    address: str
    phone: Optional[str]
    category: str
    hours: Optional[str]
    lat: float
    lng: float
    distance: Optional[float] = None
    icon: Optional[str] = None
    color: Optional[str] = None

CATEGORY_ICONS = {
    'food': {'icon': '🍽️', 'color': 'bg-green-500'},
    'health': {'icon': '🏥', 'color': 'bg-red-500'},
    'legal': {'icon': '⚖️', 'color': 'bg-blue-500'},
    'housing': {'icon': '🏠', 'color': 'bg-purple-500'},
    'clothes': {'icon': '👕', 'color': 'bg-orange-500'},
    'social': {'icon': '🤝', 'color': 'bg-pink-500'},
    'education': {'icon': '📚', 'color': 'bg-indigo-500'},
    'work': {'icon': '💼', 'color': 'bg-yellow-500'}
}

@api_router.get("/help-locations")
async def get_help_locations(
    category: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None
):
    """
    Retorna todos os locais de ajuda.
    Pode filtrar por categoria e ordenar por distância se coordenadas forem fornecidas.
    """
    # Buscar locais do arquivo de dados
    if category and category != 'all':
        locations = get_help_locations_by_category(category)
    else:
        locations = get_all_help_locations()
    
    # Adicionar ícones e cores
    result = []
    for loc in locations:
        loc_data = {**loc}
        cat_info = CATEGORY_ICONS.get(loc['category'], {'icon': '📍', 'color': 'bg-gray-500'})
        loc_data['icon'] = cat_info['icon']
        loc_data['color'] = cat_info['color']
        
        # Calcular distância se coordenadas foram fornecidas
        if lat is not None and lng is not None:
            loc_data['distance'] = round(calculate_distance(lat, lng, loc['lat'], loc['lng']), 2)
        
        result.append(loc_data)
    
    # Ordenar por distância se aplicável
    if lat is not None and lng is not None:
        result.sort(key=lambda x: x.get('distance', float('inf')))
    
    return {'locations': result, 'total': len(result)}

@api_router.get("/help-locations/nearest")
async def get_nearest_help_location(
    lat: float,
    lng: float,
    category: Optional[str] = None
):
    """
    Retorna o local de ajuda mais próximo das coordenadas fornecidas.
    Pode filtrar por categoria.
    """
    if category and category != 'all':
        locations = get_help_locations_by_category(category)
    else:
        locations = get_all_help_locations()
    
    if not locations:
        raise HTTPException(status_code=404, detail="Nenhum local encontrado")
    
    nearest = None
    min_distance = float('inf')
    
    for loc in locations:
        distance = calculate_distance(lat, lng, loc['lat'], loc['lng'])
        if distance < min_distance:
            min_distance = distance
            cat_info = CATEGORY_ICONS.get(loc['category'], {'icon': '📍', 'color': 'bg-gray-500'})
            nearest = {
                **loc,
                'distance': round(distance, 2),
                'icon': cat_info['icon'],
                'color': cat_info['color']
            }
    
    return {'nearest': nearest}

@api_router.get("/help-locations/categories")
async def get_help_location_categories():
    """Retorna todas as categorias disponíveis com contagem de locais"""
    locations = get_all_help_locations()
    
    # Contar locais por categoria
    category_counts = {}
    for loc in locations:
        cat = loc['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Formatar resposta com ícones
    categories = [
        {'value': 'all', 'label': 'Todos', 'icon': '🗺️', 'count': len(locations)}
    ]
    
    category_labels = {
        'food': 'Alimentação',
        'health': 'Saúde',
        'legal': 'Jurídico',
        'housing': 'Moradia',
        'clothes': 'Roupas',
        'social': 'Social',
        'education': 'Educação',
        'work': 'Trabalho'
    }
    
    for cat, count in sorted(category_counts.items()):
        cat_info = CATEGORY_ICONS.get(cat, {'icon': '📍', 'color': 'bg-gray-500'})
        categories.append({
            'value': cat,
            'label': category_labels.get(cat, cat.title()),
            'icon': cat_info['icon'],
            'color': cat_info['color'],
            'count': count
        })
    
    return {'categories': categories}

@api_router.post("/help-locations/seed")
async def seed_help_locations():
    """Popula o banco de dados com os locais de ajuda (operação única)"""
    locations = get_all_help_locations()
    
    # Verificar se já existem locais no banco
    existing_count = await db.help_locations.count_documents({})
    
    if existing_count > 0:
        return {'message': f'{existing_count} locais já existem no banco', 'seeded': False}
    
    # Inserir todos os locais
    for loc in locations:
        loc_with_metadata = {
            **loc,
            'created_at': datetime.now(timezone.utc)
        }
        await db.help_locations.insert_one(loc_with_metadata)
    
    return {'message': f'{len(locations)} locais adicionados com sucesso', 'seeded': True, 'count': len(locations)}

# ==================== ADVERTISEMENTS ENDPOINTS ====================

@api_router.get("/advertisements")
async def get_advertisements(type: Optional[str] = None, active_only: bool = True):
    """Retorna anúncios/divulgações para exibir na sidebar"""
    query = {}
    if type:
        query['type'] = type
    if active_only:
        query['is_active'] = True
    
    ads = await db.advertisements.find(query, {'_id': 0}).sort('priority', -1).to_list(50)
    return ads

@api_router.post("/admin/advertisements")
async def create_advertisement(ad_data: AdvertisementCreate, current_user: User = Depends(get_current_user)):
    """Cria um novo anúncio (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    ad = Advertisement(**ad_data.model_dump())
    ad_dict = ad.model_dump()
    
    await db.advertisements.insert_one(ad_dict)
    return {'message': 'Anúncio criado com sucesso', 'id': ad.id}

@api_router.get("/admin/advertisements")
async def admin_get_advertisements(current_user: User = Depends(get_current_user)):
    """Lista todos os anúncios (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    ads = await db.advertisements.find({}, {'_id': 0}).sort('created_at', -1).to_list(100)
    return ads

@api_router.put("/admin/advertisements/{ad_id}")
async def update_advertisement(ad_id: str, ad_data: dict, current_user: User = Depends(get_current_user)):
    """Atualiza um anúncio (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    # Remover campos que não devem ser atualizados
    ad_data.pop('id', None)
    ad_data.pop('created_at', None)
    
    result = await db.advertisements.update_one({'id': ad_id}, {'$set': ad_data})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    return {'message': 'Anúncio atualizado com sucesso'}

@api_router.delete("/admin/advertisements/{ad_id}")
async def delete_advertisement(ad_id: str, current_user: User = Depends(get_current_user)):
    """Exclui um anúncio (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await db.advertisements.delete_one({'id': ad_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    return {'message': 'Anúncio excluído com sucesso'}

@api_router.post("/advertisements/seed")
async def seed_advertisements():
    """Popula com anúncios iniciais de motivação e doação"""
    
    # Verificar se já existem anúncios
    existing = await db.advertisements.count_documents({})
    if existing > 0:
        return {'message': f'{existing} anúncios já existem', 'seeded': False}
    
    default_ads = [
        {
            'id': str(uuid.uuid4()),
            'type': 'motivation',
            'title': '💪 Você é mais forte do que imagina!',
            'content': 'Cada dia é uma nova oportunidade. Não desista dos seus sonhos. A jornada pode ser difícil, mas você não está sozinho.',
            'image_url': 'https://images.unsplash.com/photo-1493612276216-ee3925520721?w=400',
            'is_active': True,
            'priority': 10,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': str(uuid.uuid4()),
            'type': 'motivation',
            'title': '🙏 Deus está contigo',
            'content': '"Porque eu, o Senhor teu Deus, te tomo pela tua mão direita; e te digo: Não temas, eu te ajudo." - Isaías 41:13',
            'image_url': 'https://images.unsplash.com/photo-1507692049790-de58290a4334?w=400',
            'is_active': True,
            'priority': 9,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': str(uuid.uuid4()),
            'type': 'motivation',
            'title': '✨ Acredite em você',
            'content': 'Sua história não terminou ainda. Os melhores capítulos ainda estão por vir. Continue caminhando com fé e esperança.',
            'image_url': 'https://images.unsplash.com/photo-1499209974431-9dddcece7f88?w=400',
            'is_active': True,
            'priority': 8,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': str(uuid.uuid4()),
            'type': 'donation',
            'title': '🌍 Ajude a África - Doe Agora',
            'content': 'Milhares de famílias na África precisam de ajuda urgente. Sua doação pode salvar vidas, fornecer alimentos, água limpa e medicamentos para quem mais precisa.',
            'image_url': 'https://images.unsplash.com/photo-1509099836639-18ba1795216d?w=400',
            'link_url': 'https://www.unicef.org/appeals/africa',
            'link_text': 'Doar Agora',
            'is_active': True,
            'priority': 15,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': str(uuid.uuid4()),
            'type': 'donation',
            'title': '❤️ Seja um anjo para alguém',
            'content': 'Com apenas €5 você pode fornecer uma refeição completa para uma criança. Cada contribuição faz a diferença.',
            'image_url': 'https://images.unsplash.com/photo-1488521787991-ed7bbaae773c?w=400',
            'link_url': 'https://donate.worldvision.org',
            'link_text': 'Contribuir',
            'is_active': True,
            'priority': 14,
            'created_at': datetime.now(timezone.utc)
        },
        {
            'id': str(uuid.uuid4()),
            'type': 'motivation',
            'title': '🌟 Nunca perca a esperança',
            'content': '"Tudo posso naquele que me fortalece." - Filipenses 4:13. Você tem dentro de si a força para superar qualquer obstáculo.',
            'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400',
            'is_active': True,
            'priority': 7,
            'created_at': datetime.now(timezone.utc)
        }
    ]
    
    for ad in default_ads:
        await db.advertisements.insert_one(ad)
    
    return {'message': f'{len(default_ads)} anúncios criados com sucesso', 'seeded': True}

# ==================== JOB LISTINGS ENDPOINTS (RozgarLine Integration) ====================

async def fetch_rozgarline_jobs():
    """Busca vagas de emprego do site RozgarLine"""
    jobs = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://rozgarline.me/', timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Parse job listings from HTML usando regex
                    # Pattern para encontrar vagas
                    job_pattern = r'<a[^>]*href="(https://rozgarline\.me/jobs/[^"]+)"[^>]*>([^<]+)</a>'
                    matches = re.findall(job_pattern, html)
                    
                    seen_titles = set()
                    for url, title in matches:
                        # Limpar título
                        clean_title = title.strip()
                        if clean_title and clean_title not in seen_titles and len(clean_title) > 5:
                            # Ignorar links genéricos
                            if 'more' not in clean_title.lower() and 'author' not in url:
                                seen_titles.add(clean_title)
                                jobs.append({
                                    'id': str(uuid.uuid4()),
                                    'title': clean_title,
                                    'url': url,
                                    'source': 'RozgarLine',
                                    'location': 'Europa',
                                    'date_posted': datetime.now(timezone.utc).strftime('%d %b %Y')
                                })
                    
    except Exception as e:
        logging.error(f"Error fetching jobs from RozgarLine: {e}")
    
    return jobs[:15]  # Limitar a 15 vagas

@api_router.get("/jobs/external")
async def get_external_jobs():
    """Retorna vagas de emprego do RozgarLine"""
    # Verificar cache
    cached = await db.job_cache.find_one({'source': 'rozgarline'})
    
    # Se cache existe e tem menos de 1 hora, usar cache
    if cached and cached.get('updated_at'):
        try:
            cached_time = cached['updated_at']
            # Garantir que é aware
            if cached_time.tzinfo is None:
                cached_time = cached_time.replace(tzinfo=timezone.utc)
            cache_age = datetime.now(timezone.utc) - cached_time
            if cache_age < timedelta(hours=1):
                return {'jobs': cached.get('jobs', []), 'cached': True}
        except Exception as e:
            logging.error(f"Cache time error: {e}")
    
    # Buscar novas vagas
    jobs = await fetch_rozgarline_jobs()
    
    # Salvar no cache
    await db.job_cache.update_one(
        {'source': 'rozgarline'},
        {'$set': {
            'source': 'rozgarline',
            'jobs': jobs,
            'updated_at': datetime.now(timezone.utc)
        }},
        upsert=True
    )
    
    return {'jobs': jobs, 'cached': False}

# ==================== MURAL DE MENSAGENS ENDPOINTS ====================

class MuralMessage(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved: bool = False  # Mensagens precisam de aprovação (moderação)

class MuralMessageCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    message: str = Field(..., min_length=5, max_length=500)

@api_router.get("/mural")
async def get_mural_messages(limit: int = 20):
    """Retorna as mensagens aprovadas do mural"""
    messages = await db.mural_messages.find(
        {'approved': True}, 
        {'_id': 0}
    ).sort('created_at', -1).to_list(limit)
    
    return {'messages': messages, 'total': len(messages)}

@api_router.post("/mural")
async def create_mural_message(msg_data: MuralMessageCreate):
    """Cria uma nova mensagem no mural (precisa de aprovação)"""
    message = MuralMessage(
        name=msg_data.name,
        message=msg_data.message,
        approved=True  # Por enquanto aprovamos automaticamente
    )
    
    msg_dict = message.model_dump()
    msg_dict['created_at'] = msg_dict['created_at'].isoformat()
    
    await db.mural_messages.insert_one(msg_dict)
    return {'message': 'Mensagem enviada com sucesso!', 'id': message.id}

@api_router.get("/admin/mural")
async def admin_get_mural_messages(current_user: User = Depends(get_current_user)):
    """Lista todas as mensagens do mural (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    messages = await db.mural_messages.find({}, {'_id': 0}).sort('created_at', -1).to_list(100)
    return messages

@api_router.put("/admin/mural/{msg_id}/approve")
async def approve_mural_message(msg_id: str, current_user: User = Depends(get_current_user)):
    """Aprova uma mensagem do mural"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await db.mural_messages.update_one({'id': msg_id}, {'$set': {'approved': True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    return {'message': 'Mensagem aprovada'}

@api_router.delete("/admin/mural/{msg_id}")
async def delete_mural_message(msg_id: str, current_user: User = Depends(get_current_user)):
    """Exclui uma mensagem do mural"""
    if current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin only")
    
    result = await db.mural_messages.delete_one({'id': msg_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mensagem não encontrada")
    
    return {'message': 'Mensagem excluída'}

# ==================== JSEARCH API - BUSCA DE EMPREGOS ====================

RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
JSEARCH_BASE_URL = "https://jsearch.p.rapidapi.com"

class JobSearchQuery(BaseModel):
    query: str = Field(default="", description="Termo de busca (ex: garçom, eletricista)")
    location: str = Field(default="France", description="Localização")
    page: int = Field(default=1, description="Página de resultados")
    num_pages: int = Field(default=1, description="Número de páginas")
    date_posted: str = Field(default="all", description="Filtro de data: all, today, 3days, week, month")
    remote_jobs_only: bool = Field(default=False, description="Apenas trabalhos remotos")
    employment_types: Optional[str] = Field(default=None, description="FULLTIME, PARTTIME, CONTRACTOR, INTERN")

JOB_REGIONS = {
    'br': {'label': 'Brasil', 'country': 'br', 'geo': 'brazil', 'lang': 'pt'},
    'pt': {'label': 'Portugal', 'country': 'pt', 'geo': 'portugal', 'lang': 'pt'},
    'fr': {'label': 'França', 'country': 'fr', 'geo': 'france', 'lang': 'fr'},
    'be': {'label': 'Bélgica', 'country': 'be', 'geo': 'belgium', 'lang': 'fr'},
    'ch': {'label': 'Suíça', 'country': 'ch', 'geo': 'switzerland', 'lang': 'fr'},
    'es': {'label': 'Espanha', 'country': 'es', 'geo': 'spain', 'lang': 'es'},
    'it': {'label': 'Itália', 'country': 'it', 'geo': 'italy', 'lang': 'it'},
    'de': {'label': 'Alemanha', 'country': 'de', 'geo': 'germany', 'lang': 'de'},
    'gb': {'label': 'Reino Unido', 'country': 'gb', 'geo': 'uk', 'lang': 'en'},
    'us': {'label': 'Estados Unidos', 'country': 'us', 'geo': 'usa', 'lang': 'en'},
    'ca': {'label': 'Canadá', 'country': 'ca', 'geo': 'canada', 'lang': 'en'},
    'latam': {'label': 'América Latina', 'country': 'mx', 'geo': 'latam', 'lang': 'es'},
    'remote': {'label': 'Remoto (mundo)', 'country': 'us', 'geo': None, 'lang': 'en'},
}

GENERIC_JOB_TERMS = {'', 'emprego', 'empregos', 'vaga', 'vagas', 'trabalho', 'emploi', 'job', 'jobs', 'work', 'empleo', 'lavoro', 'arbeit'}

PT_EN_TERMS = {
    'garçom': 'waiter', 'garcom': 'waiter', 'cozinheiro': 'cook', 'limpeza': 'cleaning', 'faxineira': 'cleaner',
    'motorista': 'driver', 'entregador': 'delivery', 'eletricista': 'electrician', 'pedreiro': 'construction',
    'pintor': 'painter', 'encanador': 'plumber', 'babá': 'nanny', 'cuidador': 'caregiver', 'enfermeiro': 'nurse',
    'professor': 'teacher', 'desenvolvedor': 'developer', 'programador': 'developer', 'vendedor': 'sales',
    'vendas': 'sales', 'atendente': 'customer service', 'suporte': 'support', 'designer': 'designer',
    'marketing': 'marketing', 'contador': 'accountant', 'logística': 'logistics', 'logistica': 'logistics',
    'recepcionista': 'receptionist', 'secretária': 'assistant', 'analista': 'analyst', 'tradutor': 'translator',
}

def _strip_html(text: str) -> str:
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text or '')).strip()

def _to_english(query: str) -> str:
    q = query.lower().strip()
    for pt, en in PT_EN_TERMS.items():
        if pt in q:
            return en
    return q

def _matches(job: dict, terms: List[str]) -> bool:
    if not terms:
        return True
    hay = f"{job.get('title', '')} {job.get('description', '')[:400]}".lower()
    return any(t in hay for t in terms)

async def _fetch_json(session, url, params=None, headers=None):
    async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as r:
        if r.status != 200:
            raise RuntimeError(f"{url} -> HTTP {r.status}")
        return await r.json(content_type=None)

async def _jsearch(session, query, location, region, page, date_posted, remote_only, employment_type):
    params = {"query": f"{query} in {location or region['label']}", "page": str(page), "num_pages": "1",
              "date_posted": date_posted, "country": region['country']}
    if remote_only:
        params["remote_jobs_only"] = "true"
    if employment_type:
        params["employment_types"] = employment_type
    data = await _fetch_json(session, f"{JSEARCH_BASE_URL}/search", params,
                             {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"})
    return [{
        'id': job.get('job_id') or str(uuid.uuid4()),
        'title': job.get('job_title') or 'Vaga sem título',
        'company': job.get('employer_name') or 'Empresa não informada',
        'company_logo': job.get('employer_logo'),
        'location': ', '.join(x for x in [job.get('job_city'), job.get('job_country')] if x) or region['label'],
        'description': (job.get('job_description') or '')[:1500],
        'employment_type': job.get('job_employment_type') or '',
        'date_posted': job.get('job_posted_at_datetime_utc') or '',
        'url': job.get('job_apply_link') or job.get('job_google_link') or '',
        'source': job.get('job_publisher') or 'JSearch',
        'salary_min': job.get('job_min_salary'), 'salary_max': job.get('job_max_salary'),
        'salary_currency': job.get('job_salary_currency'), 'is_remote': job.get('job_is_remote', False),
    } for job in data.get('data', [])]

async def _jobicy(session, terms, region):
    params = {'count': 50}
    if region['geo']:
        params['geo'] = region['geo']
    if terms:
        params['tag'] = terms[0]
    data = await _fetch_json(session, 'https://jobicy.com/api/v2/remote-jobs', params)
    jobs = [{
        'id': f"jobicy-{j.get('id')}", 'title': j.get('jobTitle', ''), 'company': j.get('companyName', ''),
        'company_logo': j.get('companyLogo'), 'location': f"Remoto · {j.get('jobGeo', 'Mundo')}",
        'description': _strip_html(j.get('jobDescription') or j.get('jobExcerpt', ''))[:1500],
        'employment_type': ', '.join(j.get('jobType') or []), 'date_posted': j.get('pubDate', ''),
        'url': j.get('url', ''), 'source': 'Jobicy', 'salary_min': j.get('salaryMin'), 'salary_max': j.get('salaryMax'),
        'salary_currency': j.get('salaryCurrency'), 'is_remote': True,
    } for j in data.get('jobs', [])]
    return [j for j in jobs if _matches(j, terms)]

async def _remotive(session, terms):
    params = {'limit': 50}
    if terms:
        params['search'] = terms[0]
    data = await _fetch_json(session, 'https://remotive.com/api/remote-jobs', params)
    return [{
        'id': f"remotive-{j.get('id')}", 'title': j.get('title', ''), 'company': j.get('company_name', ''),
        'company_logo': j.get('company_logo'), 'location': f"Remoto · {j.get('candidate_required_location') or 'Mundo'}",
        'description': _strip_html(j.get('description', ''))[:1500], 'employment_type': (j.get('job_type') or '').replace('_', ' '),
        'date_posted': j.get('publication_date', ''), 'url': j.get('url', ''), 'source': 'Remotive',
        'salary_min': None, 'salary_max': None, 'salary_currency': None, 'is_remote': True,
    } for j in data.get('jobs', [])]

async def _arbeitnow(session, terms):
    data = await _fetch_json(session, 'https://www.arbeitnow.com/api/job-board-api')
    jobs = [{
        'id': f"arbeitnow-{j.get('slug')}", 'title': j.get('title', ''), 'company': j.get('company_name', ''),
        'company_logo': None, 'location': f"{j.get('location', '')}, Alemanha",
        'description': _strip_html(j.get('description', ''))[:1500], 'employment_type': ', '.join(j.get('job_types') or []),
        'date_posted': datetime.fromtimestamp(j['created_at'], timezone.utc).isoformat() if j.get('created_at') else '',
        'url': j.get('url', ''), 'source': 'Arbeitnow', 'salary_min': None, 'salary_max': None,
        'salary_currency': None, 'is_remote': bool(j.get('remote')),
    } for j in data.get('data', [])]
    return [j for j in jobs if _matches(j, terms)]

@api_router.get("/jobs/regions")
async def get_job_regions():
    return [{'value': k, 'label': v['label']} for k, v in JOB_REGIONS.items()]

@api_router.get("/jobs/search")
async def search_jobs(
    query: str = "emprego",
    location: str = "",
    region: str = "br",
    page: int = 1,
    date_posted: str = "all",
    remote_only: bool = False,
    employment_type: Optional[str] = None
):
    """Busca vagas: JSearch (Indeed/LinkedIn, se RAPIDAPI_KEY) + fontes gratuitas (Jobicy, Remotive, Arbeitnow)."""
    reg = JOB_REGIONS.get(region, JOB_REGIONS['br'])
    q = (query or '').strip()
    loc = (location or '').strip()
    if loc.lower() == reg['label'].lower():
        loc = ''
    cache_key = f"jobs2_{q.lower()}_{loc.lower()}_{region}_{page}_{date_posted}_{remote_only}_{employment_type}"
    cached = await db.job_cache.find_one({'cache_key': cache_key}, {'_id': 0})
    if cached:
        expires_at = cached.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at and expires_at > datetime.now(timezone.utc):
            return {'jobs': cached['jobs'], 'total': len(cached['jobs']), 'page': page, 'region': region,
                    'sources': cached.get('sources', []), 'cached': True}

    en_terms = [] if q.lower() in GENERIC_JOB_TERMS else [_to_english(q)]
    jobs: List[dict] = []
    sources: List[str] = []
    async with aiohttp.ClientSession() as session:
        if RAPIDAPI_KEY:
            try:
                local = await _jsearch(session, q or 'jobs', loc, reg, page, date_posted, remote_only, employment_type)
                jobs += local
                sources.append('JSearch')
            except Exception as e:
                logging.error(f"JSearch error: {e}")
        if page == 1:
            tasks = [_jobicy(session, en_terms, reg), _remotive(session, en_terms)]
            names = ['Jobicy', 'Remotive']
            if region in ('de', 'remote'):
                tasks.append(_arbeitnow(session, en_terms))
                names.append('Arbeitnow')
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for name, res in zip(names, results):
                if isinstance(res, Exception):
                    logging.error(f"{name} error: {res}")
                    continue
                jobs += res
                sources.append(name)

    seen, unique = set(), []
    for j in jobs:
        key = (j['title'].lower().strip(), (j['company'] or '').lower().strip())
        if j['title'] and j['url'] and key not in seen:
            seen.add(key)
            unique.append(j)
    unique = unique[:60]

    if sources:
        await db.job_cache.update_one({'cache_key': cache_key}, {'$set': {
            'cache_key': cache_key, 'jobs': unique, 'sources': sources,
            'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)}}, upsert=True)
    return {'jobs': unique, 'total': len(unique), 'page': page, 'region': region, 'sources': sources,
            'local_search': bool(RAPIDAPI_KEY), 'cached': False}

@api_router.get("/jobs/details/{job_id}")
async def get_job_details(job_id: str):
    """Obtém detalhes de uma vaga específica"""
    
    if not RAPIDAPI_KEY:
        raise HTTPException(status_code=503, detail="Busca de vagas indisponível: configure RAPIDAPI_KEY")
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    params = {"job_id": job_id}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{JSEARCH_BASE_URL}/job-details",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail="Erro ao buscar detalhes")
                
                data = await response.json()
                
                if not data.get('data'):
                    raise HTTPException(status_code=404, detail="Vaga não encontrada")
                
                job = data['data'][0]
                
                return {
                    'id': job.get('job_id'),
                    'title': job.get('job_title'),
                    'company': job.get('employer_name'),
                    'company_logo': job.get('employer_logo'),
                    'company_website': job.get('employer_website'),
                    'location': f"{job.get('job_city', '')}, {job.get('job_country', '')}",
                    'description': job.get('job_description', ''),
                    'employment_type': job.get('job_employment_type'),
                    'date_posted': job.get('job_posted_at_datetime_utc'),
                    'url': job.get('job_apply_link', job.get('job_google_link', '')),
                    'source': job.get('job_publisher'),
                    'salary_min': job.get('job_min_salary'),
                    'salary_max': job.get('job_max_salary'),
                    'salary_currency': job.get('job_salary_currency'),
                    'is_remote': job.get('job_is_remote', False),
                    'qualifications': job.get('job_required_skills', []),
                    'benefits': job.get('job_benefits', []),
                    'experience_required': job.get('job_required_experience', {}),
                    'education_required': job.get('job_required_education', {})
                }
                
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=503, detail=f"Erro de conexão: {str(e)}")

@api_router.get("/jobs/suggested")
async def get_suggested_jobs(category: str = "all"):
    """Retorna vagas sugeridas por categoria"""
    
    # Mapeamento de categorias para termos de busca
    category_queries = {
        'bricolage': 'electrician plumber handyman France',
        'cleaning': 'cleaning housekeeping France',
        'transport': 'driver delivery chauffeur France',
        'food': 'restaurant cook chef waiter France',
        'care': 'caregiver nurse aide soignant France',
        'education': 'teacher tutor professor France',
        'tech': 'developer IT technician France',
        'childcare': 'babysitter nanny childcare France',
        'garden': 'gardener landscaper France',
        'moving': 'mover warehouse logistics France',
        'all': 'jobs France'
    }
    
    query = category_queries.get(category, category_queries['all'])
    
    return await search_jobs(query=query, location="France", page=1, date_posted="week")

@api_router.get("/sidebar-content")
async def get_sidebar_content():
    """Retorna todo o conteúdo da sidebar: anúncios + vagas de emprego"""
    
    # Buscar anúncios ativos
    ads = await db.advertisements.find({'is_active': True}, {'_id': 0}).sort('priority', -1).to_list(10)
    
    # Buscar vagas de emprego (do cache ou externo)
    jobs_data = await get_external_jobs()
    jobs = jobs_data.get('jobs', [])
    
    # Intercalar conteúdo: motivação, vaga, doação, vaga, motivação...
    sidebar_items = []
    
    motivation_ads = [a for a in ads if a.get('type') == 'motivation']
    donation_ads = [a for a in ads if a.get('type') == 'donation']
    
    # Adicionar 2 motivações primeiro
    for ad in motivation_ads[:2]:
        sidebar_items.append({**ad, 'item_type': 'advertisement'})
    
    # Adicionar 3 vagas de emprego
    for job in jobs[:3]:
        sidebar_items.append({
            'id': job.get('id', ''),
            'item_type': 'job',
            'type': 'job',
            'title': f"💼 {job.get('title', 'Vaga')}",
            'content': f"📍 {job.get('location', 'Europa')} • {job.get('date_posted', 'Recente')}",
            'link_url': job.get('url', ''),
            'link_text': 'Ver Vaga',
            'image_url': 'https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=400',
            'source': job.get('source', 'JSearch')
        })
    
    # Adicionar doações
    for ad in donation_ads[:2]:
        sidebar_items.append({**ad, 'item_type': 'advertisement'})
    
    # Adicionar mais vagas
    for job in jobs[3:6]:
        sidebar_items.append({
            'id': job.get('id', ''),
            'item_type': 'job',
            'type': 'job',
            'title': f"💼 {job.get('title', 'Vaga')}",
            'content': f"📍 {job.get('location', 'Europa')} • {job.get('date_posted', 'Recente')}",
            'link_url': job.get('url', ''),
            'link_text': 'Ver Vaga',
            'image_url': 'https://images.unsplash.com/photo-1521791136064-7986c2920216?w=400',
            'source': job.get('source', 'JSearch')
        })
    
    # Adicionar mais motivações
    for ad in motivation_ads[2:]:
        sidebar_items.append({**ad, 'item_type': 'advertisement'})
    
    # Adicionar resto das vagas
    for job in jobs[6:]:
        sidebar_items.append({
            'id': job.get('id', ''),
            'item_type': 'job',
            'type': 'job',
            'title': f"💼 {job.get('title', 'Vaga')}",
            'content': f"📍 {job.get('location', 'Europa')} • {job.get('date_posted', 'Recente')}",
            'link_url': job.get('url', ''),
            'link_text': 'Candidatar',
            'image_url': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400',
            'source': job.get('source', 'JSearch')
        })
    
    return {
        'items': sidebar_items,
        'total_ads': len(ads),
        'total_jobs': len(jobs)
    }

# ==================== INTEGRAÇÃO: VAGAS NO MAPA E FEED ====================

@api_router.post("/jobs/sync-to-map")
async def sync_jobs_to_map(current_user: User = Depends(get_current_user)):
    """Sincroniza vagas de emprego com o mapa de oportunidades"""
    
    # Buscar vagas do cache
    jobs_data = await search_jobs(query="emploi", location="France", page=1)
    jobs = jobs_data.get('jobs', [])
    
    synced_count = 0
    for job in jobs[:20]:  # Limitar a 20 vagas
        # Verificar se já existe
        existing = await db.job_map_locations.find_one({'job_id': job.get('id')})
        if existing:
            continue
        
        # Extrair cidade da localização
        location_str = job.get('location') or 'Paris'
        
        # Coordenadas aproximadas para principais cidades da França
        city_coords = {
            'paris': {'lat': 48.8566, 'lng': 2.3522},
            'lyon': {'lat': 45.7640, 'lng': 4.8357},
            'marseille': {'lat': 43.2965, 'lng': 5.3698},
            'toulouse': {'lat': 43.6047, 'lng': 1.4442},
            'nice': {'lat': 43.7102, 'lng': 7.2620},
            'nantes': {'lat': 47.2184, 'lng': -1.5536},
            'bordeaux': {'lat': 44.8378, 'lng': -0.5792},
            'lille': {'lat': 50.6292, 'lng': 3.0573},
            'strasbourg': {'lat': 48.5734, 'lng': 7.7521},
            'rennes': {'lat': 48.1173, 'lng': -1.6778}
        }
        
        # Encontrar coordenadas
        coords = city_coords.get('paris')  # Default para Paris
        for city, coord in city_coords.items():
            if city in location_str.lower():
                coords = coord
                break
        
        # Adicionar pequena variação para não sobrepor marcadores
        lat_offset = random.uniform(-0.02, 0.02)
        lng_offset = random.uniform(-0.02, 0.02)
        
        job_location = {
            'id': str(uuid.uuid4()),
            'job_id': job.get('id'),
            'name': job.get('title', 'Vaga de Emprego'),
            'company': job.get('company', 'Empresa'),
            'address': location_str,
            'category': 'work',
            'lat': coords['lat'] + lat_offset,
            'lng': coords['lng'] + lng_offset,
            'url': job.get('url', ''),
            'salary_min': job.get('salary_min'),
            'salary_max': job.get('salary_max'),
            'employment_type': job.get('employment_type'),
            'is_remote': job.get('is_remote', False),
            'source': job.get('source', 'JSearch'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.job_map_locations.insert_one(job_location)
        synced_count += 1
    
    return {'message': f'{synced_count} vagas sincronizadas com o mapa', 'count': synced_count}

@api_router.get("/jobs/map-locations")
async def get_job_map_locations(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius: float = 50.0
):
    """Retorna vagas de emprego para exibir no mapa"""
    
    # Buscar vagas salvas no mapa
    job_locations = await db.job_map_locations.find({}, {'_id': 0}).to_list(100)
    
    # Se coordenadas fornecidas, calcular distância
    if lat is not None and lng is not None:
        for job in job_locations:
            if job.get('lat') and job.get('lng'):
                job['distance'] = round(calculate_distance(lat, lng, job['lat'], job['lng']), 2)
        
        # Filtrar por raio
        job_locations = [j for j in job_locations if j.get('distance', 0) <= radius]
        
        # Ordenar por distância
        job_locations.sort(key=lambda x: x.get('distance', float('inf')))
    
    return {'locations': job_locations, 'total': len(job_locations)}

@api_router.post("/jobs/auto-post")
async def auto_post_jobs(limit: int = 5):
    """Cria posts automáticos de vagas de emprego no feed"""
    
    # Buscar vagas do cache
    jobs_data = await search_jobs(query="emploi", location="France", page=1)
    jobs = jobs_data.get('jobs', [])
    
    posted_count = 0
    for job in jobs[:limit]:
        # Verificar se já foi postado
        existing = await db.posts.find_one({'job_id': job.get('id')})
        if existing:
            continue
        
        # Criar post da vaga
        post_dict = {
            'id': str(uuid.uuid4()),
            'user_id': 'system',
            'type': 'job',
            'category': 'work',
            'categories': ['work'],
            'title': f"💼 {job.get('title', 'Vaga de Emprego')}",
            'description': f"""🏢 **{job.get('company', 'Empresa')}**
📍 {job.get('location', 'França')}
{f"💰 {job.get('salary_min')}-{job.get('salary_max')} {job.get('salary_currency', 'EUR')}" if job.get('salary_min') else ""}
{"🏠 Trabalho Remoto" if job.get('is_remote') else ""}

{job.get('description', '')[:300]}...

🔗 Candidate-se: {job.get('url', '')}""",
            'location': None,
            'images': [job.get('company_logo')] if job.get('company_logo') else [],
            'job_id': job.get('id'),
            'job_url': job.get('url'),
            'job_company': job.get('company'),
            'job_salary_min': job.get('salary_min'),
            'job_salary_max': job.get('salary_max'),
            'is_job_post': True,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.posts.insert_one(post_dict)
        posted_count += 1
    
    return {'message': f'{posted_count} vagas postadas no feed', 'count': posted_count}

@api_router.delete("/jobs/cache")
async def clear_jobs_cache():
    """Limpa o cache de vagas para forçar atualização"""
    result = await db.job_cache.delete_many({})
    result2 = await db.job_map_locations.delete_many({})
    return {'message': f'Cache limpo: {result.deleted_count} itens removidos', 'map_locations_removed': result2.deleted_count}

# ==================== PREFERÊNCIAS DE EMPREGO DO USUÁRIO ====================

class JobPreferences(BaseModel):
    search_query: str
    search_location: str = "França"
    availability: Optional[str] = None
    experience: Optional[str] = None

@api_router.post("/user/job-preferences")
async def save_job_preferences(prefs: JobPreferences, current_user: User = Depends(get_current_user)):
    """Salva as preferências de emprego do usuário para receber vagas personalizadas"""
    
    job_prefs = {
        'user_id': current_user.id,
        'search_query': prefs.search_query,
        'search_location': prefs.search_location,
        'availability': prefs.availability,
        'experience': prefs.experience,
        'is_active': True,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Atualizar ou criar preferências
    await db.job_preferences.update_one(
        {'user_id': current_user.id},
        {'$set': job_prefs},
        upsert=True
    )
    
    return {'message': 'Preferências salvas! Você receberá vagas personalizadas.', 'preferences': job_prefs}

@api_router.get("/user/job-preferences")
async def get_job_preferences(current_user: User = Depends(get_current_user)):
    """Retorna as preferências de emprego do usuário"""
    prefs = await db.job_preferences.find_one({'user_id': current_user.id}, {'_id': 0})
    return prefs or {'is_active': False}

@api_router.delete("/user/job-preferences")
async def delete_job_preferences(current_user: User = Depends(get_current_user)):
    """Desativa as preferências de emprego do usuário"""
    await db.job_preferences.update_one(
        {'user_id': current_user.id},
        {'$set': {'is_active': False, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    return {'message': 'Alertas de vagas desativados'}

@api_router.get("/user/personalized-jobs")
async def get_personalized_jobs(current_user: User = Depends(get_current_user)):
    """Retorna vagas personalizadas baseadas nas preferências do usuário"""
    
    # Buscar preferências do usuário
    prefs = await db.job_preferences.find_one({'user_id': current_user.id, 'is_active': True})
    
    if not prefs:
        return {'jobs': [], 'message': 'Nenhuma preferência de emprego configurada'}
    
    # Mapeamento português → francês
    translations = {
        'garçom': 'serveur', 'garcom': 'serveur', 'cozinheiro': 'cuisinier',
        'limpeza': 'nettoyage', 'motorista': 'chauffeur', 'construção': 'construction',
        'vendedor': 'vendeur', 'caixa': 'caissier', 'entregador': 'livreur',
        'pedreiro': 'maçon', 'eletricista': 'électricien', 'jardineiro': 'jardinier',
        'babá': 'nounou', 'cuidador': 'aide-soignant', 'segurança': 'agent de sécurité',
        'recepcionista': 'réceptionniste', 'auxiliar': 'assistant', 'operador': 'opérateur',
        'mecânico': 'mécanicien', 'padeiro': 'boulanger', 'carpinteiro': 'charpentier',
        'soldador': 'soudeur', 'técnico': 'technicien', 'enfermeiro': 'infirmier',
        'secretária': 'secrétaire', 'contador': 'comptable'
    }
    
    # Traduzir termo de busca
    query = prefs.get('search_query', '').lower()
    translated_query = translations.get(query, query)
    location = prefs.get('search_location', 'France')
    
    # Buscar vagas
    jobs_data = await search_jobs(query=translated_query, location=location, page=1)
    jobs = jobs_data.get('jobs', [])
    
    # Formatar vagas para o feed
    personalized_jobs = []
    for job in jobs[:10]:  # Limitar a 10 vagas
        personalized_jobs.append({
            'id': job.get('id', str(uuid.uuid4())),
            'type': 'personalized_job',
            'title': job.get('title', 'Vaga de Emprego'),
            'company': job.get('company', 'Empresa'),
            'location': job.get('location', location),
            'url': job.get('url', ''),
            'company_logo': job.get('company_logo'),
            'salary_min': job.get('salary_min'),
            'salary_max': job.get('salary_max'),
            'salary_currency': job.get('salary_currency', 'EUR'),
            'is_remote': job.get('is_remote', False),
            'date_posted': job.get('date_posted', 'Recente'),
            'source': job.get('source', 'JSearch'),
            'search_query': prefs.get('search_query'),
            'is_personalized': True
        })
    
    return {
        'jobs': personalized_jobs,
        'total': len(personalized_jobs),
        'preferences': {
            'query': prefs.get('search_query'),
            'location': prefs.get('search_location')
        }
    }

# ==================== HOUSING ENDPOINTS ====================

@api_router.get("/housing")
async def get_housing_listings(
    type: Optional[str] = None,
    city: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Lista anúncios de hospedagem com filtros opcionais"""
    query = {'listing_status': 'active'}
    
    if type and type != 'all':
        query['listing_type'] = type
    
    if city:
        query['city'] = {'$regex': city, '$options': 'i'}
    
    listings = await db.housing_listings.find(query, {'_id': 0}).sort('created_at', -1).to_list(100)
    
    # Adicionar info do usuário a cada listing
    for listing in listings:
        user = await db.users.find_one({'id': listing['user_id']}, {'_id': 0, 'password': 0})
        if user:
            listing['user'] = {
                'id': user.get('id'),
                'name': user.get('name'),
                'verified': user.get('verified', False),
                'rating': user.get('rating', 4.5),
                'reviews_count': user.get('reviews_count', 0)
            }
    
    return listings

@api_router.post("/housing")
async def create_housing_listing(
    listing_data: HousingListingCreate,
    current_user: User = Depends(get_current_user)
):
    """Cria um novo anúncio de hospedagem"""
    listing = HousingListing(
        user_id=current_user.id,
        listing_type=listing_data.listing_type,
        title=listing_data.title,
        description=listing_data.description,
        city=listing_data.city,
        address=listing_data.address,
        accommodation_type=listing_data.accommodation_type,
        duration=listing_data.duration,
        max_guests=listing_data.max_guests,
        amenities=listing_data.amenities,
        pets_allowed=listing_data.pets_allowed,
        available_from=listing_data.available_from,
        available_until=listing_data.available_until,
        exchange_services=listing_data.exchange_services,
        photos=listing_data.photos
    )
    
    await db.housing_listings.insert_one(listing.model_dump())
    
    return {'message': 'Anúncio criado com sucesso', 'id': listing.id}

@api_router.get("/housing/{listing_id}")
async def get_housing_listing(
    listing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Retorna detalhes de um anúncio específico"""
    listing = await db.housing_listings.find_one({'id': listing_id}, {'_id': 0})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    # Adicionar info do usuário
    user = await db.users.find_one({'id': listing['user_id']}, {'_id': 0, 'password': 0})
    if user:
        listing['user'] = {
            'id': user.get('id'),
            'name': user.get('name'),
            'email': user.get('email'),
            'phone': user.get('phone'),
            'verified': user.get('verified', False),
            'rating': user.get('rating', 4.5),
            'reviews_count': user.get('reviews_count', 0)
        }
    
    return listing

@api_router.put("/housing/{listing_id}")
async def update_housing_listing(
    listing_id: str,
    listing_data: HousingListingCreate,
    current_user: User = Depends(get_current_user)
):
    """Atualiza um anúncio de hospedagem"""
    listing = await db.housing_listings.find_one({'id': listing_id})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    if listing['user_id'] != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Sem permissão para editar este anúncio")
    
    update_data = listing_data.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.housing_listings.update_one(
        {'id': listing_id},
        {'$set': update_data}
    )
    
    return {'message': 'Anúncio atualizado com sucesso'}

@api_router.delete("/housing/{listing_id}")
async def delete_housing_listing(
    listing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove um anúncio de hospedagem"""
    listing = await db.housing_listings.find_one({'id': listing_id})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    if listing['user_id'] != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Sem permissão para remover este anúncio")
    
    await db.housing_listings.delete_one({'id': listing_id})
    
    return {'message': 'Anúncio removido com sucesso'}

@api_router.put("/housing/{listing_id}/status")
async def update_housing_status(
    listing_id: str,
    new_status: str,
    current_user: User = Depends(get_current_user)
):
    """Atualiza o status de um anúncio (active, matched, closed)"""
    listing = await db.housing_listings.find_one({'id': listing_id})
    
    if not listing:
        raise HTTPException(status_code=404, detail="Anúncio não encontrado")
    
    if listing['user_id'] != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Sem permissão para alterar este anúncio")
    
    await db.housing_listings.update_one(
        {'id': listing_id},
        {'$set': {'listing_status': new_status, 'updated_at': datetime.now(timezone.utc).isoformat()}}
    )
    
    return {'message': f'Status atualizado para {new_status}'}

# ==================== PASSWORD RESET ====================

class ForgotPasswordIn(BaseModel):
    email: str

class ResetPasswordIn(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=128)

@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordIn):
    user = await db.users.find_one({'email': email_query(data.email)}, {'_id': 0, 'id': 1, 'name': 1, 'email': 1})
    generic = {'message': 'Se o e-mail estiver cadastrado, enviamos um código de recuperação.'}
    if not user:
        return generic
    recent = await db.password_resets.find_one({'user_id': user['id']}, {'_id': 0, 'created_at': 1})
    if recent and datetime.fromisoformat(recent['created_at']) > datetime.now(timezone.utc) - timedelta(seconds=60):
        raise HTTPException(status_code=429, detail='Aguarde 1 minuto antes de pedir um novo código')
    code = f"{random.SystemRandom().randint(0, 999999):06d}"
    subject, html = reset_code_email(user['name'], code)
    await send_email(to=user['email'], subject=subject, html=html)
    now = datetime.now(timezone.utc)
    await db.password_resets.update_one({'user_id': user['id']}, {'$set': {
        'user_id': user['id'],
        'code_hash': bcrypt.hashpw(code.encode(), bcrypt.gensalt()).decode(),
        'attempts': 0,
        'created_at': now.isoformat(),
        'expires_at': (now + timedelta(minutes=15)).isoformat()
    }}, upsert=True)
    return generic

@api_router.post("/auth/reset-password")
async def reset_password(data: ResetPasswordIn):
    invalid = HTTPException(status_code=400, detail='Código inválido ou expirado')
    user = await db.users.find_one({'email': email_query(data.email)}, {'_id': 0, 'id': 1})
    if not user:
        raise invalid
    reset = await db.password_resets.find_one({'user_id': user['id']}, {'_id': 0})
    if not reset or datetime.fromisoformat(reset['expires_at']) < datetime.now(timezone.utc) or reset.get('attempts', 0) >= 5:
        raise invalid
    if not bcrypt.checkpw(data.code.encode(), reset['code_hash'].encode()):
        await db.password_resets.update_one({'user_id': user['id']}, {'$inc': {'attempts': 1}})
        raise invalid
    hashed = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    await db.users.update_one({'id': user['id']}, {'$set': {'password': hashed}})
    await db.password_resets.delete_one({'user_id': user['id']})
    return {'message': 'Senha redefinida com sucesso'}

# ==================== APPOINTMENTS (CHAT) ====================

APPOINTMENT_MODES = {'in_person': 'Presencial', 'video': 'Chamada de vídeo', 'phone': 'Telefone', 'other': 'Outro'}

class AppointmentCreate(BaseModel):
    to_user_id: str
    date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: str = Field(pattern=r'^\d{2}:\d{2}$')
    mode: str
    info: Optional[str] = Field(default='', max_length=500)
    acknowledged: bool

class AppointmentRespond(BaseModel):
    action: str

@api_router.post("/appointments")
async def create_appointment(data: AppointmentCreate, current_user: User = Depends(get_current_user)):
    if data.mode not in APPOINTMENT_MODES:
        raise HTTPException(status_code=400, detail='Modo inválido')
    if not data.acknowledged:
        raise HTTPException(status_code=400, detail='Confirme que entendeu as condições')
    if data.to_user_id == current_user.id or not await db.users.find_one({'id': data.to_user_id}, {'_id': 1}):
        raise HTTPException(status_code=404, detail='Usuário não encontrado')
    try:
        when = datetime.fromisoformat(f"{data.date}T{data.time}")
    except ValueError:
        raise HTTPException(status_code=400, detail='Data ou hora inválida')
    if when.date() < datetime.now(timezone.utc).date():
        raise HTTPException(status_code=400, detail='A data não pode estar no passado')
    msg = {
        'id': str(uuid.uuid4()),
        'from_user_id': current_user.id,
        'to_user_id': data.to_user_id,
        'message': f"Proposta de agendamento: {when.strftime('%d/%m/%Y')} às {data.time} ({APPOINTMENT_MODES[data.mode]})",
        'created_at': datetime.now(timezone.utc).isoformat(),
        'media': [],
        'appointment': {
            'date': data.date, 'time': data.time, 'mode': data.mode,
            'info': (data.info or '').strip(), 'status': 'pending'
        }
    }
    await db.messages.insert_one(msg)
    msg.pop('_id', None)
    return msg

@api_router.put("/appointments/{message_id}/respond")
async def respond_appointment(message_id: str, data: AppointmentRespond, current_user: User = Depends(get_current_user)):
    msg = await db.messages.find_one({'id': message_id, 'appointment': {'$exists': True}}, {'_id': 0})
    if not msg or current_user.id not in (msg['from_user_id'], msg['to_user_id']):
        raise HTTPException(status_code=404, detail='Agendamento não encontrado')
    if msg['appointment']['status'] != 'pending':
        raise HTTPException(status_code=400, detail='Este agendamento já foi respondido')
    is_recipient = msg['to_user_id'] == current_user.id
    allowed = {'accept': 'accepted', 'decline': 'declined'} if is_recipient else {'cancel': 'cancelled'}
    if data.action not in allowed:
        raise HTTPException(status_code=403, detail='Ação não permitida')
    status_value = allowed[data.action]
    await db.messages.update_one({'id': message_id}, {'$set': {'appointment.status': status_value}})
    appt = msg['appointment']
    label = {'accepted': 'aceitou', 'declined': 'recusou', 'cancelled': 'cancelou'}[status_value]
    when = datetime.fromisoformat(appt['date']).strftime('%d/%m/%Y')
    other_id = msg['from_user_id'] if is_recipient else msg['to_user_id']
    await db.messages.insert_one({
        'id': str(uuid.uuid4()),
        'from_user_id': current_user.id,
        'to_user_id': other_id,
        'message': f"{current_user.name} {label} o agendamento de {when} às {appt['time']}.",
        'created_at': datetime.now(timezone.utc).isoformat(),
        'media': [],
        'appointment_update': {'ref_id': message_id, 'status': status_value}
    })
    return {'id': message_id, 'status': status_value}

# ==================== POST VIDEOS ====================

VIDEO_MAX_BYTES = 50 * 1024 * 1024
video_bucket = AsyncIOMotorGridFSBucket(db, bucket_name='post_videos')

@api_router.post("/posts/{post_id}/video")
async def upload_post_video(post_id: str, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    post = await db.posts.find_one({'id': post_id, 'user_id': current_user.id}, {'_id': 0, 'id': 1, 'video_file_id': 1})
    if not post:
        raise HTTPException(status_code=404, detail='Post não encontrado')
    ext = (file.filename or '').rsplit('.', 1)[-1].lower()
    video_exts = {'mp4': 'video/mp4', 'mov': 'video/quicktime', 'webm': 'video/webm', '3gp': 'video/3gpp', 'mkv': 'video/x-matroska', 'm4v': 'video/mp4'}
    mime = file.content_type if (file.content_type or '').startswith('video/') else video_exts.get(ext)
    if not mime:
        raise HTTPException(status_code=400, detail='Envie um arquivo de vídeo')
    data = await file.read(VIDEO_MAX_BYTES + 1)
    if len(data) > VIDEO_MAX_BYTES:
        raise HTTPException(status_code=413, detail='Vídeo muito grande (máximo 50MB)')
    if post.get('video_file_id'):
        try:
            await video_bucket.delete(ObjectId(post['video_file_id']))
        except Exception:
            pass
    file_id = await video_bucket.upload_from_stream(post_id, data, metadata={'mime': mime, 'post_id': post_id})
    await db.posts.update_one({'id': post_id}, {'$set': {'has_video': True, 'video_file_id': str(file_id), 'video_mime': mime, 'video_size': len(data)}})
    return {'video_url': f"/api/posts/{post_id}/video"}

@api_router.get("/posts/{post_id}/video")
async def get_post_video(post_id: str, request: Request):
    post = await db.posts.find_one({'id': post_id, 'has_video': True}, {'_id': 0, 'video_file_id': 1, 'video_mime': 1, 'video_size': 1})
    if not post:
        raise HTTPException(status_code=404, detail='Vídeo não encontrado')
    size = post['video_size']
    stream = await video_bucket.open_download_stream(ObjectId(post['video_file_id']))
    headers = {'Accept-Ranges': 'bytes', 'Cache-Control': 'public, max-age=604800', 'Content-Encoding': 'identity'}
    rng = request.headers.get('range')
    m = re.match(r'bytes=(\d*)-(\d*)', rng or '')
    if m and (m.group(1) or m.group(2)):
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2)))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end:
            raise HTTPException(status_code=416, detail='Range inválido')
        stream.seek(start)
        chunk = await stream.read(end - start + 1)
        headers['Content-Range'] = f'bytes {start}-{end}/{size}'
        return Response(content=chunk, status_code=206, media_type=post['video_mime'], headers=headers)
    return Response(content=await stream.read(), media_type=post['video_mime'], headers=headers)

# ==================== PROFILE PHOTOS ====================

PROFILE_PHOTOS_MAX = 6

class ProfilePhotoIn(BaseModel):
    image: str

@api_router.post("/profile/photos")
async def add_profile_photo(payload: ProfilePhotoIn, current_user: User = Depends(get_current_user)):
    if await db.profile_photos.count_documents({'user_id': current_user.id}) >= PROFILE_PHOTOS_MAX:
        raise HTTPException(status_code=400, detail=f'Máximo de {PROFILE_PHOTOS_MAX} fotos')
    header, _, data = payload.image.partition(',')
    mime = header[5:].split(';')[0] if header.startswith('data:') else ''
    if mime not in AVATAR_MIMES or not data:
        raise HTTPException(status_code=400, detail='Formato de imagem inválido')
    try:
        raw = base64.b64decode(data, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail='Imagem inválida')
    if len(raw) > 2_000_000:
        raise HTTPException(status_code=413, detail='Imagem muito grande')
    photo_id = str(uuid.uuid4())
    await db.profile_photos.insert_one({'id': photo_id, 'user_id': current_user.id, 'data': raw, 'mime': mime, 'created_at': datetime.now(timezone.utc).isoformat()})
    return {'id': photo_id, 'url': f"/api/profile-photos/{photo_id}"}

@api_router.get("/users/{user_id}/photos")
async def list_profile_photos(user_id: str, current_user: User = Depends(get_current_user)):
    docs = await db.profile_photos.find({'user_id': user_id}, {'_id': 0, 'id': 1}).sort('created_at', 1).to_list(PROFILE_PHOTOS_MAX)
    return [{'id': d['id'], 'url': f"/api/profile-photos/{d['id']}"} for d in docs]

@api_router.get("/profile-photos/{photo_id}")
async def get_profile_photo(photo_id: str):
    doc = await db.profile_photos.find_one({'id': photo_id}, {'_id': 0, 'data': 1, 'mime': 1})
    if not doc:
        raise HTTPException(status_code=404, detail='Foto não encontrada')
    return Response(content=bytes(doc['data']), media_type=doc['mime'], headers={'Cache-Control': 'public, max-age=31536000, immutable'})

@api_router.delete("/profile/photos/{photo_id}")
async def delete_profile_photo(photo_id: str, current_user: User = Depends(get_current_user)):
    res = await db.profile_photos.delete_one({'id': photo_id, 'user_id': current_user.id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Foto não encontrada')
    return {'ok': True}

# ==================== AUTO TRANSLATION ====================

LANG_NAMES = {'pt': 'Brazilian Portuguese', 'fr': 'French', 'en': 'English', 'es': 'Spanish'}

class TranslateIn(BaseModel):
    texts: List[str] = Field(max_length=150)
    lang: str

def _tkey(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

async def _llm_translate(texts: List[str], lang: str) -> List[str]:
    system = (f"You translate user interface texts and user posts of a migrant-help app into {LANG_NAMES[lang]}. "
              "You receive a JSON array of strings. Return ONLY a JSON array of the same length with each item translated, "
              "keeping order, emojis, numbers, punctuation, line breaks, URLs, e-mails and proper names. "
              "If an item is already in the target language, return it unchanged.")
    payload = json.dumps(texts, ensure_ascii=False)
    if os.environ.get('EMERGENT_LLM_KEY'):
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(api_key=os.environ['EMERGENT_LLM_KEY'], session_id=f"translate-{uuid.uuid4()}",
                       system_message=system).with_model("openai", "gpt-5.4-mini")
        raw = await chat.send_message(UserMessage(text=payload))
    else:
        providers = [(k, u, m) for k, u, m in [
            (os.environ.get('GROQ_API_KEY'), "https://api.groq.com/openai/v1", os.environ.get('GROQ_MODEL', 'openai/gpt-oss-120b')),
            (os.environ.get('OPENAI_API_KEY'), None, 'gpt-4o-mini'),
            (os.environ.get('OPENROUTER_API_KEY'), "https://openrouter.ai/api/v1", os.environ.get('OPENROUTER_MODEL', 'google/gemma-4-31b-it:free')),
        ] if k]
        if not providers:
            raise ValueError('no translation provider configured')
        key, base_url, model = providers[0]
        ai = AsyncOpenAI(api_key=key, base_url=base_url) if base_url else AsyncOpenAI(api_key=key)
        resp = await ai.chat.completions.create(model=model, messages=[{"role": "system", "content": system}, {"role": "user", "content": payload}])
        raw = resp.choices[0].message.content or ''
    start, end = raw.find('['), raw.rfind(']')
    out = json.loads(raw[start:end + 1])
    if not isinstance(out, list) or len(out) != len(texts):
        raise ValueError('bad translation length')
    return [str(o) for o in out]

_translate_hits: dict = {}

@api_router.post("/translate")
async def translate_texts(data: TranslateIn, request: Request):
    if data.lang not in LANG_NAMES:
        raise HTTPException(status_code=400, detail='Idioma inválido')
    ip = (request.headers.get('x-forwarded-for') or (request.client.host if request.client else '')).split(',')[0].strip()
    now_ts = datetime.now(timezone.utc).timestamp()
    hits = [t for t in _translate_hits.get(ip, []) if now_ts - t < 60]
    if len(hits) >= 60:
        raise HTTPException(status_code=429, detail='Muitas solicitações')
    _translate_hits[ip] = hits + [now_ts]
    texts = [t[:3000] for t in data.texts]
    keys = [_tkey(t) for t in texts]
    cached = {d['key']: d['text'] async for d in db.translations.find({'lang': data.lang, 'key': {'$in': keys}}, {'_id': 0, 'key': 1, 'text': 1})}
    missing = list({k: t for k, t in zip(keys, texts) if k not in cached}.items())
    batches = [missing[i:i + 30] for i in range(0, len(missing), 30)]

    async def run(batch):
        try:
            translated = await _llm_translate([t for _, t in batch], data.lang)
        except Exception as e:
            logging.warning(f"Translation failed: {e}")
            return
        for (k, src), tr in zip(batch, translated):
            cached[k] = tr
            if tr.strip() != src.strip():
                await db.translations.update_one({'lang': data.lang, 'key': k}, {'$set': {'text': tr}}, upsert=True)

    await asyncio.gather(*(run(b) for b in batches))
    return {'translations': [cached.get(k, t) for k, t in zip(keys, texts)]}

app.include_router(api_router)

from marketplace import build_router as build_marketplace_router
app.include_router(build_marketplace_router(db, get_current_user, User))

# Health check na raiz para o Render
@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "message": "Watizat API is running",
        "api_endpoint": "/api"
    }

# Health check alternativo
@app.get("/health")
async def health():
    try:
        # Testa conexão MongoDB
        await db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def create_indexes():
    try:
        await db.posts.create_index([('created_at', -1)])
        await db.posts.create_index('id', unique=True)
        await db.posts.create_index([('type', 1), ('created_at', -1)])
        await db.posts.create_index('user_id')
        await db.users.create_index('id', unique=True)
        await db.users.create_index('email', unique=True)
        await db.comments.create_index([('post_id', 1), ('created_at', 1)])
        await db.messages.create_index([('from_user_id', 1), ('to_user_id', 1)])
        await db.avatars.create_index('user_id', unique=True)
    except Exception as e:
        logger.warning(f"Index creation skipped: {e}")
    await seed_admin()


async def seed_admin():
    # Admin do painel vem de ADMIN_EMAIL / ADMIN_PASSWORD (idempotente)
    email = os.environ.get('ADMIN_EMAIL')
    password = os.environ.get('ADMIN_PASSWORD')
    if not email or not password:
        return
    email = email.strip().lower()
    existing = await db.users.find_one({'email': email}, {'_id': 0, 'id': 1, 'password': 1, 'role': 1})
    if existing is None:
        admin = User(email=email, name='Administrador', role='admin', languages=['pt']).model_dump()
        admin['password'] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        admin['created_at'] = admin['created_at'].isoformat()
        await db.users.insert_one(admin)
        logger.info(f"Admin criado: {email}")
        return
    updates = {}
    if existing.get('role') != 'admin':
        updates['role'] = 'admin'
    if not existing.get('password') or not bcrypt.checkpw(password.encode(), existing['password'].encode()):
        updates['password'] = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    if updates:
        await db.users.update_one({'email': email}, {'$set': updates})
        logger.info(f"Admin atualizado: {email}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
