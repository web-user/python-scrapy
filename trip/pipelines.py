# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
import pymongo


class TripPipeline(object):

    collection_name = 'trip_review_hotel'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE')
            )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.collection_name = self.mongo_db

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        if "url_tripadvisor" in item:
            url_tripadvisor = item.pop("url_tripadvisor")
            rating_add = item.get('ratings').get('rating_add') if item.get('ratings') else None

            if "reviews_if" in item:
                if not [i for i in self.db[self.collection_name].find(
                        {"reviews.review_tripadvisor.url_review": item['reviews']['url_review']})]:
                    self.db[self.collection_name].update_one({"url_tripadvisor": url_tripadvisor}, {
                        "$push": {"reviews.review_tripadvisor": {"$each": [item['reviews']]}}})
                    logging.debug("Post changed in MongoDB")
            else:
                # mycount = self.db[self.collection_name].find( { "$and": [ {"url_tripadvisor": url_tripadvisor}, { "ratings.ratings_tripadvisor": { "$exists": "true", "$ne": [] } } ] } )
                # db.doc.find({'nums': { $gt: []}}).hint({_id: 1}).count()
                print(self.db[self.collection_name].find( {"url_tripadvisor": url_tripadvisor,  "ratings.ratings_tripadvisor": { "$exists": True, "$ne": [] } } ).count())
                if rating_add and self.db[self.collection_name].find( {"url_tripadvisor": url_tripadvisor,  "ratings.ratings_tripadvisor": { "$exists": True, "$ne": [] } } ).count() > 0:
                    logging.debug("MongoDB changed add to list")
                    self.db[self.collection_name].update_one({"url_tripadvisor": url_tripadvisor}, {
                        "$push": {"ratings.ratings_tripadvisor": {"$each": [item['ratings']]}}})

                else:
                    logging.debug("MongoDB changed")

                    if item.get('ratings') is not None:
                        print(" ratings ASAS")
                        ratings_item = dict()
                        ratings_item['ratings_tripadvisor'] = []
                        ratings_item['ratings_tripadvisor'].append(item['ratings'])
                        item['ratings'] = ratings_item
                    self.db[self.collection_name].update_one({"url_tripadvisor": url_tripadvisor}, {"$set": item}, upsert=True)

        return item
