# database.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, DateTime

Base = declarative_base()


class CarItem(Base):
    __tablename__ = 'car_items'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    title = Column(String)
    price_usd = Column(Integer)
    odometer = Column(Integer)
    username = Column(String)
    phone_number = Column(String)
    image_url = Column(String)
    car_number = Column(String)
    car_vin = Column(String)
    city = Column(String)
    owners_count = Column(Integer)
    datetime_found = Column(DateTime)
