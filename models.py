from sqlalchemy import Column, String, Float, Integer

from database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String, unique=True, index=True)
    price = Column(Float)
    forward_pe = Column(Float)
    forward_eps = Column(Float)
    forward_yield = Column(Float)
    ma50 = Column(Float)
    ma200 = Column(Float)
