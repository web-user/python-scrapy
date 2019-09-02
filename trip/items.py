# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HotelRatingItem(scrapy.Item):
    updated_at = scrapy.Field()
    added_at = scrapy.Field()
    ranking = scrapy.Field()  #447 of 995 Hotels in Bangkok
    rating_overall = scrapy.Field()
    reviews_count = scrapy.Field()
    locating_rating = scrapy.Field()
    cleaniness_rating = scrapy.Field()
    service_rating = scrapy.Field()
    url_tripadvisor = scrapy.Field()
    value_rating = scrapy.Field()
    traveler_rating_five = scrapy.Field() #float
    traveler_rating_four = scrapy.Field() #float
    traveler_rating_three = scrapy.Field() #float
    traveler_rating_two = scrapy.Field() #float
    traveler_rating_one = scrapy.Field() #float
    cert_excellence = scrapy.Field()
    rating_add = scrapy.Field()


class ReviewItem(scrapy.Item):
    created_at = scrapy.Field()
    author_name = scrapy.Field()
    author_location = scrapy.Field()
    date_of_stay = scrapy.Field()
    url_tripadvisor = scrapy.Field()
    author_rating = scrapy.Field()
    author_contributions = scrapy.Field()
    helpful_votes = scrapy.Field()
    posted_at = scrapy.Field() #date
    review = scrapy.Field()
    url_review = scrapy.Field()
    title = scrapy.Field()


class HotelItem(scrapy.Item):
    updated_at = scrapy.Field()
    created_at = scrapy.Field()
    name = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    neighbourhood = scrapy.Field()
    hotel_description = scrapy.Field()
    url_tripadvisor = scrapy.Field()
    url_agoda = scrapy.Field()
    room_count = scrapy.Field()
    hotel_class = scrapy.Field()
    hotel_style = scrapy.Field()
    getting_there = scrapy.Field()
    also_known_as = scrapy.Field()
    location = scrapy.Field()
    ratings = scrapy.Field()
    reviews = scrapy.Field()
    reviews_if = scrapy.Field()
    hotel_add = scrapy.Field()
