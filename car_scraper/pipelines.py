import os
import logging
from datetime import datetime

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


class CarScraperPipeline:

    def open_spider(self, spider):
        logging.info("Connecting to the database")
        self.connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        self.curr = self.connection.cursor()

    def process_item(self, item, spider):
        self.curr.execute(''' 
        CREATE TABLE IF NOT EXISTS cars (
            id SERIAL PRIMARY KEY,
            url TEXT,
            title TEXT,
            price_usd INTEGER,
            odometer INTEGER,
            username TEXT,
            phone_number TEXT,
            image_url TEXT,
            car_number TEXT,
            car_vin TEXT,
            datetime_found TIMESTAMP
        ) ''')

        self.curr.execute('''
            INSERT INTO cars (
                url, 
                title, 
                price_usd, 
                odometer, 
                username, 
                phone_number, 
                image_url, 
                car_number, 
                car_vin, 
                datetime_found
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            item['url'],
            item['title'],
            item['price_usd'],
            item['odometer'],
            item['username'],
            item['phone_number'],
            item['image_url'],
            item['car_number'],
            item['car_vin'],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        self.connection.commit()
        logging.info("Data transferred to the PostgreSQL database")
        return item

    def close_spider(self, spider):
        self.curr.close()
        logging.info("Closing database connection")
        self.connection.close()



