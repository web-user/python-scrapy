import datetime
import json
import scrapy
import pymongo

from scrapy_splash import SplashRequest
from selenium import webdriver
from time import sleep

from trip.items import HotelItem, HotelRatingItem
from trip import settings

import logging
from scrapy.utils.log import configure_logging

# options to work selenium without GUI
options = webdriver.ChromeOptions()
options.add_argument("headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

configure_logging(install_root_handler=False)
logging.basicConfig(
    filename='logging.txt',
    format='%(levelname)s: %(message)s',
    level=logging.ERROR
)


class TripAdvisorHotelItem(scrapy.Spider):
    handle_httpstatus_list = [404]
    name = "tripadvisor_rating"

    allowed_domains = ["www.tripadvisor.com", ]

    def __init__(self, *args, **kwargs):
        # super(TripAdvisorHotelItem, self).__init__(*args, **kwargs)
        self.client = pymongo.MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DATABASE]
        self.collection = self.db[settings.MONGO_DATABASE]
        self.cursor = self.collection.find({"hotel_add": {"$exists": True}}, no_cursor_timeout=True).batch_size(1000)
        self.city = kwargs.get('city')
        self.status_requests = ''

    def start_requests(self):
        print(self.cursor.count())

        for url in self.cursor:
            # SplashRequest need to load whole page before scraping
            yield SplashRequest(url=url['url_tripadvisor'], callback=self.parse_hotel,
                                args={'wait': 4},)
        self.cursor.close()

    def parse_hotel(self, response):
        # In future parse start page with all hotels in the city

        url_tripadvisor = response.url

        # get url to selenium


        ranking = response.xpath("//b[@class[contains(.,'rank')]]/text()").get()

        try:
            rating_overall = response.xpath(
                "//a[@class[contains(.,'hotels-hotel-review-about-with-photos-Reviews__bubbleRating')]]/span/@class").re(
                r'bubble_(\d+)')[0]
        except IndexError:
            rating_overall = "null"
        try:
            reviews_count = response.xpath(
                "//span[@class[contains(.,'hotels-hotel-review-about-with-photos-Reviews__seeAllReviews')]]/text()").get().split()[0]
        except:
            reviews_count = "null"
        try:
            locating_rating = \
                response.css(
                    '#ABOUT_TAB .hotels-hotel-review-about-with-photos-Reviews__subratings--33a7M .ui_bubble_rating').xpath(
                    "@class").re(
                    r'bubble_(\d+)')[0]
        except IndexError:
            locating_rating = "null"
        try:
            cleaniness_rating = \
                response.css(
                    '#ABOUT_TAB .hotels-hotel-review-about-with-photos-Reviews__subratings--33a7M .ui_bubble_rating').xpath(
                    "@class").re(
                    r'bubble_(\d+)')[1]
        except IndexError:
            cleaniness_rating = "null"
        try:
            service_rating = \
                response.css(
                    '#ABOUT_TAB .hotels-hotel-review-about-with-photos-Reviews__subratings--33a7M .ui_bubble_rating').xpath(
                    "@class").re(
                    r'bubble_(\d+)')[2]
        except IndexError:
            service_rating = "null"
        try:
            value_rating = \
                response.css(
                    '#ABOUT_TAB .hotels-hotel-review-about-with-photos-Reviews__subratings--33a7M .ui_bubble_rating').xpath(
                    "@class").re(
                    r'bubble_(\d+)')[3]
        except IndexError:
            value_rating = "null"
        try:
            traveler_rating_five, traveler_rating_four, traveler_rating_three, traveler_rating_two, traveler_rating_one = [
                i.xpath(
                    "//span[@class[contains(.,'hotels-review-list-parts-ReviewRatingFilter__row_num')]]/text()").extract() for i in response.xpath(
                    "//ul[@class[contains(.,'hotels-review-list-parts-ReviewFilter__filter_table')]]")][0]
        except:
            traveler_rating_five, traveler_rating_four, traveler_rating_three, traveler_rating_two, traveler_rating_one = ['null' for _ in range(5)]
        certificate = response.xpath(
            "//div[@class[contains(.,'hotels-hotel-review-about-with-photos-Awards__award_text')]]/text()").get()

        hotel_item = HotelItem()
        hotel_item['url_tripadvisor'] = url_tripadvisor


        item = HotelRatingItem()
        item['updated_at'] = datetime.datetime.now().timestamp()
        item['ranking'] = ranking
        item['rating_overall'] = rating_overall
        item['reviews_count'] = reviews_count
        item['cleaniness_rating'] = cleaniness_rating
        item['service_rating'] = service_rating
        item['value_rating'] = value_rating
        item['locating_rating'] = locating_rating
        item['traveler_rating_five'] = traveler_rating_five
        item['traveler_rating_four'] = traveler_rating_four
        item['traveler_rating_three'] = traveler_rating_three
        item['traveler_rating_two'] = traveler_rating_two
        item['traveler_rating_one'] = traveler_rating_one
        item['cert_excellence'] = bool(certificate)
        item['rating_add'] = 1

        hotel_item['ratings'] = item

        yield hotel_item
