# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class Paper(Item):

    conf = Field()  # The conference name for the current paper
    title = Field()
    authors = Field()
    abstract = Field()
    code_url = Field()
    citation_count = Field() # The number of citations.
    matched_queries = Field() # The matched queries.
    pdf_url = Field()  # The PDF url for the paper.
    categories = Field()
    concepts = Field()
    doi = Field()
