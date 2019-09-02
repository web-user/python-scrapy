Project to scrapy Tripadvisor.com

Consist of three spiders:
- tripadvisor_hotel_url - first run this spider, it will scrape all urls from target city
- tripadvisor_hotel scrape main hotel info
- tripadvisor_rating scrape main hotel rating info
- tripadvisor_review scrape all reviews from hotel page

Project uses:
-python 3v
-mongodb 4.0
-pip3
-chromdriver (for selenium)

to launch spider:
   'scrapy crawl <spider_name> -a start_url=https://www.tripadvisor.com.sg/Hotels-g293916-Bangkok-Hotels.html -a city=Bangkok'

all spider stores data in mongodb