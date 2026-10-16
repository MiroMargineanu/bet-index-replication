#!/usr/bin/env python3
import logging
import re
import urllib.request
import html.parser
from concurrent.futures import ThreadPoolExecutor, as_completed

BVB_URL = "https://m.bvb.ro/FinancialInstruments/Indices/IndicesProfiles.aspx?i=BET"
BVB_SYMBOL_URL = (
    "https://m.bvb.ro/FinancialInstruments/Details/"
    "FinancialInstrumentsDetails.aspx?s={symbol}"
)

TABLE_ID = "gvC"
COL_SYMBOL = "Simbol"
COL_PRICE = "Pret ref."
COL_WEIGHT = "Pondere (%)"

STATE_INIT = 0
STATE_TABLE = 1
STATE_THEAD = 2
STATE_TH = 3
STATE_TBODY = 4
STATE_TD = 5

_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
}

# "Ultimul pret" cell on the symbol details page (live last trade).
_LAST_PRICE_RE = re.compile(
    r"Ultimul pret</td>\s*<td[^>]*>\s*([0-9]+(?:[.,][0-9]+)?)\s*</td>",
    re.IGNORECASE,
)

class BvbParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.state = STATE_INIT
        self.columns = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if self.state == STATE_INIT:
            if tag == "table":
                for key, val in attrs:
                    if key == "id" and val == TABLE_ID:
                        self.state = STATE_TABLE
        elif self.state == STATE_TABLE:
            if tag == "thead":
                self.state = STATE_THEAD
        elif self.state == STATE_THEAD:
            if tag == "th":
                self.state = STATE_TH
            elif tag == "tbody":
                self.state = STATE_TBODY
        elif self.state == STATE_TBODY:
            if tag == "tr":
                self.rows.append([])
            elif tag == "td":
                self.state = STATE_TD

    def handle_endtag(self, tag):
        if tag == "table":
            self.state = STATE_INIT

    def handle_data(self, data):
        if self.state == STATE_TH:
            self.columns.append(data.strip())
            self.state = STATE_THEAD
        elif self.state == STATE_TD:
            if len(self.rows) > 0:
                self.rows[-1].append(data.strip())
            self.state = STATE_TBODY


def _fetch(url):
    request = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def _parse_last_price(page_html):
    match = _LAST_PRICE_RE.search(page_html)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _fetch_last_price(symbol):
    try:
        page = _fetch(BVB_SYMBOL_URL.format(symbol=symbol))
    except Exception as exc:
        logging.warning(f"Nu s-a putut obtine pretul live pentru {symbol}: {exc}")
        return None
    price = _parse_last_price(page)
    if price is None:
        logging.warning(f"Nu s-a gasit 'Ultimul pret' pentru {symbol}")
    return price


def crawl():
    """Fetch BET weights from the index profile and live last prices per symbol."""
    content = _fetch(BVB_URL)
    parser = BvbParser()
    parser.feed(content)
    parser.close()

    if len(parser.columns) < 3 or len(parser.rows) < 5:
        logging.error(f"Nu s-au putut obtine date de la url-ul '{BVB_URL}'")
        return None

    colSymbol = None
    colPrice = None
    colWeight = None

    for idx, col in enumerate(parser.columns):
        if col == COL_SYMBOL:
            colSymbol = idx
        elif col == COL_PRICE:
            colPrice = idx
        elif col == COL_WEIGHT:
            colWeight = idx
    if colSymbol is None:
        logging.error(f"Nu s-a gasit coloana {COL_SYMBOL}")
        return None
    if colPrice is None:
        logging.error(f"Nu s-a gasit coloana {COL_PRICE}")
        return None
    if colWeight is None:
        logging.error(f"Nu s-a gasit coloana {COL_WEIGHT}")
        return None

    result = {}
    for row in parser.rows:
        if len(row) <= max(colSymbol, colPrice, colWeight):
            logging.error("Tabelul cu datele nu are formatul corect")
            return None
        symbol = row[colSymbol]
        ref_price = row[colPrice].replace(",", ".")
        weight = row[colWeight].replace(",", ".")
        try:
            ref_price = float(ref_price)
        except ValueError:
            logging.error(f"Pretul {ref_price} pentru simbolul {symbol} nu este un numar valid")
            return None
        try:
            weight = float(weight)
        except ValueError:
            logging.error(f"Ponderea {weight} pentru simbolul {symbol} nu este un numar valid")
            return None
        # price filled below with live last trade; keep ref as temporary fallback
        result[symbol] = {"price": ref_price, "weight": weight, "ref_price": ref_price}

    symbols = list(result.keys())
    logging.info(f"Se obtin preturile live (Ultimul pret) pentru {len(symbols)} simboluri BET")
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_last_price, s): s for s in symbols}
        for fut in as_completed(futures):
            symbol = futures[fut]
            last = fut.result()
            if last is not None:
                result[symbol]["price"] = last
            else:
                logging.warning(
                    f"Folosesc Pret ref. pentru {symbol}: {result[symbol]['ref_price']}"
                )

    return result


if __name__ == "__main__":
    result = crawl()
    print(result)
