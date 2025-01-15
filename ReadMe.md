## Paper Crawler for Top CS/AI/ML/NLP Conferences and Journals

This is a [Scrapy](https://docs.scrapy.org/en/latest/intro/tutorial.html)-based crawler. The crawler scrapes accepted papers from top  conferences and journals, including:

> &ast; indicates that the abstract is not available since the query is done from dblp. The official sites of these paper either do not have consistent html structure, or they block spiders.

| Conference   | Status | Since |
|--------------|--------|-------|
| CVPR         | [x]    | 2013  |
| ECCV         | [x]    | 2018  |
| ICCV         | [x]    | 2013  |
| NIPS         | [x]    | 1987  |
| ICLR         | [x]    | 2016  |
| ICML         | [x]    | 2015  |
| AAAI*        | [x]    | 1980  |
| IJCAI        | [x]    | 2017  |
| ACM MM*      | [x]    | 1993  |
| KDD          | [x]    | 2015  |
| WWW*         | [x]    | 1994  |
| ACL          | [x]    | 2013  |
| EMNLP        | [x]    | 2013  |
| NAACL        | [x]    | 2013  |
 


| Journal | Status | Since |
|--------|--------|-------|
| TPAMI*  | [x]    | 1979  |
| NMI*   | [x]    | 2019  |
| PNAS*  | [x]    | 1997  |
| IJCV*  | [x]    | 1987  |
| IF*    | [x]    | 2014  |
| TIP*   | [x]    | 1992  |
| TAFFC* | [x]    | 2010  |





The scraped information includes:

```text
Conference, matched keywords, title, citation count, categories, concepts, code url, pdf url, authors, abstract
```


### Install

```shell
pip install scrapy pyparsing git+https://github.com/sucv/paperCrawler.git
```

### Usage

Firstly, cd to the path where `main.py` is located. During the crawling, a `csv` will be generated on-the-go in the same directory by default unless `-out` is specified.

To get all papers from CVPR and ECCV held in 2021, 2022, and 2023 without any querying, and save all the output to `all.csv`.
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "" -out "all.csv"
```

To query papers whose title includes either `emotion recognition` or `facial expression` or `multimodal`. 
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "(emotion recognition) or (facial expression) or multimodal"
```

More example for queries can be found [here](https://github.com/pyparsing/pyparsing/blob/master/examples/booleansearchparser.py#L329C18-L329C18). Additionally, if you do not want to acquire the citation count, categories, and concepts for each paper, add `--nocrossref` 
```
python main.py -confs cvpr,iccv,eccv -years 2021,2022,2023 -queries "emotion and (visual or audio or speech)" --nocrossref  
```
>I believe the citation count is an important metric to qualify a paper. Also, the `Crossref API`does not have tight rate limits. Therefore, it is highly recommended to not add `--nocrossref`.



### Add Custom Spider (A quick and lazy solution)

[dblp](https://dblp.org/) features consistent HTML structures, therefore, we can directly add any custom spider based on it. The only downside is that there is no abstract for any papers from it.

In `spiders.py`, add the following code snippet in the rear.

For journal:
```python
class TpamiScrapySpider(DblpScrapySpider):
    name = "tpami"

    start_urls = [
        "https://dblp.org/db/journals/pami/index.html",
    ]

    from_dblp = True
```

For conference:
```python
class InterspeechScrapySpider(DblpConfScrapySpider):
    name = 'interspeech'

    start_urls = [
        "https://dblp.org/db/conf/interspeech/index.html",
    ]

    from_dblp = True
```

As shown in the example, basically you just need to inherit from `DblpScrapySpider` or `DblpConfScrapySpider`, and specify `name=` and `from_dblp = True`, and put `start_urls` to the conf/journal's dblp homepage. Leave the rest! Later you will be able to use the `name` you specified to crawl paper information.

### Supported arguments:
+ `confs`: cvpr, iccv, eccv, aaai, ijcai, nips, iclr, icml, mm, kdd, www, acl, emnlp, naacl, tpami, nmi, pnas, ijcv, if, tip, taffc. Must be in lowercase, use comma to separate. 
+ `years`: four-digit numbers, use comma to separate.
+ `queries`: a case-insensitive string containing `()`, `and`, `or`, `not` and wildcard  `*` for querying within the paper titles or abstracts, borrowed from [pyparsing](https://github.com/pyparsing/pyparsing/blob/master/examples/booleansearchparser.py).
+ `out`: if specified, will save the output to the path.
+ `nocrossref`: if specified, will not call CrossRef API for paper citation count, concepts, and categories.



### Change Log

+ 15-JAN-2024
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



