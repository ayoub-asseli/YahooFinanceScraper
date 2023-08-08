# Beautiful Soup 4
from bs4 import BeautifulSoup

# Support
from fake_useragent import UserAgent
import requests

# global variable
user_agent = {"User-Agent": UserAgent().chrome}


class ETFData:

    def __init__(self, ticker):
        """
        :param ticker: the stock symbol as a string value
        """
        self.ticker = ticker
        self.url = f"https://finance.yahoo.com/quote/{ticker}?p={ticker}"
        self.soup = BeautifulSoup(requests.get(self.url, headers=user_agent).content, 'html.parser')

    def get_current_price(self):
        return float([price.text for price in self.soup.find_all("fin-streamer", attrs={"data-test": "qsp-price"})
                if not price.find_all("fin-streamer", attrs={"data-test": "qsp-price"})][0].replace(",", ""))

    def get_last_52_week_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[0].find_all('td') if not t.find_all('td')]
        return [elem.text.replace(",", "") for elem in tds][11]

    def get_day_range(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[0].find_all('td') if not t.find_all('td')]
        return [elem.text.replace(",", "") for elem in tds][9]

    def get_net_assets(self):
        tables = [t for t in self.soup.find_all('table') if not t.find_all('table')]
        tds = [t for t in tables[1].find_all('td') if not t.find_all('td')]
        return [elem.text for elem in tds][1]

    def get_nav(self):
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


meta = ETFHoldingsData("PICK")
print(meta.get_top_holdings())
print(meta.get_sector_weightings())
print(meta.get_equity_holdings())
print(meta.get_bond_ratings())


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

