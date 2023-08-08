import unittest
import random
from yf_scraper_lib.yf_stocks_scraper import *

tickers_test_list = ["GLE.PA", "BNP.PA", "AAPL"]
benchmark_tickers = ["GSPC", "FCHI", "FTSE"]


class StocksDataTest(unittest.TestCase):

    financial_sheets = ["income-statement", "balance-sheet", "cash-flow"]
    with_driver = False

    def test_data_types(self):
        for sheet in self.financial_sheets:
            for ticker in tickers_test_list:
                yf = FinancialStatementsProfileData(ticker, sheet, driver=self.with_driver)
                data_types = yf.get_data_types()
                if sheet == "income_statement":
                    values_to_test = ["Total Revenue", "Tax Rate for Calcs", "Basic EPS", "Total Unusual Items"]
                    if self.with_driver:
                        values_to_test = ["Net Interest Income", "Non Interest Income",
                                          "Net Income Including Non-Controlling Interests", "Other Special Charges"]
                    self.assertIn(random.choice(values_to_test), data_types)
                elif sheet == "balance-sheet":
                    values_to_test = ["Total Assets", "Net Tangible Assets", "Net Debt", "Ordinary Shares Number"]
                    if self.with_driver:
                        values_to_test = ["Capital Stock", "Common Stock", "Other Liabilities",
                                          "Cash, Cash Equivalents & Federal Funds Sold"]
                    self.assertIn(random.choice(values_to_test), data_types)
                elif sheet == "cash-flow":
                    values_to_test = ["Operating Cash Flow", "Financing Cash Flow", "Capital Expenditure",
                                      "Free Cash Flow"]
                    if self.with_driver:
                        values_to_test = ["Changes in Cash", "Beginning Cash Position"]
                    self.assertIn(random.choice(values_to_test), data_types)

    def test_financial_data(self):
        periods = ["year_1", "year_2", "year_3", "year_4"]
        for sheet in self.financial_sheets:
            yf = FinancialStatementsProfileData("GLE.PA", sheet, driver=self.with_driver)
            if sheet == "income_statement":
                accounting_data = yf.get_accounting_data("Total Revenue", periods)
                self.assertEqual(accounting_data, [38649000.0, 36248000.0, 31823000.0, 34131000.0])
                if self.with_driver:
                    accounting_data = yf.get_accounting_data("Fees And Commissions", periods)
                    self.assertEqual(accounting_data, [5099000.0, 5227000.0, 4840000.0, 5177000.0])
            elif sheet == "balance-sheet":
                accounting_data = yf.get_accounting_data("Total Capitalization", periods)
                self.assertEqual(accounting_data, [219779000.0, 216220000.0, 214810000.0, 300052000.0])
                if self.with_driver:
                    accounting_data = yf.get_accounting_data("Common Stock", periods)
                    self.assertEqual(accounting_data, [1062000.0,	1067000.0, 1067000.0, 1067000.0])
            elif sheet == "cash-flow":
                accounting_data = yf.get_accounting_data("Investing Cash Flow", periods)
                self.assertEqual(accounting_data, [-9012000.0, -10118000.0, -6863000.0, -6976000.0])
                if self.with_driver:
                    accounting_data = yf.get_accounting_data("Effect of Exchange Rate Changes", periods)
                    accounting_data = [float(elem) for elem in accounting_data]
                    self.assertEqual(accounting_data, [2354000.0, 2154000.0, -2596000.0, 1386000.0])

    def test_current_price(self):
        for ticker in tickers_test_list:
            yf = StocksProfileData(ticker)
            self.assertIsInstance(yf.get_current_price(), float)

    def test_stock_sector_data(self):
        for ticker in tickers_test_list:
            yf = StocksProfileData(ticker)
            sector = yf.get_stock_sector()
            if ticker == "GLE.PA":
                self.assertEqual(sector, "Financial Services")
            elif ticker == "BNP.PA":
                self.assertEqual(sector, "Financial Services")
            elif ticker == "AAPL":
                self.assertEqual(sector, "Technology")

    def test_stock_industry_data(self):
        for ticker in tickers_test_list:
            yf = StocksProfileData(ticker)
            sector = yf.get_stock_industry()
            if ticker == "GLE.PA":
                self.assertEqual(sector, "Banks—Regional")
            elif ticker == "BNP.PA":
                self.assertEqual(sector, "Banks—Regional")
            elif ticker == "AAPL":
                self.assertEqual(sector, "Consumer Electronics")

    def test_stats_data_types(self):
        for ticker in tickers_test_list:
            yf = StockStatisticsData(ticker)
            stats_data_types = yf.get_stats_types()
            values = ["Valuation Measures", "Stock Price History", "Share Statistics", "Fiscal Year", "Profitability",
                      "Management Effectiveness", "Income Statement", "Dividends & Splits"]
            self.assertIn(random.choice(values), stats_data_types)

    def test_stats_data_types_by_data_type(self):
        for ticker in tickers_test_list:
            yf = StockStatisticsData(ticker)
            stats_data_types = ["Balance Sheet", "Cash Flow Statement"]
            for stats_data_type in stats_data_types:
                stats_data_types_by_data_type = yf.get_data_types_by_stats_type(stats_data_type)
                if stats_data_type == "Balance Sheet":
                    values = ["Total Cash (mrq)", "Total Cash Per Share (mrq)", "Total Debt (mrq)",
                              "Total Debt/Equity (mrq)", "Current Ratio (mrq)", "Book Value Per Share (mrq)"]
                    self.assertEqual(values, stats_data_types_by_data_type)
                elif stats_data_type == "Cash Flow Statement":
                    values = ["Operating Cash Flow (ttm)", "Levered Free Cash Flow (ttm)"]
                    self.assertEqual(values, stats_data_types_by_data_type)

    def test_get_stats(self):
        yf = StockStatisticsData("GLE.PA")
        stat_types = ["Share Statistics", "Profitability", "Dividends & Splits"]
        data_types = ["% Held by Insiders", "Profit Margin", "Payout Ratio"]
        values = ["8.38%", "19.89%", "101.92%"]
        for stat_type, data_type, value in zip(stat_types, data_types, values):
            data = yf.get_statistics(stat_type, data_type)
            self.assertEqual(data, value)

    def test_benchmark_data(self):
        for ticker in benchmark_tickers:
            yf = BenchmarkData(ticker)
            current_price = yf.get_current_price()
            last_52_week_range = yf.get_last_52_week_range().split("-")
            day_range = yf.get_day_range().split("-")
            previous_close = yf.get_previous_close()
            self.assertIsInstance(current_price, float)
            self.assertIsInstance(float(last_52_week_range[0]), float)
            self.assertIsInstance(float(last_52_week_range[1]), float)
            self.assertIsInstance(float(day_range[0]), float)
            self.assertIsInstance(float(day_range[1]), float)
            self.assertIsInstance(previous_close, float)


if __name__ == '__main__':
    unittest.main()
