from datetime import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_salt = Column(LargeBinary, nullable=False)
    password_verifier = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cards = relationship('Card', back_populates='owner', cascade='all, delete-orphan')
    subscriptions = relationship('Subscription', back_populates='owner', cascade='all, delete-orphan')

class Card(Base):
    __tablename__ = 'cards'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    label = Column(String, nullable=True)
    enc_data = Column(LargeBinary, nullable=False)
    nonce = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship('User', back_populates='cards')

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    service_name = Column(String, nullable=False, index=True)
    cost = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False, default='USD')
    billing_cycle = Column(String(50), default='monthly')
    next_billing_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship('User', back_populates='subscriptions')