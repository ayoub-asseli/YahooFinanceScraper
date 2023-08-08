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
import time

# global variable
user_agent = {"User-Agent": UserAgent().chrome}
delay = 120
ignored_exceptions = (NoSuchElementException, StaleElementReferenceException,)


class ScreenerCreator:

    def __init__(self, asset_type):
        self.asset_type = asset_type
        if asset_type == "Stock":
            self.url = "https://finance.yahoo.com/screener/new"
        elif asset_type == "ETF":
            self.url = "https://finance.yahoo.com/screener/etf/new"
        elif asset_type == "Mutual Fund":
            self.url = "https://finance.yahoo.com/screener/mutualfund/new"

    def screener_builder(self, numbers=100, countries=("France", "United Kingdom"), rem_usa=True,
                         caps=("Small Cap", "Mid Cap", "Large Cap", "Mega Cap"),
                         mng_star_ratings=("*", "**", "***", "****", "*****")):
        options = Options()
        # options.add_argument('--headless')
        options.add_argument(f"--user-agent={user_agent}")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(self.url)
        reject_all = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
            expected_conditions.presence_of_element_located(
                (By.XPATH, '//button[@class="btn secondary reject-all"]')))
        action = ActionChains(driver)
        action.click(on_element=reject_all)
        action.perform()
        # Set the Research Parameters
        if self.asset_type == "Stock":
            # Areas selection
            add = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, '//*[@id="screener-criteria"]/div[2]/div[1]/div[1]/div[1]/div/div[2]/ul/li[2]/div/div')))
            action.click(on_element=add)
            action.perform()
            for country in countries:
                # add the country
                w_country = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, '//*[@id="dropdown-menu"]/div/div[1]/div/input')))
                action.click(on_element=w_country)
                action.perform()
                # write the country name
                action.send_keys(country)
                action.perform()
                # checkbox
                checkbox = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "input[type^='checkbox']")))
                action.click(on_element=checkbox)
                action.perform()
                # Next one
                next_one = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, '//*[@id="dropdown-menu"]/div/div[1]/div/button')))
                action.click(on_element=next_one)
                action.perform()
            # Remove USA
            if rem_usa:
                rem_usa = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, "[title=\"Remove United States\"]")))
                action.click(on_element=rem_usa)
                action.perform()
            # Cap Size
            for cap in caps:
                cap_0, cap_1 = cap.split()
                cap_type = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                    expected_conditions.presence_of_element_located(
                        (By.CSS_SELECTOR, f"button[title^='{cap_0}'][title$='{cap_1}']")))
                action.click(on_element=cap_type)
                action.perform()
            find_stock = WebDriverWait(driver, delay).until(expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, f"button[data-test^='find-stock']")))
            action.click(on_element=find_stock)
            action.perform()
        elif self.asset_type in ["ETF", "Mutual Fund"]:
            to_remove = "Nasdaq" if self.asset_type == "Mutual Fund" else "NasdaqGM"
            rem_nasdaq = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, f"[title=\"Remove {to_remove}\"]")))
            action.click(on_element=rem_nasdaq)
            action.perform()
            find_assets = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                expected_conditions.presence_of_element_located(
                    (By.CSS_SELECTOR, f"button[data-test^='find-stock']")))
            action.click(on_element=find_assets)
            action.perform()

        data_res, switch, num = [], True, 0
        while len(data_res) < numbers:
            if switch:
                next_page = WebDriverWait(driver, delay, ignored_exceptions=ignored_exceptions).until(
                    expected_conditions.presence_of_element_located(
                        (By.XPATH, '//*[@id="scr-res-table"]/div[2]/button[3]')))
                action.click(on_element=next_page)
                action.perform()
                switch = False
            else:
                driver.get(driver.current_url[:-2] + str(num))
                time.sleep(0.05)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                symbols = [elem.text for elem in soup.find_all("td", attrs={"aria-label": "Symbol"})]
                names = [elem.text for elem in soup.find_all("td", attrs={"aria-label": "Name"})]
                market_cap = [elem.text for elem in soup.find_all("td", attrs={"aria-label": "Market Cap"})]
                data_res += list(zip(symbols, names, market_cap))
                num += 25
                print(data_res)
                print(len(data_res))
        return data_res


meta = ScreenerCreator("Stock")
res = meta.screener_builder(150, countries=("France", "United Kingdom"), caps=("Large Cap", "Mega Cap"),
                            rem_usa=True)
print(res)
print(len(res))
