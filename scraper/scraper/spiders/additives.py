import scrapy
import logging
class AdditivesSpider(scrapy.Spider):
    name = "addictives"
    allowed_domains = ["www.cspinet.org"]
    start_urls = ["https://www.cspinet.org/page/chemical-cuisine-food-additive-safety-ratings#ratings/"]
    def parse(self, response):
        rows =response.xpath("/html/body/div[1]/main/article/article[4]/div/div[1]/div[2]/div[4]/table/tbody/tr")
        for row in rows:
            # Extract the name using the provided XPath
            name = row.xpath("./td[1]/span/span[2]/a/text()").get()  # Adjusted for name in specific location
            href = row.xpath("./td[1]/span/span[2]/a/@href").get()   # Extract href

            logging.info(f"Ingredient: {ingredient}, URL: {href}")
            # Transform the URL from '/node/xxxx' to '/article/name'
            full_url = f"https://www.cspinet.org/article/{ingredient.replace(' ','-').lower()}"
            yield scrapy.Request(full_url,callback=self.parse_detail,meta={'ingredient':ingredient})
    def parse_detail(self, response):
        #Extract data from ech page 
        ingredient = response.meta['ingredient']
        purpose = response.xpath("//strong[contains(text(), 'Purpose:')]/following-sibling::text()").get()
        health_concerns = response.xpath("//strong[contains(text(), 'Health Concerns:')]/following-sibling::text()").get()

       

        purpose = purpose.strip() if purpose else 'No purpose found'
        health_concerns = health_concerns.strip() if health_concerns else 'No health concerns found'


        yield {
            'ingredient': ingredient,
            'purpose': purpose,
            'health_concerns': health_concerns
        }
        
    
            
            
        
     
