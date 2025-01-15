from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Hello PhD life!')
    parser.add_argument('-confs', default="cvpr, iccv, eccv, aaai, ijcai, nips, iclr, icml, mm, kdd, www, acl, emnlp, naacl, tpami, nmi, pnas, ijcv, if, tip, taffc", type=str,
                        help='What years you want to crawl?')
    parser.add_argument('-years', default="2016,2017,2018,2019,2020,2021,2022,2023,2024", type=str, help='What years you want to crawl?')
    parser.add_argument('-queries', default="relation, relationship,correlate,correlation", type=str, help='What keywords you want to query?')
    parser.add_argument('-out', default=None, type=str, help='Specify the output path as /path/to/filename.csv')
    parser.add_argument('--nocrossref', action='store_true', help='Do not request extra details through API call from Crossref')

    args = parser.parse_args()

    confs = args.confs
    years = args.years
    queries = args.queries
    nocrossref = args.nocrossref

    # ------------------------------------------------------------
    # Get default Scrapy settings and instantiate a CrawlerProcess
    # ------------------------------------------------------------
    setting = get_project_settings()
    process = CrawlerProcess(setting)

    # You have set some feed-output settings
    process.settings.set('FEED_FORMAT', 'csv')          # or 'csv', 'xml', etc.
    process.settings.set('FEED_URI', 'data.csv')        # default output file name

    if args.out is not None:
        # If user specified an output path, override the default
        process.settings.set('FEED_URI', args.out)


    # ------------------------------------------------------------
    # Now queue up the crawls for each requested conference
    # ------------------------------------------------------------
    for conf in confs.split(","):
        process.crawl(
            conf,
            years=years,
            queries=queries,
            nocrossref=nocrossref,
        )

    process.start()
