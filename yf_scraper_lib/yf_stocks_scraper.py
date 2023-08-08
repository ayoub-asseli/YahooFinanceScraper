# Beautiful Soup 4
from bs4 import BeautifulSoup

# Selenium 4
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException

# Support
from fake_useragent import UserAgent
import requests

# global variable
user_agent = {"User-Agent": UserAgent().chrome}
delay = 120
ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)


class FinancialStatementsProfileData:

    def __init__(self, ticker, sheet, driver=False):
        """
        :param ticker: the stock symbol as a string value
        :param sheet: Just three possible string values: "balance-sheet", "financials" (income statement), "cash-flow",
                                                         "profile"
        """
        self.ticker = ticker
        self.sheet = sheet
        self.driver = driver
        if sheet == "income-statement":
            self.sheet = "financials"
        self.url = "https://finance.yahoo.com/quote/{}/{}?p={}".format(ticker, self.sheet, ticker)
        if not driver:
            self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')
        else:
            self.soup = BeautifulSoup(self.display_hidden_values(self.url), 'html.parser')

    @staticmethod
    def display_hidden_values(url_driver):
        options = Options()
        options.add_argument('--headless')
        options.add_argument(f"--user-agent={user_agent}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url_driver)
        reject_all = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//button[@class="btn secondary reject-all"]')))
        action = ActionChains(driver)
        action.click(on_element=reject_all)
        action.perform()
        expand_button = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//*[@id="Col1-1-Financials-Proxy"]/section/div[2]/button')))
        action.click(on_element=expand_button)
        action.perform()
        source = driver.page_source
        driver.close()
        return source

    @staticmethod
    def data_parsing(to_parse):
        """
        The source code structure and css selector are quite complex. This method would be useful
        in order to parse efficiently accounting data and keep an easy maintenance
        :param to_parse: data to parse from the front code
        :return: The parsed data as a list
        """
        # Global Treatment
        global_parsing = []
        for elem in to_parse.split(","):
            if len(elem) > 3 and any(char.isdigit() for char in elem):
                char, index = "", 0
                while elem[index].isalpha() or elem[index] == " ":
                    char += elem[index]
                    index += 1
                if index != 0:
                    global_parsing.append(char)
                    global_parsing.append("/")
                    global_parsing.append(elem[index:])
                else:
                    global_parsing.append(elem[:3])
                    global_parsing.append("/")
                    global_parsing.append(elem[3:])
            else:
                global_parsing.append(elem)

        return global_parsing

    def get_data_types(self):
        """
        This method allows you to have a visibility of the data you can retrieve from the company's sheet selected.
        It refers to the "Breakdown" columns
        :return: The list of all data types you can retrieve. You will be able to loop over.
        """
        types = []
        for elem in self.soup.find_all("div", attrs={"data-test": "fin-row"}):
            types.append(self.data_parsing(elem.text.strip())[0])
        return types

    def get_accounting_data(self, type_of_information, periods):
        """
        :param
        period: Could take a list of string which could contains:
                - 'TTM': Trailing twelve months (Income Statement, Cash Flow)
                - 'year_1': the year before the current one (Income Statement, Balance Sheet, Cash Flow)
                - 'year_2': the year before the year_1 (Income Statement, Balance Sheet, Cash Flow)
                -'year_3': the year before the year_2 (Income Statement, Balance Sheet, Cash Flow)
                -'year_4': the year before the year_3 (Income Statement, Balance Sheet, Cash Flow)
        type_of_information: Could take a string value which is the accounting data type from yahoo finance.
                             It refers to the "Breakdown" column (ex: "Total Revenue")
        :return: Return the revenue from the specific "period" as an integer
        """
        periods_ = ["TTM", "year_1", "year_2", "year_3", "year_4"]
        data_types = self.get_data_types()
        aimed_index, res = data_types.index(type_of_information), []
        sheet_idx = 4 if self.sheet == "balance-sheet" else 5
        for index, elem in enumerate(self.soup.find_all("div", attrs={"data-test": "fin-col"})):
            elem = elem.text
            if aimed_index * sheet_idx <= index < aimed_index * sheet_idx + sheet_idx:
                if elem[0]:
                    res.append(float(elem.replace(",", "")))
                else:
                    res.append(float(elem))
        data_res = []
        if self.sheet in ["financials", "cash-flow"]:
            for period in periods:
                data_res.append(res[periods_.index(period)])
            return data_res
        elif self.sheet == "balance-sheet" and "TTM" in periods:
            return "No TTM info for the balance-sheet"
        for period in periods:
            data_res.append(res[periods_.index(period) - 1])
        return data_res


class StocksProfileData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        :param sheet: Just three possible string values: "balance-sheet", "financials" (income statement), "cash-flow",
                                                         "profile"
        """
        self.ticker = ticker
        self.url = "https://finance.yahoo.com/quote/{}/profile?p={}".format(ticker, ticker)
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_current_price(self):
        return float([price.text for price in self.soup.find_all("fin-streamer", attrs={"data-test": "qsp-price"})
                      if not price.find_all("fin-streamer", attrs={"data-test": "qsp-price"})][0].replace(",", ""))

    def get_stock_sector(self):
        return [price.text for price in self.soup.find_all("div", attrs={"data-test": "qsp-profile"})
                if not price.find_all("div", attrs={"data-test": "qsp-profile"})][0].split("\xa0")[1].split(
            "Industry:")[0]

    def get_stock_industry(self):
        return [price.text for price in self.soup.find_all("div", attrs={"data-test": "qsp-profile"})
                if not price.find_all("div", attrs={"data-test": "qsp-profile"})][0].split("\xa0")[2].split(
            "Full Time Employees:")[0]


class StockStatisticsData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = "https://finance.yahoo.com/quote/{}/key-statistics?p={}".format(ticker, ticker)
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_stats_types(self):
        return [title.text[:-1] for title in self.soup.find_all('h2') if not title.find_all('h2')][:1] + \
               [title.text for title in self.soup.find_all('h3') if not title.find_all('h3')][6:]

    def get_data_types_by_stats_type(self, statistics_type):
        """
        :param statistics_type:
        :return:
        """
        tables_titles = self.get_stats_types()
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[tables_titles.index(statistics_type)].find_all('td') if not t.find_all('td')]
        res = []
        for index, elem in enumerate(tds):
            if index % 2 == 0:
                elem = elem.text
                if elem[-1].isnumeric():
                    res.append(elem.strip()[:-1].strip())
                else:
                    res.append(elem.strip())
        return res

    def get_statistics(self, statistics_type, stats_info):
        """
        :param statistics_type:
        :param stats_info:
        :return:
        """
        tables_titles = self.get_stats_types()
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[tables_titles.index(statistics_type)].find_all('td') if not t.find_all('td')]
        res, i = [], 0
        for elem in tds:
            elem = elem.text.strip()
            if elem[-1].isnumeric():
                elem = elem.strip()[:-1].strip()
            else:
                elem = elem.strip()
            if elem == stats_info:
                res.append(elem)
                i += 1
            elif i == 1:
                res.append(elem)
                return res[1]
        return "No data"


class BenchmarkData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker.split("=")[0]
        self.url = f"https://finance.yahoo.com/quote/%5E{self.ticker}?p=%5E{self.ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_current_price(self):
        return float([price.text for price in self.soup.find_all("fin-streamer", attrs={"data-test": "qsp-price"})
                      if not price.find_all("fin-streamer", attrs={"data-test": "qsp-price"})][0].replace(",", ""))

    def get_last_52_week_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text.replace(",", "") for elem in tds][3]

    def get_day_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text.replace(",", "") for elem in tds][1]

    def get_previous_close(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[0].find_all('td') if not t.find_all('td')]
        return float([elem.text for elem in tds][1].replace(",", ""))
