import os

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

from .items import CarItem, Base

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

POSTGRES_DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class CarScraperPipeline:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    @classmethod
    def from_crawler(cls, crawler):
        db_url = crawler.settings.get('POSTGRES_DB_URL', POSTGRES_DB_URL)
        return cls(db_url)

    def process_item(self, item, spider):
        session = self.Session()

        instance = session.query(CarItem).filter_by(**item).one_or_none()
        if instance:
            session.close()
            return instance

        car_item = CarItem(**item)
        try:
            session.add(car_item)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        return item
