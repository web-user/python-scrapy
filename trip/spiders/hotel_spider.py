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
    name = "tripadvisor_hotel"

    allowed_domains = ["www.tripadvisor.com", ]

    def __init__(self, *args, **kwargs):
        # super(TripAdvisorHotelItem, self).__init__(*args, **kwargs)
        self.client = pymongo.MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DATABASE]
        self.collection = self.db[settings.MONGO_DATABASE]
        self.cursor = self.collection.find({"hotel_add": {"$exists": False}}, no_cursor_timeout=True).batch_size(1000)
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
        header = response.xpath(
            '//div[@class="ui_columns is-multiline is-mobile contentWrapper"]')
        title_container = header.xpath(
            ".//div[@class='ui_column is-12-tablet is-10-mobile hotelDescription']")
        hotel_title = title_container.xpath(
            ".//h1[@id='HEADING']/text()").get()



        # add_hot.name
        hotel_street = response.xpath(
            "//span[@class[contains(.,'street-address')]]/text()").get()
        # get url to selenium
        driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", chrome_options=options)
        sleep(1)
        driver.get(response.url)
        # wait till it loads
        sleep(3)
        try:
            next = driver.find_element_by_xpath("//div[@data-vendorname[contains(.,'Agoda')]]")
            if next:
                # click on agora url sleep 2
                next.click()
                # wait till redirect ends loads
                sleep(2)
                # switching to agoda tab
                driver.switch_to.window(driver.window_handles[1])
                agoda_url = driver.current_url
        except:
            agoda_url = "Not provided"
        driver.quit()

        hotel_country = response.xpath(
            "//span[contains(@class, 'country-name')]/text()").get(default='Thailand')
        # //*[@id="taplc_resp_hr_atf_hotel_info_0"]/div/div[2]/div/div[2]/div


        try:
            logging.debug("Post hotel_country: " + str(hotel_country))
            hotel_city = response.xpath("//span[@class[contains(.,'locality')]]/text()").get()
            address = hotel_street + hotel_city + hotel_country
        except:

            try:
                address = hotel_street + hotel_country
            except:
                add_hot = response.xpath('//script[@type="application/ld+json"]/text()').get()
                address_all = json.loads(add_hot)

                address = "{0}, {1}, {2}".format(address_all["address"]["streetAddress"],
                                       address_all["address"]["addressLocality"],
                                       address_all["address"]["addressCountry"]["name"])

        try:
            neighbourhood = response.xpath(
                "//div[@class[contains(.,'Neighborhood__name')]]/text()").extract()[0]
        except:
            neighbourhood = "null"

        hotel_description = response.xpath(
            "//div[@class[contains(.,'common-text-ReadMore__content')]]/text()").get()
        url_tripadvisor = response.url
        additional_info = response.xpath(
            "//div[@class[contains(.,'hotels-hotel-review-about-addendum-AddendumItem__item')]]")
        try:
            room_count = [i.xpath(
                ".//div[@class='hotels-hotel-review-about-addendum-AddendumItem__content--iVts5']/text()").get()
                          for i in additional_info if i.xpath(
                    ".//div[@class='hotels-hotel-review-about-addendum-AddendumItem__title--2QuyD']/text()").get() == 'NUMBER OF ROOMS'][0]
        except:
            room_count = "null"
        try:
            location_container = [i.xpath("//span[@class[contains(.,'hotels-hotel-review-about-addendum-LocationHierarchy')]]/text()") for i in response.xpath(
                "//div[@class[contains(.,'hotels-hotel-review-about-addendum-AddendumItem__item')]]")
                                  if i.xpath(".//text()").get() == 'LOCATION']
            location = [i.get() for i in location_container[0]]
        except:
            location = "No info"
        also_known_as_container = [i.xpath("//span[@class[contains(.,'hotels-hotel-review-about-addendum-HotelAliases__alias')]]/text()") for i in response.xpath(
            "//div[@class[contains(.,'hotels-hotel-review-about-addendum-AddendumItem__item')]]")
                              if i.xpath(".//text()").get() == 'ALSO KNOWN AS']
        if also_known_as_container:
            also_known_as = [i.get() for i in also_known_as_container[0]]
        else:
            also_known_as = "null"
        try:
            hotel_class = response.xpath(
                "//span[@class[contains(.,'ui_star_rating')]]/@class").re(
                r'star_(\d+)')[0]
        except:
            hotel_class = "null"

        try:
            hotel_style = [i.xpath(
                "//div[@class[contains(.,'hotels-hotel-review-about-with-photos-layout-TextItem__textitem')]]/text()").get()
                           for i in response.xpath(
                    "//div[@class[contains(.,'ui_column is-6')]]") if i.xpath(
                    "//div[@class[contains(.,'hotels-hotel-review-about-with-photos-layout-Subsection__title')]]/text()").get() == 'HOTEL STYLE'][0]

        except:
            try:
                hotel_style = [i.xpath(
                    "//div[@class[contains(.,'hotels-hotel-review-about-with-photos-layout-TextItem__textitem')]]/text()").get()
                               for i in response.xpath(
                        "//div[@class[contains(.,'ui_columns is-gapless-vertical is-mobile')]]") if i.xpath(
                        "div[@class[contains(.,'ui_column is-6')]]/div[@class[contains(.,'hotels-hotel-review-about-with-photos-layout-Subsection__title')]]/text()")[1].extract() == 'HOTEL STYLE'][0]
            except:
                hotel_style = "null"
        #all getting there places
        all_places = [b.get() for b in response.xpath(
            "//span[@class[contains(., 'hotels-hotel-review-location-NearbyTransport__name')]]/text()")]
        # all getting there icons to places
        all_icons_to_places = [b.re(r'flights|train')[0] for b in response.xpath(
            "//span[@class[contains(., 'hotels-hotel-review-location-NearbyTransport__typeIcon')]]/@class")]
        # all getting there info to places
        activities = [b.re(r'parking|activities')[0] for b in response.xpath(
            "//span[@class[contains(., 'hotels-hotel-review-location-NearbyTransport__travelIcon')]]")]
        # all getting there time
        lenght_time = [i.get() for i in response.xpath(
            "//span[@class[contains(.,'hotels-hotel-review-location-NearbyTransport__distance')]]/span/span/text()")]
        # block to connect all getting there info to one hotel
        lenght_and_time_pairs = list()
        while (lenght_time):
            a = lenght_time.pop(0)
            b = lenght_time.pop(0)
            lenght_and_time_pairs.append((a, b))
        getting_there = list(
            zip(all_places, ["airport" if i == 'flights' else i for i in all_icons_to_places],
                ["car" if i == 'parking' else "by walk" for i in activities],
                lenght_and_time_pairs))
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
                i.get() for i in response.xpath(
                    "//div[@class[contains(.,'hotels-review-list-parts-ReviewFilters__filters_wrap')]]/div/div/ul/li/span[2]/text()")]
        except:
            traveler_rating_five, traveler_rating_four, traveler_rating_three, traveler_rating_two, traveler_rating_one = ['null' for _ in range(5)]
        certificate = response.xpath(
            "//div[@class[contains(.,'hotels-hotel-review-about-with-photos-Awards__award_text')]]/text()").get()

        review_item = dict()

        review_item['review_tripadvisor'] = []


        hotel_item = HotelItem()
        hotel_item['updated_at'] = datetime.datetime.now().timestamp()
        hotel_item['created_at'] = datetime.datetime.now().timestamp()
        hotel_item['name'] = hotel_title
        hotel_item['address'] = address
        hotel_item['neighbourhood'] = neighbourhood
        hotel_item['hotel_description'] = hotel_description
        hotel_item['url_tripadvisor'] = url_tripadvisor
        hotel_item['room_count'] = room_count
        hotel_item['hotel_class'] = hotel_class
        hotel_item['hotel_style'] = hotel_style
        hotel_item['getting_there'] = getting_there
        hotel_item['url_agoda'] = agoda_url
        hotel_item['also_known_as'] = also_known_as
        hotel_item['location'] = location
        hotel_item['reviews'] = review_item
        hotel_item['hotel_add'] = 1


        yield hotel_item
