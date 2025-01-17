import scrapy
import re

# To remove consecutive space and special formatting characters like \n
import inspect

# We import the Paper item we defined in `items.py`.
from ..items import Paper

import json

class BaseSpider(scrapy.Spider):

    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)

        # Save the conference and keyword arguments.
        years = kwargs.get('years').split(',')
        queries = kwargs.get('queries')
        nocrossref = kwargs.get('nocrossref')

        # Remove repeated input
        wanted_conf = []
        for year in years:
            if year not in wanted_conf:
                wanted_conf.append(self.name.upper() + year)
        self.wanted_conf = wanted_conf
        self.queries = queries

        # If not call Crossref API
        if not nocrossref:
            self.crossref = True

    def parse(self, response):
        raise NotImplementedError

    @staticmethod
    def extract_data(response):
        raise NotImplementedError

    def parse_paper(self, response):
        # Deliver the scraped item to `pipelines.py`.
        paper = Paper()

        title, pdf_url, authors, abstract = self.extract_data(response)
        conf = response.meta['conf']

        if abstract is not None:
            abstract = abstract.replace("\n", " ")

        paper["conf"] = conf
        paper["title"] = title
        paper["pdf_url"] = pdf_url
        paper["authors"] = authors
        paper["abstract"] = abstract

        yield paper


class CvprScrapySpider(BaseSpider):
    # The name differentiate this crawler class against others. Try to
    # use unique name for each crawler class.

    name = 'cvpr'

    # Where to start the crawling.
    start_urls = [
        "https://openaccess.thecvf.com/menu",
    ]

    from_dblp = False

    def parse(self, response):
        # response contains all the data scraped from the start_url, including the html source code.

        # Here we loop over the target conferences, which are CVPRs in different years.
        # We manually define the target url according to the homework we did on the target website.
        # Then, we send a request to the new target url, and call another method to process it.
        for conf in self.wanted_conf:
            url = response.url.split("menu")[0] + conf.upper()
            meta = {"conf": conf}

            # For conferences in 2018 onward, the html elements contain the list of days, instead of the paper list directly
            if conf[4:] >= "2018":

                # Navigate to the day list
                yield scrapy.Request(url, callback=self.parse_day, meta = meta)
            else:

                # Navigate to the paper list
                yield scrapy.Request(url, callback=self.parse_paper_list, meta = meta)

    def parse_day(self, response):
        meta = {"conf": response.meta['conf']}
        # Now we navigate to the Day page.
        # Get all the days listed there using the xpath.
        # extract() generates a list of all matched elements.
        day_url_list = response.xpath("//div[@id='content']/dl/dd/a/@href").extract()

        # Traverse every day
        for day_url in day_url_list:

            # Exclude the Day-aLL hyperlink to avoid redundancy.
            if "day=all" in day_url:
                continue

            # For each day, we once again manually generate the new url, visit it,
            # and call yet another method to process it.
            url = response.urljoin(day_url)
            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        # Now we have all the papers.
        paper_url_list = response.xpath("//div[@id='content']/dl/dt[@class='ptitle']/a/@href").extract()

        # We loop all the paper url, visit them, and call the `parse_paper` method to process.
        for paper_url in paper_url_list:
            url = response.urljoin(paper_url)

            # for each paper, navigate to its detail page
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):
        # This function specifies how to extract the relevance from the paper detail page of the OpenCVF website.
        # Use the xpath with trial-and-error to rid of any exceptions.

        # Correct the bug caused by slight difference on the elements

        title = inspect.cleandoc(response.xpath("//div[@id='papertitle']/text()").get())
        pdf_url = response.urljoin(response.xpath("//div[@id='content']/dl/dd/a[1]/@href").get())
        authors = inspect.cleandoc(response.xpath("//div[@id='authors']/b/i/text()").get())
        abstract = inspect.cleandoc(response.xpath("//div[@id='abstract']/text()").get())

        return title, pdf_url, authors, abstract


class IccvScrapySpider(CvprScrapySpider):
    name = 'iccv'
    start_urls = [
        "https://openaccess.thecvf.com/menu",
    ]

    from_dblp = False

class EccvScrapySpider(CvprScrapySpider):
    name = 'eccv'
    start_urls = [
        "https://www.ecva.net/papers.php",
    ]
    base_url = "https://www.ecva.net"

    from_dblp = False

    def parse(self, response):


        for conf in self.wanted_conf:
            year = conf[4:]
            paper_url_list = response.xpath(f"//button[contains(text(), {year})]/following-sibling::div[1]/div[@id='content']/dl/dt/a/@href").extract()
            meta = {"conf": conf}
            for paper_url in paper_url_list:
                url = self.base_url + "/" + paper_url
                yield scrapy.Request(url, callback=self.parse_paper, meta=meta)


class NipsScrapySpider(BaseSpider):
    name = 'nips'
    start_urls = [
        "https://papers.nips.cc/",
    ]

    from_dblp = False

    def parse(self, response):

        for conf in self.wanted_conf:
            conf_url = "/paper/" + conf[4:]
            year = conf[4:]
            url = response.urljoin(conf_url)
            meta = {"conf": conf}

            if year == "2023":
                url = response.urljoin("https://nips.cc" + "/Conferences/" + conf[4:] + "/Schedule")
                yield scrapy.Request(url, callback=self.parse_paper_list_for_openreview, meta=meta)
            else:
                yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list_for_openreview(self, response):
        meta = {"conf": response.meta['conf']}
        paper_id_list = response.xpath(
            "//div[@id='base-main-content']/div[2]/div[3 < position()]/div[@class='maincard narrower poster']/@id").extract()

        for paper_id in paper_id_list:
            url = response.url + "?showEvent=" + paper_id.split("_")[1]

            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)
    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        paper_url_list = response.xpath("//div[@class='container-fluid']/div[@class='col']/ul/li/a/@href").extract()

        for paper_url in paper_url_list:
            url = response.urljoin(paper_url)
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):

        if response.meta['conf'] == "NIPS2023":
            title = inspect.cleandoc(
                response.xpath("//div[@id='base-main-content']/div[2]/div[@id=$pid]/div[@class='maincardBody']/text()",
                               pid="maincard_" + response.url.split("=")[1]).get())
            authors = inspect.cleandoc(
                ",".join(response.xpath("//div[@id='base-main-content']/div[2]/button/text()").extract())).replace("»",
                                                                                                                   "")
            abstract = inspect.cleandoc(response.xpath(
                "//div[@class='abstractContainer']/p/text() | //div[@class='abstractContainer']/text() | //div[@class='abstractContainer']/span/text()").get())

            paper_id = response.xpath("//div[@class='maincard narrower poster']/@id").get()

            pdf_openreview_url = response.xpath(
                "//div[@id=$pid]//a[contains(string(), 'OpenReview') or contains(string(), 'Paper')]/@href",
                pid=paper_id).get()
            pdf_url = pdf_openreview_url.replace("forum", "pdf")

        else:
            title = inspect.cleandoc(response.xpath("//div[@class='col']/h4/text()").get())

            authors = inspect.cleandoc(response.xpath("//div[@class='col']/p[position()=2]/i/text()").get())

            try:
                abstract = inspect.cleandoc(response.xpath("//div[@class='col']/p[position()=4]/text()").get())
            except:
                abstract = inspect.cleandoc(response.xpath(
                    "//div[@class='col']/p[position()=3]/text() | //div[@class='col']/p[position()=3]/span/text()").get())

            pdf_url = response.urljoin(response.xpath("//div[@class='col']/div/a[text()='Paper']/@href").get())

        return title, pdf_url, authors, abstract


# class AaaiScrapySpider(BaseSpider):
#     name = 'aaai'
#     start_urls = [
#         "https://aaai.org/aaai-publications/aaai-conference-proceedings/",
#     ]
#
#     from_dblp = False
#
#     def parse(self, response):
#
#         for conf in self.wanted_conf:
#             meta = {"conf": conf}
#             year = conf[4:].lower()
#             url = response.xpath(f"//p[contains(@class, 'link-block')]/a[contains(text(), '{year}')]/@href").get()
#             yield scrapy.Request(url, callback=self.parse_track_list, meta=meta)
#
#     def parse_track_list(self, response):
#         meta = {"conf": response.meta['conf']}
#         paper_url_list = response.xpath("//ul[@class='cmp_article_list articles']/li//h3[@class='title']/a/@href").extract()
#
#         for paper_url in paper_url_list:
#             url = response.urljoin(paper_url)
#             yield scrapy.Request(url, callback=self.parse_paper, meta=meta)
#
#
#     @staticmethod
#     def extract_data(response):
#
#         title = inspect.cleandoc(response.xpath("//article[contains(@class, 'obj_article_details')]/h1[@class='page_title']/text()").get())
#         authors = response.xpath("//ul[@class='authors']/li/span[@class='name']/text()").getall()
#         authors = ",".join([author.strip() for author in authors])
#
#         abstract = response.xpath("//section[@class='item abstract']/text()").getall()
#         abstract = " ".join([text.strip() for text in abstract])
#
#         pdf_url = response.xpath("//a[contains(@class, 'obj_galley_link pdf')]/@href").get()
#
#         return title, pdf_url, authors, abstract


class IjcaiScrapySpider(BaseSpider):
    name = 'ijcai'
    start_urls = [
        "https://www.ijcai.org/all_proceedings",
    ]

    from_dblp = False

    def parse(self, response):
        for conf in self.wanted_conf:
            meta = {"conf": conf}
            url = "https://www.ijcai.org/proceedings/" + conf[5:]
            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        paper_url_list = response.xpath("//div[@class='paper_wrapper']/div[@class='details']/a[2]/@href").extract()

        for paper_url in paper_url_list:
            url = response.urljoin(paper_url)
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):

        title = inspect.cleandoc(response.xpath("//div[@class='row'][1]/div/h1/text()").get())

        authors = inspect.cleandoc(response.xpath("//div[@class='row'][1]/div/h2/text()").get())
        abstract = inspect.cleandoc(response.xpath("//div[@class='row'][3]/div/text()").get())
        pdf_url = response.xpath("//div[@class='btn-container']/a/@href").get()

        return title, pdf_url, authors, abstract


class InterspeechScrapySpider(BaseSpider):
    name = 'interspeech'
    start_urls = [
        "https://www.isca-archive.org/index.html",
    ]

    base_url = "https://www.isca-archive.org/"

    from_dblp = False

    def parse(self, response):
        for conf in self.wanted_conf:
            meta = {"conf": conf}
            year = conf[-4:]
            url = f"{self.base_url}/interspeech_{year}/index.html"
            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        paper_url_list = [u for u in response.xpath("//a[@class='w3-text']/@href").extract() if not u.startswith("#")]

        for paper_url in paper_url_list:
            url = response.url.replace("index.html", paper_url)
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):

        title = inspect.cleandoc(response.xpath("//div[@id='global-info']/h3[@class='w3-center']/text()").get())

        authors = inspect.cleandoc(response.xpath("//div[@id='global-info']/h5[@class='w3-center']/text()").get())
        abstract = inspect.cleandoc(response.xpath("//div[@id='abstract']/p/text()").get())
        pdf_url = response.url.replace(response.url[-4:], "pdf")

        return title, pdf_url, authors, abstract


class IclrScrapySpider(BaseSpider):
    name = 'iclr'
    start_urls = [
        "https://openreview.net/group?id=ICLR.cc&referrer=%5BHomepage%5D(%2F)",
    ]

    from_dblp = False

    def parse(self, response):

        GET_dict = {
            "2024": {
                "GET": "https://api2.openreview.net/notes?content.venue=ICLR 2024 {session}&details=replyCount,presentation&domain=ICLR.cc/2024/Conference&limit=1000&offset={offset}",
                "sessions": ["oral", "spotlight", "poster"],
                "total_paper": 3000
            },
            "2023": {
                "GET": "https://api.openreview.net/notes?content.venue=ICLR+2023+{session}25&details=replyCount&offset={offset}&limit=1000&invitation=ICLR.cc%2F2023%2FConference%2F-%2FBlind_Submission",
                "sessions": ["notable+top+5%", "notable+top+25%", "poster"],
                "total_paper": 3000
                },
            "2022":{
                "GET": "https://api.openreview.net/notes?content.venue=ICLR 2022 {session}&details=replyCount&offset={offset}&limit=1000&invitation=ICLR.cc/2022/Conference/-/Blind_Submission",
                "sessions": ["Spotlight", "Oral", "Poster"],
                "total_paper": 3000
            },
            "2021": {
                "GET": "https://api.openreview.net/notes?invitation=ICLR.cc/2021/Conference/-/Blind_Submission&details=replyCount,invitation,original,directReplies&limit=1000&offset={offset}",
                "sessions": ["Blind_Submission"],
                "total_paper": 3000
            },
            "2020": {
                "GET": "https://api.openreview.net/notes?invitation=ICLR.cc/2020/Conference/-/{session}&details=replyCount,invitation,original,directReplies&limit=1000&offset={offset}",
                "sessions": ["Blind_Submission"],
                "total_paper": 2000
            },
            "2019": {
                "GET": "https://api.openreview.net/notes?invitation=ICLR.cc/2019/Conference/-/{session}&details=replyCount,invitation,original,directReplies&limit=1000&offset={offset}",
                "sessions": ["Blind_Submission"],
                "total_paper": 1000
            },
            "2018": {
                "GET": "https://api.openreview.net/notes?details=replyCount,original,invitation&offset={offset}&limit=1000&invitation=ICLR.cc/2018/Conference/-/{session}",
                "sessions": ["Blind_Submission"],
                "total_paper": 1000
            },
            "2017": {
                "GET": "https://api.openreview.net/notes?content.venue=ICLR+2017+Poster&details=replyCount&offset=0&limit=25&invitation=ICLR.cc%2F2017%2Fconference%2F-%2Fsubmission",
                "sessions": ["Poster", "Oral"],
                "total_paper": 1000
            }
        }

        for conf in self.wanted_conf:
            year = conf[4:]

            if not year in GET_dict:
                continue

            get_request = GET_dict[year]["GET"]
            sessions = GET_dict[year]["sessions"]
            total_paper = GET_dict[year]["total_paper"]
            num_papers = 1000

            for session in sessions:
                offset = 0
                while offset <= total_paper:
                    url = get_request.format(session=session, offset=offset)
                    yield scrapy.Request(url, callback=self.parse_paper_list, meta={"conf": conf})
                    offset += num_papers



    def parse_paper_list(self, response):

        received_data = json.loads(response.text)

        for item in received_data['notes']:

            conf = response.meta['conf']
            year = conf[4:]
            # If the bibtex starts with misc, it means the paper was rejected.
            if year <= "2023" and "_bibtex" in item['content'] and item['content']['_bibtex'].startswith("@misc"):
                continue

            paper = Paper()
            title, pdf_url, authors, abstract = self.extract_data(item, year)

            abstract =abstract.replace("\n", " ")

            paper["conf"] = conf
            paper["title"] = title
            paper["pdf_url"] = pdf_url
            paper["authors"] = authors
            paper["abstract"] = abstract

            yield paper


    @staticmethod
    def extract_data(item, year):

        if year <= "2023":
            title = inspect.cleandoc(item['content']['title'])
            authors = inspect.cleandoc(",".join(item['content']['authors']))
            abstract = inspect.cleandoc(item['content']['abstract'])
            pdf_id = item['content']['pdf']
        else:
            title = inspect.cleandoc(item['content']['title']['value'])
            authors = inspect.cleandoc(",".join(item['content']['authors']['value']))
            abstract = inspect.cleandoc(item['content']['abstract']['value'])
            pdf_id = item['content']['pdf']['value']


        pdf_url =  "https://openreview.net" + pdf_id
        return title, pdf_url, authors, abstract


class IcmlScrapySpider(BaseSpider):
    name = 'icml'
    start_urls = [
        "https://icml.cc/Downloads",
    ]

    from_dblp = False

    def parse(self, response):
        for conf in self.wanted_conf:
            meta = {"conf": conf}
            url = response.urljoin(response.url + "/" + conf[4:])
            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        paper_href_list = response.xpath("//div[@class='list_html']/ul/li/a/@href").extract()

        for paper_href in paper_href_list:
            url = response.urljoin("https://icml.cc/" + paper_href)

            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):

        paper_type = inspect.cleandoc(response.xpath("//div[@class='card-header']/h3[@class='text-center ']/text()").get())

        if paper_type == "Workshop":
            return None

        title = inspect.cleandoc(response.xpath("//div[@class='card-header']/h2/text()").get())
        authors = inspect.cleandoc(response.xpath("//div[@class='card-header']/h2/following-sibling::*[1]/text()").get()).replace(" · ", ",")
        abstract = inspect.cleandoc(" ".join(response.xpath("//div[@id='abstract_details']//div[@id='abstractExample']//text()").getall()))
        abstract = re.sub(r"Abstract:\s*\n", "Abstract: ", abstract)

        pdf_url = response.xpath("//a[contains(@class, 'href_Poster') and @title='PDF']/@href").get()

        return title, pdf_url, authors, abstract


class MmScrapySpider(BaseSpider):
    name = 'mm'

    start_urls = [
        "https://dl.acm.org/conference/mm/proceedings",
    ]
    base_url = "https://dl.acm.org"

    from_dblp = False

    def parse(self, response):
        proceeding_urls = response.xpath("//ul[@class='conference__proceedings__container']/li/div[@class='conference__title left-bordered-title']/a/@href").extract()
        proceeding_titles = response.xpath("//ul[@class='conference__proceedings__container']/li/div[@class='conference__title left-bordered-title']/a/text()").extract()
        proceeding_years = [pro.split(" '")[1][:2] for pro in proceeding_titles]
        proceeding_years = ["MM20" + year if year[0] !='9' else "MM19" + year for year in proceeding_years ]
        proceeding_dicts = {year: url for year, url in zip(proceeding_years, proceeding_urls)}

        for conf in self.wanted_conf:
            if conf not in proceeding_dicts:
                continue
            url = self.base_url + proceeding_dicts[conf]
            meta = {"conf": conf}
            yield scrapy.Request(url, callback=self.parse_session_list, meta=meta)

    def parse_session_list(self, response):
        meta = {"conf": response.meta['conf']}
        session_list = response.xpath("//div[@class='accordion sections']/div[@class='accordion-tabbed rlist']/div/a/@href").extract()

        for session in session_list:
            doi = re.search(pattern=r'10(.+?)\?', string=session)[0][:-1]
            tocHeading = session.split("=")[1]
            url = "https://dl.acm.org/pb/widgets/lazyLoadTOC?tocHeading={}&widgetId=f51662a0-fd51-4938-ac5d-969f0bca0843&doi={}&pbContext=;" \
                  "article:article:doi\:{};" \
                  "taxonomy:taxonomy:conference-collections;" \
                  "topic:topic:conference-collections>mm;" \
                  "wgroup:string:ACM Publication Websites;" \
                  "groupTopic:topic:acm-pubtype>proceeding;" \
                  "csubtype:string:Conference Proceedings;" \
                  "page:string:Book Page;" \
                  "website:website:dl-site;" \
                  "ctype:string:Book Content;journal:journal:acmconferences;" \
                  "pageGroup:string:Publication Pages;" \
                  "issue:issue:doi\:{}".format(tocHeading, doi, doi, doi)

            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        doi_list = response.xpath("//div[@class='issue-item clearfix']/div/div/h5/a/@href").extract()

        for doi in doi_list:
            url = self.base_url + doi
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):

        title = response.xpath("//div[@class='article-citations']/div[@class='citation']/div[@class='border-bottom clearfix']/h1/text()").get()

        authors = inspect.cleandoc(",".join(response.xpath(
            "//div[@class='article-citations']/div[@class='citation']/div[@class='border-bottom clearfix']/div[@id='sb-1']/ul/li[@class='loa__item']/a/@title").extract()))

        abstract = inspect.cleandoc(response.xpath("//div[@class='abstractSection abstractInFull']/p/text()").get())

        pdf_url = response.xpath("//div[@class='article-citations']//a[@title='PDF']/@href").get()

        return title, pdf_url, authors, abstract

class KddScrapySpider(MmScrapySpider):
    name = 'kdd'

    start_urls = [
        "https://dl.acm.org/conference/kdd/proceedings",
    ]
    base_url = "https://dl.acm.org"

    from_dblp = False

    def parse(self, response):
        proceeding_urls = response.xpath("//ul[@class='conference__proceedings__container']/li[@class='conference__proceedings']/div[@class='conference__title left-bordered-title']/a/@href").extract()
        proceeding_titles = response.xpath("//ul[@class='conference__proceedings__container']/li[@class='conference__proceedings']/div[@class='conference__title left-bordered-title']/a/text()").extract()
        proceeding_years = [pro.split(" '")[1][:2] for pro in proceeding_titles]
        proceeding_years = ["KDD20" + year if year[0] !='9' else "KDD19" + year for year in proceeding_years ]
        proceeding_dicts = {year: url for year, url in zip(proceeding_years, proceeding_urls)}

        for conf in self.wanted_conf:
            if conf not in proceeding_dicts:
                continue
            url = self.base_url + proceeding_dicts[conf]
            meta = {"conf": conf}
            yield scrapy.Request(url, callback=self.parse_session_list, meta=meta)


    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        doi_list = response.xpath("//div[@class='issue-item clearfix']/div/div/h5/a/@href").extract()

        for doi in doi_list:
            url = self.base_url + doi
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)


class WwwScrapySpider(MmScrapySpider):
    name = 'www'

    start_urls = [
        "https://dl.acm.org/conference/www/proceedings",
    ]
    base_url = "https://dl.acm.org"

    from_dblp = False

    def parse(self, response):

        proceeding_urls = response.xpath("//li[@class='conference__proceedings']/div[@class='conference__title left-bordered-title']/a[contains(string(), ': Proceedings of') and not(contains(text(), 'Companion:')) and not(contains(text(), 'Special interest tracks and posters')) and not(contains(text(), 'Alt')) and not(contains(text(), 'WWW4')) ]/@href").extract()
        proceeding_titles = response.xpath("//li[@class='conference__proceedings']/div[@class='conference__title left-bordered-title']/a[contains(string(), ': Proceedings of') and not(contains(text(), 'Companion:')) and not(contains(text(), 'Special interest tracks and posters')) and not(contains(text(), 'Alt')) and not(contains(text(), 'WWW4'))]/text()").extract()
        proceeding_years = [pro.split(" '")[1][:2] for pro in proceeding_titles]
        proceeding_years = ["WWW20" + year if year[0] !='9' else "WWW19" + year for year in proceeding_years ]
        proceeding_dicts = {year: url for year, url in zip(proceeding_years, proceeding_urls)}

        for conf in self.wanted_conf:
            if conf not in proceeding_dicts:
                continue
            url = self.base_url + proceeding_dicts[conf]
            meta = {"conf": conf}
            yield scrapy.Request(url, callback=self.parse_session_list, meta=meta)


    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        doi_list = response.xpath("//div[@class='issue-item clearfix']/div/div/h5/a/@href").extract()

        for doi in doi_list:
            url = self.base_url + doi
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)


class AclScrapySpider(BaseSpider):
    name = 'acl'

    start_urls = [
        "https://aclanthology.org/venues/acl/",
    ]
    base_url = "https://aclanthology.org"

    from_dblp = False

    def parse(self, response):
        conf_urls = response.xpath("//div[@id='main-container']//div[contains(@class, 'col-sm')]//ul/li[1]/a[@class='align-middle']/@href").extract()
        years = response.xpath("//div[@id='main-container']//div[contains(@class, 'col-sm-1')]//text()").extract()
        proceeding_dicts = {year:conf for year, conf in zip(years, conf_urls) if year >= "2013"}

        for conf in self.wanted_conf:
            if conf[-4:] not in proceeding_dicts:
                continue
            url = self.base_url + proceeding_dicts[conf[-4:]]
            meta = {"conf": conf}
            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):
        meta = {"conf": response.meta['conf']}
        paper_urls = response.xpath(
            "//section[@id='main']//p[contains(@class, 'd-sm-flex align-items-stretch')][position() >= 2]//strong/a/@href").extract()

        for paper_url in paper_urls:
            url = self.base_url + paper_url
            yield scrapy.Request(url, callback=self.parse_paper, meta=meta)

    @staticmethod
    def extract_data(response):
        title = re.sub(r'<[^>]+>', '', response.xpath("//section[@id='main']/div/h2[@id='title']").get())

        authors = ",".join([author for author in response.xpath("//section[@id='main']/div/p[@class='lead']//a/text()").extract()])
        abstract = response.xpath("//div[contains(@class, 'acl-abstract')]/span/text()").get()
        pdf_url = response.xpath("//div[contains(@class, 'acl-paper-link-block')]/a[contains(@class, 'btn-primary')]/@href").get()
        return title, pdf_url, authors, abstract


class EmnlpScrapySpider(AclScrapySpider):
    name = "emnlp"

    start_urls = [
        "https://aclanthology.org/venues/emnlp/",
    ]

    base_url = "https://aclanthology.org"

    from_dblp = False

class NaaclScrapySpider(AclScrapySpider):
    name = "naacl"

    start_urls = [
        "https://aclanthology.org/venues/naacl/",
    ]

    base_url = "https://aclanthology.org"

    from_dblp = False

class DblpScrapySpider(BaseSpider):

    def parse(self, response):
        href_pattern = r'href="([^"]+)"'
        year_pattern = r'\b\d{4}\b'
        year_html_list = response.xpath("//div[@id='info-section']/following-sibling::ul/li")

        year_dict = {}
        for year_html in year_html_list:
            volumn_list = re.findall(href_pattern, year_html.get())
            year = re.findall(year_pattern, year_html.get())[0]
            year_dict[year] = volumn_list

        for conf in self.wanted_conf:
            if conf[-4:] not in year_dict:
                continue

            meta = {"conf": conf}
            urls = year_dict[conf[-4:]]
            for url in urls:
                yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)

    def parse_paper_list(self, response):

        numbers = response.xpath("//div[@id='main']//ul[@class='publ-list']")

        for number in numbers:
            titles = number.xpath(".//cite[@class='data tts-content']//span[@class='title']/text()").extract()
            for i, title in enumerate(titles):

                authors = ",".join(number.xpath(".//cite[@class='data tts-content']")[i].xpath(".//span[@itemprop='author']/a//text()").extract())
                # Deliver the scraped item to `pipelines.py`.

                paper = Paper()
                paper["conf"] = response.meta['conf']
                paper["title"] = title
                paper["authors"] = authors
                paper["pdf_url"] = ""
                paper["abstract"] = ""

                yield paper


class DblpConfScrapySpider(DblpScrapySpider):

    def parse(self, response):
        year_lst = response.xpath("//header[@class='h2']/h2/@id").extract()
        year_content = response.xpath("//ul[@class='publ-list']/li[1]//a[@class='toc-link']/@href").extract()

        year_dict = dict(zip(year_lst, year_content))

        for conf in self.wanted_conf:
            if conf[-4:] not in year_dict:
                continue

            meta = {"conf": conf}
            url = year_dict[conf[-4:]]

            yield scrapy.Request(url, callback=self.parse_paper_list, meta=meta)


class MultimediaScrapySpider(DblpConfScrapySpider):
    name = 'mm'

    start_urls = [
        "https://dblp.org/db/conf/mm/index.html",
    ]

    from_dblp = True


class WwwScrapySpider(DblpConfScrapySpider):
    name = 'www'

    start_urls = [
        "https://dblp.org/db/conf/www/index.html",
    ]

    from_dblp = True

class AaaiScrapySpider(DblpConfScrapySpider):
    name = 'aaai'
    start_urls = [
        "https://dblp.org/db/conf/aaai/index.html",
    ]

    from_dblp = True


class IcasspScrapySpider(DblpConfScrapySpider):
    name = 'icassp'

    start_urls = [
        "https://dblp.org/db/conf/icassp/index.html",
    ]

    from_dblp = True
class TpamiScrapySpider(DblpScrapySpider):
    name = "tpami"

    start_urls = [
        "https://dblp.org/db/journals/pami/index.html",
    ]

    from_dblp = True

class NmiScrapySpider(DblpScrapySpider):
    name = "nmi"

    start_urls = [
        "https://dblp.org/db/journals/natmi/index.html",
    ]

    from_dblp = True

class PnasScrapySpider(DblpScrapySpider):
    name = "pnas"

    start_urls = [
        "https://dblp.org/db/journals/pnas/index.html",
    ]

    from_dblp = True

class IjcvScrapySpider(DblpScrapySpider):
    name = "ijcv"

    start_urls = [
        "https://dblp.org/db/journals/ijcv/index.html",
    ]

    from_dblp = True

class TaffcScrapySpider(DblpScrapySpider):
    name = "taffc"

    start_urls = [
        "https://dblp.org/db/journals/taffco/index.html",
    ]

    from_dblp = True

class TipScrapySpider(DblpScrapySpider):
    name = "tip"

    start_urls = [
        "https://dblp.org/db/journals/tip/index.html",
    ]

    from_dblp = True

class IfScrapySpider(DblpScrapySpider):
    name = "if"

    start_urls = [
        "https://dblp.org/db/journals/inffus/index.html",
    ]

    from_dblp = True


class TspScrapySpider(DblpScrapySpider):
    name = "tsp"

    start_urls = [
        "https://dblp.org/db/journals/tsp/index.html",
    ]

    from_dblp = True


