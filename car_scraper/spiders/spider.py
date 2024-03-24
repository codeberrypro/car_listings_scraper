import json
import re
import datetime

import scrapy
from scrapy.http import HtmlResponse


class CarSpider(scrapy.Spider):
    name = "cars"
    allowed_domains = ["auto.ria.com"]
    start_urls = ["https://auto.ria.com/uk/car/used/"]

    def parse(self, response: HtmlResponse):
        """Parse the main page and extract total pages, then proceed to parse each page."""
        total_pages_text = response.xpath('//nav//a[contains(text(), "Вперед")]/preceding-sibling::span/text()').get()
        total_pages = int(re.search(r'\d+(?:\s*\d*)*', total_pages_text).group().replace(" ", ""))

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
        url = response.url
        title = response.css("h1.head::text").get()
        price_usd = self.extract_price_usd(response)
        odometer = int(response.css("div.base-information span.size18::text").re_first(r"(\d+)") or 0) * 1000
        username = self.get_user_name(response)
        car_number = response.css("span.state-num::text").get()
        car_vin = response.css("span.vin-code::text, span.label-vin::text").get()
        image_url = self.extract_image_url(response)
        datetime_create = datetime.datetime.now()
        city = self.extract_city(response)
        owners_count = self.extract_owners_count(response)
        engine_info = self.extract_engine_power(response)

        # Creating an item to store scraped data
        item = {
            'url': url,
            'title': title,
            'price_usd': price_usd,
            'odometer': odometer,
            'username': username,
            'car_number': car_number,
            'car_vin': car_vin,
            'city': city,
            'owners_count': owners_count,
            'engine_info': engine_info,
            'image_url': image_url,
            'datetime_found': datetime_create
        }

        data_hash, data_expires, data_id = self.get_data_attributes(response)
        phone_number_url = f"https://auto.ria.com/users/phones/{data_id}/?hash={data_hash}&expires={data_expires}"
        request = scrapy.Request(url=phone_number_url, callback=self.parse_phone_numbers)
        request.meta['item'] = item  # Setting 'item' value in metadata
        yield request

    def parse_phone_numbers(self, response: HtmlResponse):
        """Parse the phone numbers from the AJAX response."""
        item = response.meta['item']

        try:
            phone_data = json.loads(response.text)
            first_phone = phone_data.get('phones', [])[0]  # Get the first phone number from the list of phones
            phone_number = first_phone.get('phoneFormatted') if first_phone else None
        except Exception as e:
            self.logger.error(f"Failed to parse phone numbers: {e}")
            phone_number = None

        formatted_phone_number = self.format_phone_number(phone_number)  # Formatting the phone number
        item['phone_number'] = formatted_phone_number
        yield item

    @staticmethod
    def format_phone_number(phone_number):
        """Format the phone number into international format."""
        if phone_number:
            digits = re.sub(r'\D', '', phone_number)
            formatted_number = f"+38{digits}"
            return formatted_number
        return None

    @staticmethod
    def get_data_attributes(response: HtmlResponse):
        """Get data attributes from the page."""
        try:
            script_tag = response.xpath('//script[contains(@class, "js-user-secure")]')
            data_hash = script_tag.xpath("@data-hash").get()
            data_expires = script_tag.xpath("@data-expires").get()
            data_auto_id = response.css("body::attr(data-auto-id)").extract_first()
            return data_hash, data_expires, data_auto_id
        except Exception as e:
            raise ValueError(f"Failed to get data attributes: {e}")

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
        try:
            price_value = response.css('.price.mb-15.mhide').get()
            price_usd_pattern = r'\b(\d[\d\s]*)\s\$'
            price_usd_match = re.search(price_usd_pattern, price_value)
            if price_usd_match:
                price_usd_str = price_usd_match.group(1).replace(' ', '')
                return int(price_usd_str)
        except Exception as e:
            raise ValueError(f"Failed to extract price USD: {e}")
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
        try:
            if response.css("dd:contains('Кількість власників')"):
                owners_count = response.css("dd:contains('Кількість власників') span.argument::text").get()
            else:
                owners_count = 0
            return owners_count
        except Exception as e:
            self.logger.error(f"Failed to extract owners count: {e}")
            return None

    def extract_engine_power(self, response):
        """Extract engine power from the response."""
        selectors = [
            "dd:contains('Двигун') span.argument::text",
            "dt:contains('Двигун') + dd span::text"
        ]

        for selector in selectors:
            engine_info = response.css(selector).get()
            if engine_info:
                if engine_info:
                    return engine_info.strip()

        return None
