import json
import logging
import re

import scrapy
from scrapy.http import HtmlResponse


# logger configuration to log to fie
logging.basicConfig(
    level=logging.ERROR,
    format="[%(levelname)s] %(message)s (Line %(lineno)d)",
    handlers=[
        logging.FileHandler("car_debug.log"),
        logging.StreamHandler()
    ]
)


class CarSpider(scrapy.Spider):
    name = "cars"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/uk/car/used/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def parse(self, response: HtmlResponse):
        """Parse the main page and extract total pages, then proceed to parse each page."""
        try:
            total_pages_selector = response.css("#pagination > nav > span:nth-child(8) > a::text").get()
            total_pages = int(total_pages_selector.replace(" ", ""))
        except Exception as e:
            logging.error(f"Failed to parse main page: {e}")
            total_pages = 10  # Setting the default value to 10

        for page_number in range(1, total_pages + 1):
            next_page_url = f"https://auto.ria.com/uk/car/used/?page={page_number}"
            yield scrapy.Request(next_page_url, callback=self.parse_page)

    def parse_page(self, response: HtmlResponse):
        """Parse individual page and extract links to car listings."""
        car_links = response.css('div.head-ticket > div.item.ticket-title > a.address::attr(href)').getall()
        for car_link in car_links:
            yield scrapy.Request(car_link, callback=self.parse_car_details)

    def parse_car_details(self, response: HtmlResponse):
        """Parse the details of a car listing."""
        try:
            raise Exception("Test error")  # Это намеренная ошибка для проверки логирования
            # Остальной код функции
        except Exception as e:
            logging.error(f"Failed to parse car details: {e}")

    def parse_phone_numbers(self, response: HtmlResponse):
        """Parse the phone numbers from the AJAX response."""
        item = response.meta['item']
        try:
            phone_data = json.loads(response.text)
            first_phone = phone_data.get('phones', [])[0]  # Get the first phone number from the list of phones
            phone_number = first_phone.get('phoneFormatted') if first_phone else None

            formatted_phone_number = self.format_phone_number(phone_number)  # Formatting the phone number
            item['phone_number'] = formatted_phone_number
            yield item
        except Exception as e:
            self.logger.error(f"Failed to parse phone number for {item['url']}: {e}")

    @staticmethod
    def format_phone_number(phone_number):
        """Format the phone number into international format."""
        digits = re.sub(r'\D', '', phone_number)
        formatted_number = f"+38{digits}"
        return formatted_number

    @staticmethod
    def get_data_attributes(response: HtmlResponse):
        """Get data attributes from the page."""
        script_tag = response.css('[class^="js-user-secure"]')
        data_hash = script_tag.xpath("@data-hash").extract_first()
        data_expires = script_tag.xpath("@data-expires").extract_first()
        data_auto_id = response.css("body::attr(data-auto-id)").extract_first()
        return data_hash, data_expires, data_auto_id

    @staticmethod
    def extract_image_url(response: HtmlResponse):
        """Extract the image URL of the car."""
        image_url = response.css("#photosBlock img::attr(src)").get()
        if not image_url:
            image_url = response.css("div.image-gallery-slides ::attr(src)").get()
        return image_url

    @staticmethod
    def extract_price_usd(response: HtmlResponse):
        """Extract the price of the car in USD."""
        price_value = response.css('section.price.mb-15.mhide > div.price_value > strong::text').get()
        if price_value:
            price_usd = price_value.split('$')[0].replace(' ','')
            return int(price_usd)

        return None

    def get_user_name(self, response: HtmlResponse):
        """Get the username of the seller from the page."""
        selectors = [
            "#userInfoBlock div.seller_info div.seller_info_name a::text",
            "#userInfoBlock div.seller_info.mb-15 div h4 a::text",
            "#userInfoBlock div.seller_info_area div h4 a::text",
            "#userInfoBlock div.seller_info div.seller_info_name::text",
        ]

        for selector in selectors:
            user_name = response.css(selector).get()
            if user_name:
                return user_name.strip()

        return None

    def extract_city(self, response):
        """Extract the city information from the response."""
        selectors = ['#userInfoBlock > ul:nth-child(2) > li:nth-child(1)::text',
                     '#basicInfoTableMainInfoRight1 > span::text',
                     '#breadcrumbs > div:nth-child(3) > a > span::text']
        for selector in selectors:
            city = response.css(selector).get()
            if city:
                return city.strip()

        return None

    def extract_owners_count(self, response):
        """Extract the number of owners from the response."""
        if response.css("dd:contains('Кількість власників')"):
            owners_count = response.css("dd:contains('Кількість власників') span.argument::text").get()
        else:
            owners_count = 0
        return owners_count


