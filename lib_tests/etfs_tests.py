import unittest
from yf_scraper_lib.yf_etf_scraper import *

tickers_etf_list = ["XTL", "SPMO", "VPU"]


class ETFDataTest(unittest.TestCase):

    def test_etf_summary_data(self):
        for ticker in tickers_etf_list:
            yf = ETFData(ticker)
            current_price = yf.get_current_price()
            last_52_week_range = yf.get_last_52_week_range().split("-")
            day_range = yf.get_day_range().split("-")
            day_net_asset = yf.get_net_assets()
            day_nav = yf.get_nav()
            inception_date = len(yf.get_inception_date().split("-"))
            expense_ratio = yf.get_expense_ratio()
            self.assertIsInstance(current_price, float)
            self.assertIsInstance(float(last_52_week_range[0]), float)
            self.assertIsInstance(float(last_52_week_range[1]), float)
            self.assertIsInstance(float(day_range[0]), float)
            self.assertIsInstance(float(day_range[1]), float)
            self.assertIsInstance(float(day_net_asset[:-1]), float)
            self.assertIsInstance(float(day_nav[:-1]), float)
            self.assertIsInstance(float(expense_ratio[:-1]), float)
            self.assertEqual(inception_date, 3)

    def test_top_holdings(self):
        for ticker in tickers_etf_list:
            yf = ETFHoldingsData(ticker)

