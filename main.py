from scrapy import cmdline
cmdline.execute('scrapy crawl tripadvisor_hotel_url -a start_url=https://www.tripadvisor.com.sg/Hotels-g293916-Bangkok-Hotels.html -a city=Bangkok'.split())