import time
import threading
import re
import requests

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from fuzzywuzzy import fuzz

OPENALEX_URL = "https://api.openalex.org/works"

# ------------- BooleanSearchParser code (unchanged) -------------
from pyparsing import (
    Word,
    alphanums,
    CaselessKeyword,
    Group,
    Forward,
    Suppress,
    OneOrMore,
    one_of,
    ParserElement,
)

ParserElement.enablePackrat()

alphabet_ranges = [
    [int("0400", 16), int("04FF", 16)],  # CYRILIC
    [int("0600", 16), int("07FF", 16)],  # ARABIC
    [int("0E00", 16), int("0E7F", 16)],  # THAI
    [int("3040", 16), int("30FF", 16)],  # JAPANESE
    [int("3200", 16), int("32FF", 16)],  # Enclosed CJK Letters and Months
    [int("4E00", 16), int("9FFF", 16)],  # CHINESE
    [int("1100", 16), int("11FF", 16)],  # KOREAN
    [int("3130", 16), int("318F", 16)],
    [int("A960", 16), int("A97F", 16)],
    [int("AC00", 16), int("D7AF", 16)],
    [int("D7B0", 16), int("D7FF", 16)],
    [int("FF00", 16), int("FFEF", 16)],  # Halfwidth and Fullwidth Forms
]


class BooleanSearchParser:
    def __init__(self):
        self._methods = {
            "and": self.evaluateAnd,
            "or": self.evaluateOr,
            "not": self.evaluateNot,
            "parenthesis": self.evaluateParenthesis,
            "quotes": self.evaluateQuotes,
            "word": self.evaluateWord,  # if no wildcards
            "wordwildcardprefix": self.evaluateWordWildcardPrefix,
            "wordwildcardsufix": self.evaluateWordWildcardSufix,
        }
        self._parser = self.parser()
        self.text = ""
        self.words = []

    def parser(self):
        operatorOr = Forward()

        alphabet = alphanums
        for lo, hi in alphabet_ranges:
            alphabet += "".join(chr(c) for c in range(lo, hi + 1) if not chr(c).isspace())

        operatorWord = Group(Word(alphabet + "*")).set_results_name("word*")

        operatorQuotesContent = Forward()
        operatorQuotesContent << ((operatorWord + operatorQuotesContent) | operatorWord)

        operatorQuotes = (
            Group(Suppress('"') + operatorQuotesContent + Suppress('"')).set_results_name("quotes")
            | operatorWord
        )

        operatorParenthesis = (
            Group(Suppress("(") + operatorOr + Suppress(")")).set_results_name("parenthesis")
            | operatorQuotes
        )

        operatorNot = Forward()
        operatorNot << (
            Group(Suppress(CaselessKeyword("not")) + operatorNot).set_results_name("not")
            | operatorParenthesis
        )

        operatorAnd = Forward()
        operatorAnd << (
            Group(operatorNot + Suppress(CaselessKeyword("and")) + operatorAnd).set_results_name("and")
            # implicit AND if operator is missing
            | Group(operatorNot + OneOrMore(~one_of("and or") + operatorAnd)).set_results_name("and")
            | operatorNot
        )

        operatorOr << (
            Group(operatorAnd + Suppress(CaselessKeyword("or")) + operatorOr).set_results_name("or")
            | operatorAnd
        )

        return operatorOr.parse_string

    def evaluateAnd(self, argument):
        overall_found = True
        overall_tokens = set()
        for arg in argument:
            found, tokens = self.evaluate(arg)
            if not found:
                return (False, set())
            overall_found = overall_found and found
            overall_tokens |= tokens
        return (overall_found, overall_tokens)

    def evaluateOr(self, argument):
        any_found = False
        union_tokens = set()
        for arg in argument:
            found, tokens = self.evaluate(arg)
            if found:
                any_found = True
                union_tokens |= tokens
        return (any_found, union_tokens if any_found else set())

    def evaluateNot(self, argument):
        found, tokens = self.evaluate(argument[0])
        if found:
            return (False, set())
        else:
            return (True, set())

    def evaluateParenthesis(self, argument):
        return self.evaluate(argument[0])

    def evaluateQuotes(self, argument):
        phrase = " ".join(tok[0] for tok in argument)
        if phrase in self.text:
            return (True, {phrase})
        else:
            return (False, set())

    def evaluateWord(self, argument):
        raw_word = argument[0]
        wildcard_count = raw_word.count("*")
        if wildcard_count > 0:
            # Single '*' at start -> endswith
            if wildcard_count == 1 and raw_word.startswith("*"):
                return self.GetWordWildcard(raw_word[1:], method="endswith")
            # Single '*' at end -> startswith
            if wildcard_count == 1 and raw_word.endswith("*"):
                return self.GetWordWildcard(raw_word[:-1], method="startswith")
            # Otherwise -> treat as regex
            _regex = raw_word.replace("*", ".*")
            matched = set()
            for w in self.words:
                if re.search(_regex, w):
                    matched.add(w)
            return ((len(matched) > 0), matched)
        # no wildcard
        return self.GetWord(raw_word)

    def evaluateWordWildcardPrefix(self, argument):
        return self.GetWordWildcard(argument[0], method="endswith")

    def evaluateWordWildcardSufix(self, argument):
        return self.GetWordWildcard(argument[0], method="startswith")

    def evaluate(self, argument):
        return self._methods[argument.getName()](argument)

    def Parse(self, query):
        parsed = self._parser(query)[0]
        return self.evaluate(parsed)

    def GetWord(self, word):
        if word in self.words:
            return (True, {word})
        return (False, set())

    def GetWordWildcard(self, word, method="startswith"):
        matched = set()
        for w in self.words:
            if getattr(w, method)(word):
                matched.add(w)
        return ((len(matched) > 0), matched)

    def _split_words(self, text):
        words = []
        r = re.compile(r"[\s{}]+".format(re.escape("!\"$%&'()*+,-/:;<=>?[\\]^`{|}~")))
        _words = r.split(text)
        for _w in _words:
            if "." in _w and not _w.startswith("#") and not _w.startswith("@"):
                words.extend(_w.split("."))
            else:
                words.append(_w)
        return [w for w in words if w]

    def match_with_tokens(self, text, expr):
        self.text = text
        self.words = self._split_words(text)
        return self.Parse(expr)

    def match(self, text, expr):
        found, _ = self.match_with_tokens(text, expr)
        return found


# ------------------------------- NEW Code / Changes -------------------------------
import time
import threading

class CrawlPipeline:
    # These three attributes are newly added for rate-limiting:
    rate_limit_lock = threading.Lock()
    last_request_time = 0
    COOLDOWN_SECONDS = 1  # Wait 1s between external requests

    def process_item(self, item, spider):
        parser = BooleanSearchParser()
        abstract = item["abstract"]
        title = item["title"]

        clean_title = re.sub(r'\W+', ' ', title).lower()
        text_body = clean_title

        # parse queries
        if spider.queries == "":
            found = True
            matched_tokens = set()
        else:
            found, matched_tokens = parser.match_with_tokens(
                text=text_body, expr=spider.queries
            )

        if found:
            if not spider.from_dblp and abstract is not None:
                item["code_url"] = re.findall(r'(https?://\S+)', abstract)

            citation_count = -1
            paper_categories = ""
            paper_concepts = ""

            # Only call external API if the spider says so
            if spider.crossref:
                params = {"search": clean_title}

                # --- NEW: This block is now rate-limited ---
                with self.rate_limit_lock:
                    now = time.time()
                    elapsed = now - self.last_request_time
                    if elapsed < self.COOLDOWN_SECONDS:
                        time.sleep(self.COOLDOWN_SECONDS - elapsed)

                    response = requests.get(OPENALEX_URL, params=params)
                    self.last_request_time = time.time()
                # --- END of rate-limited block ---

                if response.status_code == 200:
                    data = response.json()
                    if data["results"]:
                        paper = data["results"][0]
                        citation_count = paper["cited_by_count"]
                        paper_categories = ",".join([paper["topics"][i]['display_name'] for i in range(len(paper["topics"]))])
                        paper_concepts = ",".join([paper["concepts"][i]['display_name'] for i in range(len(paper["concepts"]))])

            item["citation_count"] = citation_count
            item["matched_queries"] = ",".join(list(matched_tokens))
            item["categories"] = paper_categories
            item["concepts"] = paper_concepts
            return item
        else:
            raise DropItem("Missing keyword in %s" % item)
