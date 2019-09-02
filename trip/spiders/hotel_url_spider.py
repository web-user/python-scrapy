import scrapy

from trip.items import HotelItem


class TripAdvisorHotelItem(scrapy.Spider):
    name = "tripadvisor_hotel_url"

    allowed_domains = ["www.tripadvisor.com", ]

    def __init__(self, *args, **kwargs):
        super(TripAdvisorHotelItem, self).__init__(*args, **kwargs)

        self.start_urls = [kwargs.get('start_url')]
        self.city = kwargs.get('city')
        self.status_requests = ''

    def start_requests(self):
        for url in self.start_urls:
            # SplashRequest need to load whole page before scraping
            yield scrapy.Request(url=url, callback=self.parse_hotel_page)

    def parse_hotel_page(self, response):
        hotels = response.xpath("//div[@class='prw_rup prw_meta_hsx_responsive_listing ui_section listItem']"
                                "/div/div[@data-index]")

        for hotel in hotels:
            hotel_detail = hotel.xpath(".//div[@class='listing_title']/a/@href").extract_first()
            hotel_url = 'https://www.tripadvisor.com' + hotel_detail
            yield scrapy.Request(url=hotel_url, callback=self.parse_hotel_url)

        next_button = response.xpath("//link[@rel='next']/@href").extract()[0]
        url_next = 'https://www.tripadvisor.com' + next_button
        if next_button:
            yield scrapy.Request(url=url_next, callback=self.parse_hotel_page)

    def parse_hotel_url(self, response):
        hotel_item = HotelItem()
        hotel_item['url_tripadvisor'] = response.url
        hotel_item['city'] = self.city

        yield hotel_item