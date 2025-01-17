## Table of Contents

- [Paper Crawler for Top CS/AI/ML/NLP Conferences and Journals](#paper-crawler-for-top-csai-mlnlp-conferences-and-journals)
  - [Supported Conferences](#supported-conferences)
  - [Supported Journals](#supported-journals)
  - [Scraped Information](#scraped-information)
- [Installation](#installation)
- [Usage](#usage)
  - [Example Commands](#example-commands)
- [Adding a Custom Spider (Quick & Lazy Solution)](#adding-a-custom-spider-quick--lazy-solution)
  - [Adding a Journal Spider](#adding-a-journal-spider)
  - [Adding a Conference Spider](#adding-a-conference-spider)
  - [Explanation](#explanation)
- [Supported Arguments](#supported-arguments)
- [Change Log](#change-log)

## Paper Crawler for Top CS/AI/ML/NLP Conferences and Journals

This is a [Scrapy](https://docs.scrapy.org/en/latest/intro/tutorial.html)-based crawler. The crawler scrapes accepted papers from top conferences and journals, including:

> &ast; Indicates that the abstract is not available since the query is done from DBLP. The official sites of these papers either do not have a consistent HTML structure or block spiders.

### Supported Conferences

| Conference  | Status | Since |
|-------------|--------|-------|
| CVPR        | ✅    | 2013  |
| ECCV        | ✅    | 2018  |
| ICCV        | ✅    | 2013  |
| NeurIPS     | ✅    | 1987  |
| ICLR        | ✅    | 2016  |
| ICML        | ✅    | 2015  |
| AAAI*       | ✅    | 1980  |
| IJCAI       | ✅    | 2017  |
| ACM MM*     | ✅    | 1993  |
| KDD         | ✅    | 2015  |
| WWW*        | ✅    | 1994  |
| ACL         | ✅    | 2013  |
| EMNLP       | ✅    | 2013  |
| NAACL       | ✅    | 2013  |
| Interspeech | ✅    | 1987  |
| ICASSP*     | ✅    | 1976  |

### Supported Journals

| Journal | Status | Since |
|---------|--------|-------|
| TPAMI*  | ✅    | 1979  |
| NMI*    | ✅    | 2019  |
| PNAS*   | ✅    | 1997  |
| IJCV*   | ✅    | 1987  |
| IF*     | ✅    | 2014  |
| TIP*    | ✅    | 1992  |
| TAFFC*  | ✅    | 2010  |
| TSP*    | ✅    | 1991  |

### Scraped Information

The following information is extracted from each paper:

```text
Conference, matched keywords, title, citation count, categories, concepts, code URL, PDF URL, authors, abstract
```

## Installation

```shell
pip install scrapy pyparsing git+https://github.com/sucv/paperCrawler.git
```

## Usage

First, navigate to the directory where `main.py` is located. During crawling, a CSV file will be generated in the same directory by default unless `-out` is specified.

### Example Commands

#### Get all papers from CVPR, ICCV, and ECCV (2021-2023) without querying and save output to `all.csv`
```shell
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "" -out "all.csv"
```

#### Query papers with titles containing `emotion recognition`, `facial expression`, or `multimodal`
```shell
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "(emotion recognition) or (facial expression) or multimodal"
```

#### Query papers with more advanced boolean expressions
```shell
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "emotion and (visual or audio or speech)" --nocrossref  
```

> **Note:** Citation count is an important metric for evaluating a paper. Since the `Crossref API` does not have strict rate limits, it is recommended **not** to use `--nocrossref` unless necessary.

## Adding a Custom Spider (Quick & Lazy Solution)

[dblp](https://dblp.org/) provides consistent HTML structures, making it easy to add custom spiders for publishers. You can quickly create a spider for any conference or journal. However, abstracts are unavailable through DBLP. Nonetheless, useful details like citation count, categories, and concepts can still be extracted.

### Adding a Journal Spider

In `spiders.py`, add the following code:

```python
class TpamiScrapySpider(DblpScrapySpider):
    name = "tpami"

    start_urls = [
        "https://dblp.org/db/journals/pami/index.html",
    ]

    from_dblp = True
```

### Adding a Conference Spider

```python
class InterspeechScrapySpider(DblpConfScrapySpider):
    name = 'icassp'

    start_urls = [
        "https://dblp.org/db/conf/icassp/index.html",
    ]

    from_dblp = True
```

### Explanation

Simply inherit from `DblpScrapySpider` or `DblpConfScrapySpider`, set `name=`, set `from_dblp = True`, and provide `start_urls` pointing to the DBLP homepage of the conference/journal. The rest is handled automatically. Later, you can use the specified `name` to crawl paper information.

## Supported Arguments

- `confs`: A list of supported conferences and journals (must be lowercase, separated by commas).
- `years`: A list of four-digit years (separated by commas).
- `queries`: A case-insensitive query string supporting `()`, `and`, `or`, `not`, and wildcard `*`, based on [pyparsing](https://github.com/pyparsing/pyparsing/blob/master/examples/booleansearchparser.py).
- `out`: Specifies the output file path.
- `nocrossref`: Disables fetching citation count, concepts, and categories via CrossRef API.

## Change Log

+ 17-JAN-2025
  + Add spiders for Interspeech, TSP, and ICASSP.
+ 15-JAN-2025
  + Add citation count, concepts, categories for a matched paper based on the Crossref API, with 1s cooldown for each request. For unmatched paper, the download cooldown won't be triggered.
  + Fixed multiple out-of-date crawlers.
  + Removed some arguments such as `count_citations` and `query_from_abstract`. Now it will call Crossref API for extra information by default, and will always query from title, not abstract.
+ 19-JAN-2024
  + Fixed an issue in which the years containing single volume and multiple volumes of a journal from dblp cannot be correctly parsed. 
+ 05-JAN-2024
  + Greatly speeded up journal crawling, as by default only title and authors are captured directly from dblp. Specified `-count_citations` to get `abstract`, `pdf_url`, and `citation_count`.
+ 04-JAN-2024
  + Added support for ACL, EMNLP, and NAACL.
  + Added support for top journals, including TPAMI, NMI (Nature Machine Intelligence), PNAS, IJCV, IF, TIP, and TAAFC via dblp and sematic scholar AIP. Example is provided.
    + You may easily add your own spider in `spiders.py` by inheriting class `DblpScrapySpider` for the conferences and journals as a shortcut. In this way you will only get the paper title and authors. As paper titles can already provide initial information, you may manually search for your interested papers later. 
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



