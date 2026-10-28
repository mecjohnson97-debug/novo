import re
import uuid
import secrets
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

PLANS = {
    'free': {'id': 'free', 'name': 'Grátis', 'price': 0.0, 'days': 0, 'trial': False,
             'features': ['Publicar pedidos e ofertas', 'Responder até 5 pedidos por mês', 'Chat com vizinhos', 'Caronas e vagas de emprego']},
    'premium': {'id': 'premium', 'name': 'Premium', 'price': 29.90, 'days': 30, 'trial': True,
                'features': ['Respostas ilimitadas', 'Alertas de novos pedidos perto de você', 'Selo Premium no perfil', '1 destaque de 7 dias por mês', 'Suporte prioritário']},
    'pro': {'id': 'pro', 'name': 'Pro', 'price': 59.90, 'days': 30, 'trial': True,
            'features': ['Tudo do Premium', 'Selo Profissional verificado', 'Perfil no topo das buscas', 'Destaques ilimitados de 7 dias', 'Estatísticas de visitas e contatos']},
}
BOOSTS = {
    'boost7': {'id': 'boost7', 'name': 'Destaque 7 dias', 'price': 9.90, 'days': 7},
    'boost15': {'id': 'boost15', 'name': 'Destaque 15 dias', 'price': 17.90, 'days': 15},
    'boost30': {'id': 'boost30', 'name': 'Destaque 30 dias', 'price': 29.90, 'days': 30},
}
TRIAL_DAYS = 3
DEFAULT_PIX = {'key': 'b22b05bc-de1c-4998-8870-e6a21d84bcd6', 'name': 'Eri Jonhson de Sousa Carv', 'city': 'SAO PAULO'}


def _now():
    return datetime.now(timezone.utc)


def _iso(dt):
    return dt.isoformat()


def _crc16(payload: str) -> str:
    crc = 0xFFFF
    for b in payload.encode('utf-8'):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def _ascii(text: str) -> str:
    table = str.maketrans('áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ', 'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC')
    return re.sub(r'[^A-Za-z0-9 .\-@]', '', (text or '').translate(table))


def _f(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def pix_code(key: str, name: str, city: str, amount: float, txid: str) -> str:
    account = _f('00', 'BR.GOV.BCB.PIX') + _f('01', key.strip())
    payload = (_f('00', '01') + _f('26', account) + _f('52', '0000') + _f('53', '986')
               + (_f('54', f"{amount:.2f}") if amount > 0 else '') + _f('58', 'BR')
               + _f('59', _ascii(name)[:25] or 'RECEBEDOR') + _f('60', _ascii(city).upper()[:15] or 'BRASIL')
               + _f('62', _f('05', re.sub(r'[^A-Za-z0-9]', '', txid)[:25] or '***')) + '6304')
    return payload + _crc16(payload)


class PaymentIn(BaseModel):
    kind: Literal['plan', 'boost']
    item_id: str
    post_id: Optional[str] = None


class TrialIn(BaseModel):
    plan: Literal['premium', 'pro']


class NotifyIn(BaseModel):
    note: Optional[str] = Field(default=None, max_length=500)
    receipt: Optional[str] = None


class PixSettingsIn(BaseModel):
    key: str = Field(min_length=3, max_length=77)
    name: str = Field(min_length=2, max_length=60)
    city: str = Field(min_length=2, max_length=40)


class RideIn(BaseModel):
    origin: str = Field(min_length=2, max_length=80)
    destination: str = Field(min_length=2, max_length=80)
    date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: str = Field(pattern=r'^\d{2}:\d{2}$')
    seats: int = Field(ge=1, le=8)
    price: float = Field(ge=0, le=5000)
    car: Optional[str] = Field(default=None, max_length=60)
    notes: Optional[str] = Field(default=None, max_length=500)
    pix_key: Optional[str] = Field(default=None, max_length=77)


class BookIn(BaseModel):
    seats: int = Field(ge=1, le=8)


def build_router(db, get_current_user, User):
    r = APIRouter(prefix="/api")

    def require_admin(user):
        if user.role != 'admin':
            raise HTTPException(status_code=403, detail='Admin only')

    async def pix_settings():
        doc = await db.settings.find_one({'id': 'pix'}, {'_id': 0}) or {}
        return {k: doc.get(k) or DEFAULT_PIX[k] for k in DEFAULT_PIX}

    async def active_subscription(user_id):
        sub = await db.subscriptions.find_one({'user_id': user_id}, {'_id': 0})
        if sub and sub.get('expires_at') and sub['expires_at'] > _iso(_now()):
            return sub
        return None

    def public_payment(p):
        p.pop('receipt', None)
        return p

    @r.get("/plans")
    async def get_plans():
        return {'plans': list(PLANS.values()), 'boosts': list(BOOSTS.values()), 'trial_days': TRIAL_DAYS}

    @r.get("/subscription/me")
    async def my_subscription(current_user: User = Depends(get_current_user)):
        sub = await active_subscription(current_user.id)
        used = await db.subscriptions.find_one({'user_id': current_user.id, 'trial_used': True}, {'_id': 0, 'user_id': 1})
        return {'plan': sub['plan'] if sub else 'free', 'expires_at': sub['expires_at'] if sub else None,
                'trial': bool(sub and sub.get('trial')), 'trial_available': not used}

    @r.post("/subscription/trial")
    async def start_trial(data: TrialIn, current_user: User = Depends(get_current_user)):
        existing = await db.subscriptions.find_one({'user_id': current_user.id}, {'_id': 0})
        if existing and existing.get('trial_used'):
            raise HTTPException(status_code=400, detail='Você já usou os 3 dias grátis')
        if await active_subscription(current_user.id):
            raise HTTPException(status_code=400, detail='Você já tem um plano ativo')
        expires = _iso(_now() + timedelta(days=TRIAL_DAYS))
        await db.subscriptions.update_one({'user_id': current_user.id}, {'$set': {
            'user_id': current_user.id, 'plan': data.plan, 'expires_at': expires, 'trial': True, 'trial_used': True}}, upsert=True)
        return {'plan': data.plan, 'expires_at': expires, 'trial': True}

    @r.post("/payments")
    async def create_payment(data: PaymentIn, current_user: User = Depends(get_current_user)):
        catalog = PLANS if data.kind == 'plan' else BOOSTS
        item = catalog.get(data.item_id)
        if not item or item['price'] <= 0:
            raise HTTPException(status_code=400, detail='Pacote inválido')
        if data.kind == 'boost':
            if not data.post_id or not await db.posts.find_one({'id': data.post_id, 'user_id': current_user.id}, {'_id': 0, 'id': 1}):
                raise HTTPException(status_code=400, detail='Escolha uma das suas publicações para destacar')
        pix = await pix_settings()
        txid = secrets.token_hex(6).upper()
        payment = {
            'id': str(uuid.uuid4()), 'txid': txid, 'user_id': current_user.id, 'user_name': current_user.name,
            'user_email': current_user.email, 'kind': data.kind, 'item_id': item['id'], 'item_name': item['name'],
            'amount': item['price'], 'post_id': data.post_id, 'status': 'pending',
            'pix_code': pix_code(pix['key'], pix['name'], pix['city'], item['price'], txid),
            'pix_name': pix['name'], 'created_at': _iso(_now()),
        }
        await db.payments.insert_one(dict(payment))
        return payment

    @r.get("/payments/me")
    async def my_payments(current_user: User = Depends(get_current_user)):
        return await db.payments.find({'user_id': current_user.id}, {'_id': 0, 'receipt': 0}).sort('created_at', -1).to_list(50)

    @r.get("/payments/{payment_id}")
    async def get_payment(payment_id: str, current_user: User = Depends(get_current_user)):
        p = await db.payments.find_one({'id': payment_id}, {'_id': 0, 'receipt': 0})
        if not p or (p['user_id'] != current_user.id and current_user.role != 'admin'):
            raise HTTPException(status_code=404, detail='Pagamento não encontrado')
        return p

    @r.post("/payments/{payment_id}/notify")
    async def notify_payment(payment_id: str, data: NotifyIn, current_user: User = Depends(get_current_user)):
        p = await db.payments.find_one({'id': payment_id, 'user_id': current_user.id}, {'_id': 0, 'status': 1})
        if not p:
            raise HTTPException(status_code=404, detail='Pagamento não encontrado')
        if p['status'] not in ('pending', 'review'):
            raise HTTPException(status_code=400, detail='Este pagamento já foi analisado')
        update = {'status': 'review', 'note': data.note, 'notified_at': _iso(_now())}
        if data.receipt:
            header, _, b64 = data.receipt.partition(',')
            if not header.startswith('data:image/') or len(b64) > 2_800_000:
                raise HTTPException(status_code=400, detail='Comprovante inválido (imagem até 2MB)')
            base64.b64decode(b64, validate=True)
            update['receipt'] = data.receipt
            update['has_receipt'] = True
        await db.payments.update_one({'id': payment_id}, {'$set': update})
        return {'status': 'review'}

    async def activate(p):
        now = _now()
        if p['kind'] == 'plan':
            sub = await active_subscription(p['user_id'])
            base = datetime.fromisoformat(sub['expires_at']) if sub and sub['plan'] == p['item_id'] and not sub.get('trial') else now
            await db.subscriptions.update_one({'user_id': p['user_id']}, {'$set': {
                'user_id': p['user_id'], 'plan': p['item_id'], 'trial': False,
                'expires_at': _iso(base + timedelta(days=PLANS[p['item_id']]['days']))}}, upsert=True)
        else:
            post = await db.posts.find_one({'id': p['post_id']}, {'_id': 0, 'boosted_until': 1}) or {}
            cur = post.get('boosted_until')
            base = datetime.fromisoformat(cur) if cur and cur > _iso(now) else now
            await db.posts.update_one({'id': p['post_id']}, {'$set': {'boosted_until': _iso(base + timedelta(days=BOOSTS[p['item_id']]['days']))}})

    @r.get("/admin/payments")
    async def admin_payments(status: Optional[str] = None, current_user: User = Depends(get_current_user)):
        require_admin(current_user)
        q = {'status': status} if status else {}
        items = await db.payments.find(q, {'_id': 0, 'receipt': 0}).sort('created_at', -1).to_list(200)
        approved = await db.payments.find({'status': 'approved'}, {'_id': 0, 'amount': 1}).to_list(5000)
        return {'payments': items, 'stats': {
            'revenue': round(sum(x['amount'] for x in approved), 2),
            'pending': await db.payments.count_documents({'status': {'$in': ['pending', 'review']}}),
            'active_subscriptions': await db.subscriptions.count_documents({'expires_at': {'$gt': _iso(_now())}}),
            'rides': await db.rides.count_documents({}),
        }}

    @r.get("/admin/payments/{payment_id}/receipt")
    async def admin_receipt(payment_id: str, current_user: User = Depends(get_current_user)):
        require_admin(current_user)
        p = await db.payments.find_one({'id': payment_id}, {'_id': 0, 'receipt': 1})
        if not p or not p.get('receipt'):
            raise HTTPException(status_code=404, detail='Sem comprovante')
        return {'receipt': p['receipt']}

    @r.post("/admin/payments/{payment_id}/{action}")
    async def admin_review(payment_id: str, action: Literal['approve', 'reject'], current_user: User = Depends(get_current_user)):
        require_admin(current_user)
        p = await db.payments.find_one({'id': payment_id}, {'_id': 0, 'receipt': 0})
        if not p:
            raise HTTPException(status_code=404, detail='Pagamento não encontrado')
        if p['status'] == 'approved':
            raise HTTPException(status_code=400, detail='Pagamento já aprovado')
        if action == 'approve':
            await activate(p)
        status = 'approved' if action == 'approve' else 'rejected'
        await db.payments.update_one({'id': payment_id}, {'$set': {'status': status, 'reviewed_at': _iso(_now()), 'reviewed_by': current_user.id}})
        return {'status': status}

    @r.get("/admin/pix-settings")
    async def get_pix_settings(current_user: User = Depends(get_current_user)):
        require_admin(current_user)
        return await pix_settings()

    @r.put("/admin/pix-settings")
    async def put_pix_settings(data: PixSettingsIn, current_user: User = Depends(get_current_user)):
        require_admin(current_user)
        await db.settings.update_one({'id': 'pix'}, {'$set': {'id': 'pix', **data.model_dump()}}, upsert=True)
        return await pix_settings()

    # ---------- Caronas ----------
    def ride_out(ride, user_id=None):
        ride = {k: v for k, v in ride.items() if k != 'pix_key'}
        ride['has_pix'] = bool(ride.pop('has_pix', False))
        ride['is_mine'] = ride['driver_id'] == user_id
        return ride

    @r.post("/rides")
    async def create_ride(data: RideIn, current_user: User = Depends(get_current_user)):
        if f"{data.date}T{data.time}" < _now().strftime('%Y-%m-%dT%H:%M'):
            raise HTTPException(status_code=400, detail='A data da viagem já passou')
        ride = {**data.model_dump(), 'id': str(uuid.uuid4()), 'driver_id': current_user.id, 'driver_name': current_user.name,
                'seats_left': data.seats, 'status': 'active', 'has_pix': bool(data.pix_key), 'created_at': _iso(_now())}
        await db.rides.insert_one(dict(ride))
        return ride_out(ride, current_user.id)

    @r.get("/rides")
    async def list_rides(origin: str = '', destination: str = '', date: str = '', current_user: User = Depends(get_current_user)):
        q = {'status': 'active', 'seats_left': {'$gt': 0}, 'date': {'$gte': date or _now().strftime('%Y-%m-%d')}}
        if date:
            q['date'] = date
        if origin.strip():
            q['origin'] = {'$regex': re.escape(origin.strip()), '$options': 'i'}
        if destination.strip():
            q['destination'] = {'$regex': re.escape(destination.strip()), '$options': 'i'}
        rides = await db.rides.find(q, {'_id': 0}).sort([('date', 1), ('time', 1)]).to_list(100)
        return [ride_out(x, current_user.id) for x in rides]

    @r.get("/rides/mine")
    async def my_rides(current_user: User = Depends(get_current_user)):
        offered = await db.rides.find({'driver_id': current_user.id}, {'_id': 0}).sort('date', -1).to_list(100)
        for ride in offered:
            ride['bookings'] = await db.ride_bookings.find({'ride_id': ride['id'], 'status': 'confirmed'}, {'_id': 0}).to_list(20)
        booked = await db.ride_bookings.find({'passenger_id': current_user.id}, {'_id': 0}).sort('created_at', -1).to_list(100)
        return {'offered': [ride_out(x, current_user.id) | {'bookings': x['bookings']} for x in offered], 'booked': booked}

    @r.post("/rides/{ride_id}/book")
    async def book_ride(ride_id: str, data: BookIn, current_user: User = Depends(get_current_user)):
        ride = await db.rides.find_one({'id': ride_id, 'status': 'active'}, {'_id': 0})
        if not ride:
            raise HTTPException(status_code=404, detail='Carona não encontrada')
        if ride['driver_id'] == current_user.id:
            raise HTTPException(status_code=400, detail='Você não pode reservar sua própria carona')
        res = await db.rides.update_one({'id': ride_id, 'seats_left': {'$gte': data.seats}}, {'$inc': {'seats_left': -data.seats}})
        if res.modified_count == 0:
            raise HTTPException(status_code=400, detail='Não há vagas suficientes')
        total = round(ride['price'] * data.seats, 2)
        booking = {'id': str(uuid.uuid4()), 'ride_id': ride_id, 'passenger_id': current_user.id, 'passenger_name': current_user.name,
                   'driver_id': ride['driver_id'], 'driver_name': ride['driver_name'], 'seats': data.seats, 'total': total,
                   'origin': ride['origin'], 'destination': ride['destination'], 'date': ride['date'], 'time': ride['time'],
                   'status': 'confirmed', 'created_at': _iso(_now())}
        if ride.get('pix_key') and total > 0:
            booking['pix_code'] = pix_code(ride['pix_key'], ride['driver_name'], 'BRASIL', total, booking['id'][:8])
        await db.ride_bookings.insert_one(dict(booking))
        await db.messages.insert_one({
            'id': str(uuid.uuid4()), 'from_user_id': current_user.id, 'to_user_id': ride['driver_id'],
            'message': f"Reservei {data.seats} vaga(s) na sua carona {ride['origin']} → {ride['destination']} em {ride['date']} às {ride['time']}.",
            'created_at': _iso(_now()), 'media': []})
        return booking

    @r.post("/rides/bookings/{booking_id}/cancel")
    async def cancel_booking(booking_id: str, current_user: User = Depends(get_current_user)):
        b = await db.ride_bookings.find_one({'id': booking_id, 'passenger_id': current_user.id, 'status': 'confirmed'}, {'_id': 0})
        if not b:
            raise HTTPException(status_code=404, detail='Reserva não encontrada')
        await db.ride_bookings.update_one({'id': booking_id}, {'$set': {'status': 'cancelled'}})
        await db.rides.update_one({'id': b['ride_id']}, {'$inc': {'seats_left': b['seats']}})
        return {'status': 'cancelled'}

    @r.post("/rides/{ride_id}/cancel")
    async def cancel_ride(ride_id: str, current_user: User = Depends(get_current_user)):
        res = await db.rides.update_one({'id': ride_id, 'driver_id': current_user.id}, {'$set': {'status': 'cancelled'}})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail='Carona não encontrada')
        await db.ride_bookings.update_many({'ride_id': ride_id, 'status': 'confirmed'}, {'$set': {'status': 'cancelled'}})
        return {'status': 'cancelled'}

    return r
