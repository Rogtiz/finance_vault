from sqlalchemy.orm import Session
import os
import base64
from . import models, schemas, crypto
from .config import SALT_SIZE

# --- User ---
def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    salt = os.urandom(SALT_SIZE)
    verifier = crypto.make_password_verifier(user.password, salt)
    db_user = models.User(
        username=user.username,
        password_salt=salt,
        password_verifier=verifier
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Card ---
def create_user_card(db: Session, card: schemas.CardCreate, user: models.User):
    key = crypto.user_key_from_user(user)
    payload = {
        "card_number": card.card_number,
        "holder": card.holder,
        "exp": card.exp,
        "cvv": card.cvv,
        "notes": card.notes
    }
    nonce, ct = crypto.encrypt_payload(key, payload)
    db_card = models.Card(
        owner_id=user.id,
        label=card.label,
        enc_data=ct,
        nonce=nonce
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

def get_user_cards(db: Session, user_id: int):
    return db.query(models.Card).filter(models.Card.owner_id == user_id).all()

def get_user_card(db: Session, card_id: int, user_id: int):
    return db.query(models.Card).filter(models.Card.id == card_id, models.Card.owner_id == user_id).first()

def delete_user_card(db: Session, card_id: int, user_id: int):
    db_card = get_user_card(db, card_id, user_id)
    if not db_card:
        return None
    db.delete(db_card)
    db.commit()
    return db_card

# --- Card Raw ---
def create_raw_card(db: Session, raw: schemas.RawCardIn, user_id: int):
    ct = base64.b64decode(raw.enc_data_b64)
    nonce = base64.b64decode(raw.nonce_b64)
    db_card = models.Card(
        owner_id=user_id,
        label=raw.label,
        enc_data=ct,
        nonce=nonce
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

# --- Subscription ---
def create_user_sub(db: Session, sub: schemas.SubscriptionCreate, user_id: int):
    db_sub = models.Subscription(**sub.dict(), owner_id=user_id)
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return db_sub

def get_user_subs(db: Session, user_id: int):
    return db.query(models.Subscription).filter(models.Subscription.owner_id == user_id).order_by(models.Subscription.next_billing_date.asc()).all()

def get_user_sub(db: Session, sub_id: int, user_id: int):
    return db.query(models.Subscription).filter(models.Subscription.id == sub_id, models.Subscription.owner_id == user_id).first()

def update_user_sub(db: Session, sub_id: int, sub_in: schemas.SubscriptionCreate, user_id: int):
    db_sub = get_user_sub(db, sub_id, user_id)
    if not db_sub:
        return None
    update_data = sub_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_sub, key, value)
    db.commit()
    db.refresh(db_sub)
    return db_sub

def delete_user_sub(db: Session, sub_id: int, user_id: int):
    db_sub = get_user_sub(db, sub_id, user_id)
    if not db_sub:
        return None
    db.delete(db_sub)
    db.commit()
    return db_sub