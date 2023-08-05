# Beautiful Soup 4
from bs4 import BeautifulSoup
from selenium import webdriver

# Selenium 4
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

# Support
from fake_useragent import UserAgent
import requests
import time


user_agent = {"User-Agent": UserAgent().chrome}


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
        reject_all = driver.find_element(By.XPATH, '//button[@class="btn secondary reject-all"]')
        time.sleep(1)
        action = ActionChains(driver)
        action.click(on_element=reject_all)
        action.perform()
        time.sleep(1)
        expand_button = driver.find_element(By.XPATH, '//*[@id="Col1-1-Financials-Proxy"]/section/div[2]/button')
        action.click(on_element=expand_button)
        action.perform()
        time.sleep(1)
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

    def get_current_price(self):
        return [price.text for price in self.soup.find_all("fin-streamer", attrs={"data-test": "qsp-price"})
                if not price.find_all("fin-streamer", attrs={"data-test": "qsp-price"})][0]

    def get_accounting_data(self, type_of_information, period):
        """
        :param
        period: Could take a string value argument which could be
                - 'TTM': Trailing twelve months (Income Statement, Cash Flow)
                - 'year_1': the year before the current one (Income Statement, Balance Sheet, Cash Flow)
                - 'year_2': the year before the year_1 (Income Statement, Balance Sheet, Cash Flow)
                -'year_3': the year before the year_2 (Income Statement, Balance Sheet, Cash Flow)
                -'year_4': the year before the year_3 (Income Statement, Balance Sheet, Cash Flow)
        type_of_information: Could take a string value which is the accounting data type from yahoo finance.
                             It refers to the "Breakdown" column (ex: "Total Revenue")
        :return: Return the revenue from the specific "period" as an integer
        """
        periods = ["TTM", "year_1", "year_2", "year_3", "year_4"]
        data_types = self.get_data_types()
        aimed_index, res = data_types.index(type_of_information), []
        sheet_idx = 4 if self.sheet == "balance-sheet" else 5
        for index, elem in enumerate(self.soup.find_all("div", attrs={"data-test": "fin-col"})):
            elem = elem.text
            if aimed_index * sheet_idx <= index < aimed_index * sheet_idx + sheet_idx:
                if elem[0]:
                    res.append(elem.replace(",", ""))
                else:
                    res.append(elem)
        if self.sheet in ["financials", "cash-flow"]:
            return res[periods.index(period)]
        elif self.sheet == "balance-sheet" and period == "TTM":
            return "No TTM info for the balance-sheet"
        return res[periods.index(period)-1]

    def get_stock_sector(self):
        return [price.text for price in self.soup.find_all("div", attrs={"data-test": "qsp-profile"})
                if not price.find_all("div", attrs={"data-test": "qsp-profile"})][0].split("\xa0")[1].split(
                                                                                                        "Industry:")[0]

    def get_stock_industry(self):
        return [price.text for price in self.soup.find_all("div", attrs={"data-test": "qsp-profile"})
                if not price.find_all("div", attrs={"data-test": "qsp-profile"})][0].split("\xa0")[2].split(
                                                                                             "Full Time Employees:")[0]


meta = FinancialStatementsProfileData("GLE.PA", "income-statement", driver=True)
print(meta.get_data_types())
# print(meta.get_accounting_data("Total Revenue", "year_2"))
# print(meta.get_stock_sector())
# print(meta.get_stock_industry())
# print(meta.get_current_price())


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
                res.append(elem.text.strip())
        return res

    def get_statistics(self, statistics_type, ratio):
        """
        :param statistics_type:
        :param ratio:
        :return:
        """
        tables_titles = self.get_stats_types()
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[tables_titles.index(statistics_type)].find_all('td') if not t.find_all('td')]
        res, i = [], 0
        for elem in tds:
            elem = elem.text.strip()
            if elem == ratio:
                res.append(elem)
                i += 1
            elif i == 1:
                res.append(elem)
                return res[1]
        return "No data"


# meta = StockStatisticsData("AMZN")
# print(meta.get_stats_types())
# print(meta.get_data_types_by_stats_type('Profitability'))
# print(meta.get_statistics('Profitability', 'Profit Margin'))


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


class BenchmarkData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker.split("=")[0]
        self.url = f"https://finance.yahoo.com/quote/%5E{self.ticker}?p=%5E{self.ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_current_price(self):
        return [price.text for price in self.soup.find_all("fin-streamer", attrs={"data-test": "qsp-price"})
                if not price.find_all("fin-streamer", attrs={"data-test": "qsp-price"})][0]

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


# meta = BenchmarkData("GSPC")
# print(meta.get_current_price())
# print(meta.get_last_52_week_range())
# print(meta.get_previous_close())


class ETFData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_current_price(self):
        return [price.text for price in self.soup.find_all("fin-streamer", attrs={"data-test": "qsp-price"})
                if not price.find_all("fin-streamer", attrs={"data-test": "qsp-price"})][0]

    def get_last_52_week_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[0].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][11]

    def get_day_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[0].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][9]

    def get_day_net_assets(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][1]

    def get_day_nav(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][3]

    def get_inception_date(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][15]

    def get_expense_ratio(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][13]


# meta = ETFData("HTUS")
# print(meta.get_current_price())
# print(meta.get_last_52_week_range())
# print(meta.get_day_range())


class ETFHoldingsData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = f"https://finance.yahoo.com/quote/{ticker}/holdings?p={ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_top_holdings(self):
        """
        :return:
        """
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t.text for t in tables[0].find_all('td') if not t.find_all('td')]
        res, l_r, index = [], [], 0
        for elem in tds:
            if index < 3:
                l_r.append(elem)
                index += 1
            if index == 3:
                res.append(l_r)
                index, l_r = 0, []
        return res

    def get_overall_portfolio_composition(self):
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][:2]
        part_comp = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(end)"})
                     if not elem.find_all("span", attrs={"class": "Fl(end)"})][:2]
        return list(zip(composed, part_comp))

    def get_sector_weightings(self):
        data = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                if not elem.find_all("span", attrs={"class": "Fl(start)"})][5:38]
        print(data)
        res, l_res, index = [], [], 0
        for elem in data:
            if index < 2 and elem != "":
                l_res.append(elem)
                index += 1
            if index == 2:
                res.append(l_res)
                l_res, index = [], 0
        return res

    def get_equity_holdings(self):
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][40:46]
        part_comp = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(end)"})
                     if not elem.find_all("span", attrs={"class": "Fl(end)"})][2:8]
        return list(zip(composed, part_comp))

    def get_bond_ratings(self):
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][47:]
        part_comp = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(end)"})
                     if not elem.find_all("span", attrs={"class": "Fl(end)"})][9:]
        return list(zip(composed, part_comp))


# meta = ETFHoldingsData("PICK")
# print(meta.get_top_holdings())
# print(meta.get_sector_weightings())
# print(meta.get_equity_holdings())
# print(meta.get_bond_ratings())

class ETFPerformanceData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = f"https://finance.yahoo.com/quote/{ticker}/performance?p={ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_trailing_period_available(self):
        """

        :return:
        """
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][3:30]
        res, index = [composed[0]], 0
        for elem in composed:
            if index == 3:
                res.append(elem)
                index = 0
            index += 1
        return res

    def get_fund_trailing_performance_vs_benchmark(self, trailing_period):
        """

        :return:
        """
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][3:30]
        res, index = [], 0
        for elem in composed:
            if elem == trailing_period or (1 <= index < 3):
                res.append(elem)
                index += 1
            if index == 3:
                break
        return res

    def get_years_available_for_total_return(self):
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][34:]
        res, index = [composed[0]], 0
        for elem in composed:
            if index == 4:
                res.append(elem)
                index = 0
            index += 1
        return res

    def get_total_return_fund_vs_benchmark(self, year):
        """

        :return:
        """
        composed = [elem.text for elem in self.soup.find_all("span", attrs={"class": "Fl(start)"})
                    if not elem.find_all("span", attrs={"class": "Fl(start)"})][34:]
        res, index = [], 0
        for elem in composed:
            if elem == year or (elem != "" and (1 <= index < 3)):
                res.append(elem)
                index += 1
            if index == 3:
                break
        return res

    def get_fund_overview(self):
        composed = self.soup.find_all("span", attrs={"class": "Fl(end)"})
        return composed


# meta = ETFPerformanceData("VUG")
# print(meta.get_trailing_period_available())
# print(meta.get_fund_trailing_performance_vs_benchmark('1-Month'))R
# print(meta.get_years_available_for_total_return())
# print(meta.get_total_return_fund_vs_benchmark('2020'))
# print(meta.get_fund_overview())

class ETFRiskData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = f"https://finance.yahoo.com/quote/{ticker}/risk?p={ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_fund_risk_data_types(self):
        composed = [elem.find("span").text for elem in
                    self.soup.find_all(name='div', class_='Fl(start)') if elem.find("span") is not None][4:]
        res, index = [composed[0]], 0
        for elem in composed:
            if index == 4:
                res.append(elem)
                index = 0
            index += 1
        return res

    def get_fund_risk_data_by_type(self, risk_type):
        composed = [elem.find("span").text for elem in
                    self.soup.find_all(name='div', class_='Fl(start)') if elem.find("span") is not None][4:]
        res, index = [], 0
        for elem in composed:
            if elem == risk_type or (1 <= index < 4):
                res.append(elem)
                index += 1
            if index == 4:
                break
        return res


# meta = ETFRiskData("VUG")
# print(meta.get_fund_risk_data_types())
# print(meta.get_fund_risk_data_by_type("Treynor Ratio"))
