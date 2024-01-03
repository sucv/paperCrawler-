# from scrapy import cmdline
#
# cmdline.execute("scrapy crawl mm  -a years=2016,2017,2018,2019,2020,2021,2022 -a keys=emotion,affective -o emotion.csv".split())

# cmdline.execute("scrapy crawl nips  -a years=2016,2017,2018,2019,2020,2021,2022 -a keys=emotion,affective -o emotion.csv".split())
#
# # cmdline.execute("scrapy crawl nips  -a years=2015 -a keys=video -o test.csv".split())
# # cmdline.execute("scrapy crawl eccv  -a years=2020,2021,2022 -a keys=video -o output.csv -s JOBDIR=folder6".split())


from scrapy.utils.project import get_project_settings
from scrapy.crawler import CrawlerProcess
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Hello PhD life!')
    parser.add_argument('-confs', default="cvpr,iccv,eccv,nips,icml,iclr,mm,aaai,ijcai,kdd,www", type=str,
                        help='What years you want to crawl?')
    parser.add_argument('-years', default="2016,2017,2018,2019,2020,2021,2022,2023", type=str, help='What years you want to crawl?')
    parser.add_argument('-queries', default="relation, relationship,correlate,correlation", type=str, help='What keywords you want to query?')
    parser.add_argument('-out', default=None, type=str, help='Specify the output path as /path/to/filename.csv')
    parser.add_argument('--count_citations', action='store_true', help='Count the citations?')
    parser.add_argument('--query_from_abstract', action='store_true', help='Count the citations?')




    args = parser.parse_args()

    confs = args.confs
    years = args.years
    queries = args.queries
    count_citations = args.count_citations
    query_from_abstract = args.query_from_abstract


    setting = get_project_settings()
    process = CrawlerProcess(setting)

    process.settings.set('FEED_FORMAT', 'csv')  # or 'csv', 'xml', etc.
    process.settings.set('FEED_URI', 'data.csv')  # output file name
    if args.out is not None:
        # Specify the output format and file
        process.settings.set('FEED_URI', args.out)  # output file name

    for conf in confs.split(","):
        process.crawl(conf, years=years, queries=queries, count_citations=count_citations, query_from_abstract=query_from_abstract)

    process.start()