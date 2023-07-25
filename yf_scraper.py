from bs4 import BeautifulSoup
import requests

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
}


class FinancialStatementsData:

    def __init__(self, ticker, sheet):
        """
        :param ticker: the stock symbol as a string value
        :param sheet: Just three possible string values: "balance-sheet", "financials" (income statement), "cash-flow"
        """
        self.ticker = ticker
        self.sheet = sheet
        self.url = "https://finance.yahoo.com/quote/{}/{}?p={}".format(ticker, sheet, ticker)
        self.soup = BeautifulSoup(requests.get(self.url, headers=headers).content, 'html.parser')

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

        final_parsing, char = [], ""
        for elem in global_parsing:
            if elem == "/":
                final_parsing.append(char.strip())
                char = ""
            else:
                char += elem + " "
        final_parsing.append(char.strip())

        # Handle exceptions
        final_res = [elem for elem in final_parsing[:-1]]
        n = len(final_parsing)
        char, dot_counter = "", 0

        if n < 6 and final_parsing[-1] in ["-" * (6 - (n - 1)), "0" * (6 - (n - 1))]:
            for elem in final_parsing[-1]:
                final_res.append(elem)

        elif n < 6:
            for elem in final_parsing[-1]:
                if elem == "-":
                    final_res.append(elem)
                    continue
                elif elem == ".":
                    dot_counter += 1
                if dot_counter >= 1:
                    dot_counter += 1
                char += elem
                if dot_counter == 4:
                    final_res.append(char)
                    char, dot_counter = "", 0

        return final_res

    def get_data_types(self):
        """
        This method allows you to have a visibility of the data you can retrieve from the company's income statement.
        It refers to the "Breakdown" columns
        :return: The list of all data types you can retrieve. You will be able to loop over.
        """
        types = []
        for elem in self.soup.find_all("div", attrs={"data-test": "fin-row"}):
            types.append(self.data_parsing(elem.text.strip())[0])
        return types

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
        for elem in self.soup.find_all("div", attrs={"data-test": "fin-row"}):
            data = self.data_parsing(elem.text.strip())
            if data[0] == type_of_information:
                try:
                    if data[periods.index(period) + 1] == "-":
                        raise ValueError
                    return data[periods.index(period) + 1]
                except ValueError:
                    return f"No {data[0]} data for the {period} period"


# print(FinancialStatementsData("AMZN", "financials").url)
# print(FinancialStatementsData("AMZN", "financials").get_accounting_data("Total Revenue", "year_1"))


class StockStatisticsData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = "https://finance.yahoo.com/quote/{}/key-statistics?p={}".format(ticker, ticker)
        self.soup = BeautifulSoup(requests.get(self.url, headers=headers).content, 'html.parser')

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


# print(StockStatisticsData("AMZN").get_stats_types())
# print(StockStatisticsData("AMZN").get_data_types_by_stats_type('Share Statistics'))
# print(StockStatisticsData("AMZN").get_statistics('Share Statistics', 'Avg Vol (3 month) 3'))

class CrossCurrencyData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker.split("=")[0]
        self.url = f"https://finance.yahoo.com/quote/{self.ticker}%3DX?p={self.ticker}%3DX"
        self.soup = BeautifulSoup(requests.get(self.url, headers=headers).content, 'html.parser')

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


# print(CrossCurrencyData("EURUSD=X").get_current_price())
# print(CrossCurrencyData("EURUSD=X").get_last_52_week_range())
# print(CrossCurrencyData("EURUSD=X").get_day_range())
# print(CrossCurrencyData("EURUSD=X").get_previous_close())
# print("/n*********/n")

class BenchmarkData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker.split("=")[0]
        self.url = f"https://finance.yahoo.com/quote/%5E{self.ticker}?p=%5E{self.ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=headers).content, 'html.parser')

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


# print(BenchmarkData("GSPC").get_current_price())
# print(BenchmarkData("GSPC").get_last_52_week_range())
# print(BenchmarkData("GSPC").get_previous_close())

class ETFData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=headers).content, 'html.parser')

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


print(ETFData("PICK").get_current_price())
print(ETFData("PICK").get_last_52_week_range())
print(ETFData("PICK").get_day_range())

