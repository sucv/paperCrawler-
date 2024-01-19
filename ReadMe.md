## Paper Crawler for Top CS/AI/ML/NLP Conferences and Journals

This is a [Scrapy](https://docs.scrapy.org/en/latest/intro/tutorial.html)-based crawler. The crawler scrapes accepted papers from top  conferences and journals, including:


| Year   | 2023 | 2022 | 2021 | 2020 | 2019 | 2018 | 2017 | older |
|--------|------|------|------|------|------|------|------|-------|
| CVPR   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| ECCV   |      | [x]  |      | [x]  |      | [x]  |      |       |
| ICCV   | [x]  |      | [x]  |      | [x]  |      | [x]  | [x]   |
| NIPS   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| ICLR   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  |    |
| ICML   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  |   |
| AAAI   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| IJCAI  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| ACM MM | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| KDD    | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| WWW    | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| ACL    | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| EMNLP  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| NAACL  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
|        | | | | | | | | |
| TPAMI  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| NMI    | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| PNAS   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| IJCV   | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| IF     | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| TIP    | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |
| TAFFC  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]  | [x]   |



The scraped information includes:

```text
Conference, matched keywords, title, citation count, code url, pdf url, authors, abstract
```

>Note that some terms are not available for each paper, such as the `code url` and `pdf url`. Also, for journals, most of them are not directly crawl-able.  I resort to dblp to get the paper title, then query via Semantic Scholar API. The latter will soon reach the limit (status 429). It will continue querying the same paper until got status 200. 


### Install

```shell
pip install scrapy semanticscholar fuzzywuzzy pyparsing git+https://github.com/sucv/paperCrawler.git
```

### Usage

Firstly, cd to the path where `main.py` is located. During the crawling, a `data.csv` will be generated on-the-go in the same directory by default unless `-out` is specified.

To get all papers from CVPR and ECCV held in 2021, 2022, and 2023 without any querying, and save all the output to `all.csv`.
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "" -out "all.csv"
```

To query papers whose title includes either `emotion recognition` or `facial expression` or `multimodal`. 
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "(emotion recognition) or (facial expression) or multimodal"
```

To query within paper abstracts instead of paper titles.
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "(emotion recognition) or (facial expression) or multimodal" --query_from_abstract  
```

Additionally, to count the citation for each matched paper. 
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "emotion and (visual or audio or speech)" --query_from_abstract  --count_citations  
```
Note that the counting is done using [SemanticScholar API](https://www.semanticscholar.org/product/api), 10-second is set as the time interval for each url request to not exceed the API call limit, therefore it would be time-consuming, considering that one conference may have thousands of papers.

More example for queries can be found [here](https://github.com/pyparsing/pyparsing/blob/master/examples/booleansearchparser.py#L329C18-L329C18)

### Add Custom Spider for a journal/conf from dblp

In `spiders.py`, add the following code snippet in the rear:
```python
class TpamiScrapySpider(DblpScrapySpider): ### Name your class and inherit from DblpScrapySpider
    name = "tpami" ### Name your spider

    start_urls = [
        "https://dblp.org/db/journals/pami/index.html",  # Specify the starting dblp page of your target conf/journal
    ]
    
    ### The rest remain the same.
    base_url = "https://dblp.org/db/journals/pami/"
    download_delay = 10

    custom_settings = {
        'ITEM_PIPELINES': {'crawl_conf.pipelines.CrawlDblpPipeline': 300},
    }
```
As shown in the example, basically you just need to inherit from `DblpScrapySpider`, and specify `name=`, and put `start_urls` to the conf/journal's dblp homepage. Leave the rest! That's all. Later you will be able to use the `name` you specified to crawl paper information.

Supported arguments:
+ `confs`: cvpr, iccv, eccv, aaai, ijcai, nips, iclr, icml, mm, kdd, www, acl, emnlp, naacl, tpami, nmi, pnas, ijcv, if, tip, taffc. Must be in lowercase, use comma to separate. 
+ `years`: four-digit numbers, use comma to separate.
+ `queries`: a case-insensitive string containing `()`, `and`, `or`, `not` and wildcard  `*` for querying within the paper titles or abstracts, borrowed from [pyparsing](https://github.com/pyparsing/pyparsing/blob/master/examples/booleansearchparser.py).
+ `out`: if specified, will save the output to the path.
+ `count_citations`: if specified, will count the citations using [SemanticScholar API](https://www.semanticscholar.org/product/api). The time interval for crawling each paper will be set to 10 seconds to prevent from exceeding the maximum request limit per second . Don't easily use this as it will greatly slow down the crawling!!!
+ `query_from_abstract`: if specified, will query from the abstract instead of title. Ignored for journals.



### Change Log

+ 19-JAN-2024
  + Fixed an issue in which the years containing single volume and multiple volumes of a journal from dblp cannot be correctly parsed. 
+ 05-JAN-2024
  + Greatly speeded up journal crawling, as by default only title and authors are captured directly from dblp. Specified `-count_citations` to get `abstract`, `pdf_url`, and `citation_count`.
+ 04-JAN-2024
  + Added support for ACL, EMNLP, and NAACL.
  + Added support for top journals, including TPAMI, NMI (Nature Machine Intelligence), PNAS, IJCV, IF, TIP, and TAAFC via dblp and sematic scholar AIP.
    + You may easily add your own spider in `spiders.py` by inheriting class `TpamiScrapySpider` [like I did](https://github.com/sucv/paperCrawler/blob/b83062636a338ce612bacb4d50b22446ff44e6ca/crawl_conf/crawl_conf/spiders/spiders.py#L774C10-L774C10) for the journals. 
+ 03-JAN-2024
  + Added the `-out` argument to specify the output path and filename.
  + Fixed urls for NIPS2023.
+ 02-JAN-2024
  + Fixed urls that were not working due to target website updates.
  + Added support for ICLR, ICML, KDD, and WWW.
  + Added support for querying with [pyparsing](https://github.com/pyparsing/pyparsing/blob/master/examples/booleansearchparser.py):
    + 'and', 'or' and implicit 'and' operators;
    + parentheses;
    + quoted strings;
    + wildcards at the end of a search term (help*);
    + wildcards at the beginning of a search term (*lp);
+ 28-OCT-2022
  + Added a feature in which the target conferences can be specified in `main.py`. See Example 4. 
+ 27-OCT-2022
  + Added support for ACM Multimedia. 
+ 20-OCT-2022
  + Fixed a bug that falsely locates the paper pdf url for NIPS.
+ 7-OCT-2022
    + Rewrote `main.py` so that the crawler can run over all the conferences!
+ 6-OCT-2022
    + Removed the use of `PorterStemmer()` from `nltk` as it involves false negative when querying.



