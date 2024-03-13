# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy  # Define here the models for your scraped items

#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class CarItem:
    url: str
    title: str
    price_usd: Optional[int]
    odometer: int
    username: Optional[str]
    phone_number: Optional[str]
    image_url: Optional[str]
    car_number: Optional[str]
    car_vin: Optional[str]
    datetime_found: datetime