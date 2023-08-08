# Beautiful Soup 4
from bs4 import BeautifulSoup

# Support
from fake_useragent import UserAgent
import requests

# global variable
user_agent = {"User-Agent": UserAgent().chrome}
delay = 120


class CrossCurrencyData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker.split("=")[0]
        self.url = f"https://finance.yahoo.com/quote/{self.ticker}%3DX?p={self.ticker}%3DX"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_current_price(self):
        return [price.text for price in self.soup.find_all("fin-streamer", attrs={"data-pricehint": "4"})
                if not price.find_all("fin-streamer", attrs={"data-pricehint": "4"})][0]

    def get_last_52_week_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][3]

    def get_day_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][1]

    def get_previous_close(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[0].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][1]


# meta = CrossCurrencyData("EURUSD=X")
# print(meta.get_current_price())
# print(meta.get_last_52_week_range())
# print(meta.get_day_range())
# print(meta.get_previous_close())

