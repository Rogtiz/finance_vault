from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import base64
from datetime import timedelta

from . import crud, models, schemas, auth, crypto
from .config import ACCESS_TOKEN_EXPIRE_MINUTES

# Cоздаем роутер. Все эндпоинты будут привязаны к нему.
router = APIRouter()

# --- Auth Endpoints ---

@router.post("/register", response_model=schemas.Token)
def register(u: schemas.UserCreate, db: Session = Depends(auth.get_db)):
    if crud.get_user_by_username(db, u.username):
        raise HTTPException(status_code=400, detail="Username exists")
    
    user = crud.create_user(db, u)
    token = auth.create_access_token(
        {"sub": user.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

@router.post('/token', response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(auth.get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not crypto.verify_password(form_data.password, user.password_salt, user.password_verifier):
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    
    token = auth.create_access_token(
        {"sub": user.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

# --- Card Endpoints ---

# @router.post('/cards', response_model=schemas.CardOut)
# def create_card(card: schemas.CardCreate, 
#                 current_user: models.User = Depends(auth.get_current_user), 
#                 db: Session = Depends(auth.get_db)):
    
#     db_card = crud.create_user_card(db, card, current_user)
#     masked = crypto.mask_card_number(card.card_number)
    
#     return schemas.CardOut(
#         id=db_card.id,
#         label=db_card.label,
#         masked=masked,
#         holder=card.holder,
#         exp=card.exp,
#         created_at=db_card.created_at
#     )

# @router.get('/cards', response_model=List[schemas.CardOut])
# def list_cards(current_user: models.User = Depends(auth.get_current_user), 
#                db: Session = Depends(auth.get_db)):
    
#     cards = crud.get_user_cards(db, current_user.id)
#     out = []
#     key = crypto.user_key_from_user(current_user)
    
#     for c in cards:
#         try:
#             payload = crypto.decrypt_payload(key, c.nonce, c.enc_data)
#             masked = crypto.mask_card_number(payload.get('card_number',''))
#             holder = payload.get('holder')
#             exp = payload.get('exp')
#         except Exception:
#             masked, holder, exp = '(cannot decrypt)', None, None
            
#         out.append(schemas.CardOut(
#             id=c.id, label=c.label, masked=masked, holder=holder, exp=exp, created_at=c.created_at
#         ))
#     return out

# @router.get('/cards/{card_id}', response_model=schemas.CardFull)
# def get_card(card_id: int, 
#              current_user: models.User = Depends(auth.get_current_user), 
#              db: Session = Depends(auth.get_db)):
    
#     c = crud.get_user_card(db, card_id, current_user.id)
#     if not c:
#         raise HTTPException(status_code=404, detail='Not found')
    
#     key = crypto.user_key_from_user(current_user)
#     payload = crypto.decrypt_payload(key, c.nonce, c.enc_data)
    
#     return schemas.CardFull(
#         id=c.id, label=c.label, card_number=payload.get('card_number'), 
#         holder=payload.get('holder'), exp=payload.get('exp'), 
#         cvv=payload.get('cvv'), notes=payload.get('notes'), created_at=c.created_at
#     )

# --- Card Endpoints (Используем RAW-логику как основную) ---

# Было: @router.post('/cards', response_model=schemas.CardOut)
@router.post('/cards', response_model=schemas.RawCardOut)
def create_card(card: schemas.RawCardIn, # <-- Схема изменена на RawCardIn
                current_user: models.User = Depends(auth.get_current_user), 
                db: Session = Depends(auth.get_db)):
    
    db_card = crud.create_user_card(db, card, current_user.id) # <-- Вызываем переименованный crud
    
    # Теперь возвращаем RawCardOut
    return schemas.RawCardOut(
        id=db_card.id, label=db_card.label, 
        enc_data_b64=card.enc_data_b64, # Возвращаем то, что прислал клиент
        nonce_b64=card.nonce_b64, 
        created_at=db_card.created_at
    )

# Было: @router.get('/cards', response_model=List[schemas.CardOut])
@router.get('/cards', response_model=List[schemas.RawCardOut])
def list_cards(current_user: models.User = Depends(auth.get_current_user), 
               db: Session = Depends(auth.get_db)):
    
    cards = crud.get_user_cards(db, current_user.id)
    # Удалена логика дешифровки, просто возвращаем RAW
    return [
        schemas.RawCardOut(
            id=c.id, label=c.label, 
            enc_data_b64=base64.b64encode(c.enc_data).decode('ascii'), 
            nonce_b64=base64.b64encode(c.nonce).decode('ascii'), 
            created_at=c.created_at
        ) for c in cards
    ]

# Было: @router.get('/cards/{card_id}', response_model=schemas.CardFull)
@router.get('/cards/{card_id}', response_model=schemas.RawCardOut)
def get_card(card_id: int, 
             current_user: models.User = Depends(auth.get_current_user), 
             db: Session = Depends(auth.get_db)):
    
    c = crud.get_user_card(db, card_id, current_user.id)
    if not c:
        raise HTTPException(status_code=404, detail='Not found')
    
    # Удалена логика дешифровки, возвращаем RAW
    return schemas.RawCardOut(
        id=c.id, label=c.label, 
        enc_data_b64=base64.b64encode(c.enc_data).decode('ascii'), 
        nonce_b64=base64.b64encode(c.nonce).decode('ascii'), 
        created_at=c.created_at
    )

# Удалите или закомментируйте все роуты /cards/raw (они теперь дублируются)
# Убедитесь, что роуты /cards/raw/... БОЛЬШЕ не существуют!

@router.delete('/cards/{card_id}')
def delete_card(card_id: int, 
                current_user: models.User = Depends(auth.get_current_user), 
                db: Session = Depends(auth.get_db)):
    
    deleted = crud.delete_user_card(db, card_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Not found')
    return {"detail": "deleted"}

# --- Raw Card Endpoints ---

# @router.post('/cards/raw', response_model=schemas.RawCardOut)
# def create_raw_card(raw: schemas.RawCardIn, 
#                     current_user: models.User = Depends(auth.get_current_user), 
#                     db: Session = Depends(auth.get_db)):
    
#     c = crud.create_raw_card(db, raw, current_user.id)
#     return schemas.RawCardOut(
#         id=c.id, label=c.label, enc_data_b64=raw.enc_data_b64, 
#         nonce_b64=raw.nonce_b64, created_at=c.created_at
#     )

# @router.get('/cards/raw', response_model=List[schemas.RawCardOut])
# def list_raw_cards(current_user: models.User = Depends(auth.get_current_user), 
#                    db: Session = Depends(auth.get_db)):
    
#     cards = crud.get_user_cards(db, current_user.id)
#     return [
#         schemas.RawCardOut(
#             id=c.id, label=c.label, 
#             enc_data_b64=base64.b64encode(c.enc_data).decode('ascii'), 
#             nonce_b64=base64.b64encode(c.nonce).decode('ascii'), 
#             created_at=c.created_at
#         ) for c in cards
#     ]

# @router.get('/cards/raw/{card_id}', response_model=schemas.RawCardOut)
# def get_raw_card(card_id: int, 
#                  current_user: models.User = Depends(auth.get_current_user), 
#                  db: Session = Depends(auth.get_db)):
    
#     c = crud.get_user_card(db, card_id, current_user.id)
#     if not c:
#         raise HTTPException(status_code=404, detail='Not found')
    
#     return schemas.RawCardOut(
#         id=c.id, label=c.label, 
#         enc_data_b64=base64.b64encode(c.enc_data).decode('ascii'), 
#         nonce_b64=base64.b64encode(c.nonce).decode('ascii'), 
#         created_at=c.created_at
    )

# --- Subscription Endpoints ---

@router.post('/subscriptions', response_model=schemas.SubscriptionOut)
def create_subscription(sub: schemas.SubscriptionCreate, 
                        current_user: models.User = Depends(auth.get_current_user), 
                        db: Session = Depends(auth.get_db)):
    
    return crud.create_user_sub(db, sub, current_user.id)

@router.get('/subscriptions', response_model=List[schemas.SubscriptionOut])
def list_subscriptions(current_user: models.User = Depends(auth.get_current_user), 
                       db: Session = Depends(auth.get_db)):
    
    return crud.get_user_subs(db, current_user.id)

@router.get('/subscriptions/{sub_id}', response_model=schemas.SubscriptionOut)
def get_subscription(sub_id: int, 
                     current_user: models.User = Depends(auth.get_current_user), 
                     db: Session = Depends(auth.get_db)):
    
    sub = crud.get_user_sub(db, sub_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail='Subscription not found')
    return sub

@router.put('/subscriptions/{sub_id}', response_model=schemas.SubscriptionOut)
def update_subscription(sub_id: int, 
                        sub_in: schemas.SubscriptionCreate, 
                        current_user: models.User = Depends(auth.get_current_user), 
                        db: Session = Depends(auth.get_db)):
    
    sub_db = crud.update_user_sub(db, sub_id, sub_in, current_user.id)
    if not sub_db:
        raise HTTPException(status_code=404, detail='Subscription not found')
    return sub_db

@router.delete('/subscriptions/{sub_id}')
def delete_subscription(sub_id: int, 
                        current_user: models.User = Depends(auth.get_current_user), 
                        db: Session = Depends(auth.get_db)):
    
    sub_db = crud.delete_user_sub(db, sub_id, current_user.id)
    if not sub_db:
        raise HTTPException(status_code=404, detail='Subscription not found')
    return {"detail": "deleted"}