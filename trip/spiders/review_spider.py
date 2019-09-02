import datetime
import scrapy
import pymongo
from scrapy.xlib.pydispatch import dispatcher
from scrapy_splash import SplashRequest
from selenium import webdriver
from scrapy import signals

from trip.items import ReviewItem, HotelItem
from trip.proxy import GimmeProxy
from trip import settings

# options to work selenium without GUI
options = webdriver.ChromeOptions()
options.add_argument("headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")


class TripAdvisorReview(scrapy.Spider):
    name = "tripadvisor_review"

    start_urls = [
        "https://www.tripadvisor.com.sg/Hotel_Review-g293916-d301388-Reviews-Montien_Hotel_Bangkok-Bangkok.html"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dispatcher.connect(self.spider_closed, signals.spider_closed)


        self.proxy_suplier = GimmeProxy()
        # self.driver = webdriver.Chrome(chrome_options=options)
        self.client = pymongo.MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DATABASE]
        self.collection = self.db[settings.MONGO_DATABASE]
        self.cursor = self.collection.find({"hotel_add": {"$exists": True}}, no_cursor_timeout=True).batch_size(500000)
        self.city = kwargs.get('city')
        self.status_requests = ''
        self.count_url_cursor = 0

    def spider_closed(self, spider):
      # second param is instance of spder about to be closed.
      print("spider_closed:  ")


    def start_requests(self):

        print(self.cursor.count())

        for url in self.cursor:
            # SplashRequest need to load whole page before scraping
            yield scrapy.Request(url=url['url_tripadvisor'], callback=self.parse_review_page,
                                 meta={'splash': {'args': {'wait': 4, 'new_url': url['url_tripadvisor']}},})
        self.cursor.close()




    def parse_review_page(self, response):
        new_url = response.meta.get('splash').get('args').get('new_url')
        # get review item from review list page
        review_page = response.xpath(
            "//div[@class[contains(.,'hotels-review-list-parts-ReviewTitle__reviewTitle')]]/a/@href").extract()
        author_names = response.xpath(
            "//a[@class[contains(.,'ui_header_link social-member-event-MemberEventOnObjectBlock__member')]]/text()").extract()[:5]
        author_locations = response.xpath(
            "//span[@class[contains(.,'default social-member-common-MemberHometown__hometown')]]/text()").extract()[:5]
        # author_contributions_and_votes = response.xpath(
        #     "//span[@class[contains(.,'social-member-MemberHeaderStats__bold')]]/text()").extract()[:10]
        posted_at_list = response.xpath(
            "//div[@class[contains(.,'ocial-member-event-MemberEventOnObjectBlock__event_type')]]/span/text()").extract()[:5]
        # // div[ @ data - vendorname[contains(., 'Agoda')]

        # .xpath(
        #     ".//div[@class='hotels-review-list-parts-SingleReview__reviewContainer']").get()

        voice_new = dict()
        voice_new['author_contribution'] = list()
        voice_new['author_vote'] = list()

        for sel in response.xpath("//div[@class[contains(.,'social-member-MemberHeaderStats__event_info')]]"):
            try:

                voice_new['author_contribution'].append(sel.xpath("span[@class[contains(.,'social-member-MemberHeaderStats__stat_item')]]/span/span[@class[contains(.,'social-member-MemberHeaderStats__bold')]]/text()")[0].extract())
            except:
                voice_new['author_contribution'].append('0')


            try:
                voice_new['author_vote'].append(sel.xpath(
                    "span[@class[contains(.,'social-member-MemberHeaderStats__stat_item')]]/span/span[@class[contains(.,'social-member-MemberHeaderStats__bold')]]/text()")[
                    1].extract())
            except:
                voice_new['author_vote'].append('0')

        if review_page:
            # going to all review_pages
            for i in range(len(review_page)):

                url = response.urljoin(review_page[i])
                author_name = author_names[i]
                try:
                    author_location = author_locations[i]
                except:
                    author_location = "null"

                author_contribution = voice_new['author_contribution'][i]
                author_vote = voice_new['author_vote'][i]
                posted_at = posted_at_list[:5][i]
                # add proxy to a request
                yield scrapy.Request(url, self.parse_review,
                                    meta={'splash': {'args': {'wait': 4,}},'author_name': author_name,
                                          'author_location': author_location,
                                          'author_contribution': author_contribution,
                                          'author_vote': author_vote,
                                          'posted_at': posted_at,
                                          'url_hotel': response.url,
                                          "new_url": new_url})

        next_page = response.xpath('//a[@class="ui_button nav next primary "]/@href').extract()
        if next_page:
            url = response.urljoin(next_page[-1])
            yield SplashRequest(url, self.parse_review_page, args={'wait': 4, "new_url": new_url},)

    def parse_review(self, response):
        from time import sleep
        hotel_item = HotelItem()
        item = ReviewItem()
        title = response.xpath(".//h1[@id='HEADING']/text()").get()
        date_of_stay = response.xpath(
            "//div[@class[contains(.,'prw_rup prw_reviews_stay_date_hsx')]]/text()").get()
        review = response.xpath("//span[@class[contains(.,'fullText ')]]/text()").get()
        author_rating = response.xpath(
            "//span[@class[contains(.,'ui_bubble_rating')]]/@class").re(
            r'bubble_(\d+)')[0]
        item['created_at'] = datetime.datetime.now().timestamp()
        item['author_name'] = response.meta['author_name']
        item['author_location'] = response.meta['author_location']
        item['author_contributions'] = response.meta['author_contribution']
        item['helpful_votes'] = response.meta['author_vote']
        item['posted_at'] = response.meta['posted_at']
        item['url_review'] = response.url

        hotel_item['url_tripadvisor'] = response.meta['new_url']

        if not title:
            try:
                # old reviews needs to be load before it scrapes. That's why selenium is used
                driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", chrome_options=options)
                driver.get(response.url)
                # wait till it loads
                sleep(3)
                title = driver.find_element_by_xpath(".//h1[@id='HEADING']").text
            except:
                title = ''
        if not review:
            try:
                # old reviews needs to be load before it scrapes. That's why selenium is used
                driver = webdriver.Chrome(executable_path="/usr/bin/chromedriver", chrome_options=options)
                driver.get(response.url)
                # wait till it loads
                sleep(3)
                review = driver.find_element_by_xpath("//span[@class[contains(.,'fullText')]]").text
                if not review:
                    review = driver.find_element_by_xpath("//span[@class[contains(.,'summaryText')]]").text
            except:
                review = ''
        item['title'] = title
        item['date_of_stay'] = date_of_stay
        item['review'] = review
        item['author_rating'] = author_rating

        hotel_item['reviews_if'] = '1'
        hotel_item['reviews'] = item

        yield hotel_item
