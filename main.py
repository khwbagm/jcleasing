import json
import os
import re
import time
import random

from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List
import requests
from logzero import logger
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

date_fetched = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def exception_helper(func):
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func} failed at ({args}, {kwargs}), err: {e}")
            return None

    return wrapped


@dataclass
class PriceInfo:
    price: int = 0
    price_range: str = ""
    date_fetched: str = ""


@dataclass
class UnitInfo:
    unit: str = ""
    building: str = ""
    size: int = 0
    available_date: str = ""
    floorplan_type: str = ""
    floorplan_link: str = ""
    floorplan_note: str = ""
    prices: List[PriceInfo] = None


def wait(b=0.2, a=1):
    time.sleep(b + random.random() * a)


def shorten_floorplan_type(fpt):
    fpt = fpt.lower()
    if "studio" in fpt:
        return "studio"
    return (
        fpt.replace("s", "")
        .replace("bath", "b")
        .replace("bedroom", "b")
        .replace("bed", "b")
        .replace(" ", "")
        .replace(",", "")
        .replace("/", "")
    )


def shorten_price(p):
    return p.replace(",", "").replace("$", "")


def get_units_columbus579(driver):
    def _get_available_floorplan(driver, url_building):
        url = url_building + "#floor-plans-property"
        driver.get(url)
        wait()
        floorplan_boxes = driver.find_elements(
            by=By.CSS_SELECTOR, value="div.floorplans-widget__box"
        )

        results = []
        for box in floorplan_boxes:
            links = box.find_elements(by=By.CSS_SELECTOR, value="a")
            for link in links:
                href = link.get_attribute("href")
                if "/floorplan/" in href:
                    results.append(href)
        return results

    def _remove_brackets(text):
        return re.sub(r"<[^>]+>", "", text)

    def _parse_unit_html(unit):
        try:
            aval, unit, price_n_size_type, _ = unit.text.split("\n")
            price, size_type = price_n_size_type.split(" ", 1)
            size, floorplan_type = size_type.split(" sq. ft. ")
            unit = unit.split(" ")[1]
        except ValueError:
            text = unit.get_attribute("innerHTML").strip()
            lines = _remove_brackets(text).split("\n")
            vals = [x.strip() for x in lines if x.strip() != ""]
            if len(vals) == 5:
                aval_unit, price, size, floorplan_type, _ = vals
                aval, unit = aval_unit.lower().split("unit")
                aval = aval.strip()
                unit = unit.strip()
            elif len(vals) == 6:
                aval, unit, price, size, floorplan_type, _ = vals
            else:
                raise ValueError(f"unexpected values: {vals}")
            # match vals:
            #     case aval, unit, price, size, floorplan_type, _:
            #         pass
            #     case aval_unit, price, size, floorplan_type, _:
            #         aval, unit = aval_unit.lower().split("unit")
            #         aval = aval.strip()
            #         unit = unit.strip()
            #     case _:
            #         raise ValueError(f"unexpected values: {vals}")

        if "now" in aval.lower():
            aval_date = "01/01/1900"
        else:
            aval_date = aval.split(" ")[1]
        aval_m, aval_d, aval_y = aval_date.split("/")
        unit = unit.lower().replace("unit", "").strip()
        size = size.lower().replace("sq. ft.", "").strip()
        size = size.replace(",", "")

        price_info = PriceInfo(
            price=shorten_price(price), price_range="", date_fetched=date_fetched
        )
        return UnitInfo(
            unit=unit,
            size=size,
            floorplan_type=shorten_floorplan_type(floorplan_type),
            available_date=f"{int(aval_y)}-{int(aval_m):02d}-{int(aval_d):02d}",
            prices=[price_info],
        )

    def _get_units_in_floorplan(driver, url_floorplan, building_name):
        driver.get(url_floorplan + "#units")
        wait()
        units = driver.find_elements(by=By.CSS_SELECTOR, value="article.splide__slide")

        results = {}
        for unit in units:
            r = _parse_unit_html(unit)
            r.building = building_name
            results[r.unit] = r
        return list(results.values())

    units = []
    for url_building in [
        "https://ironstate.com/property/50-columbus",
        "https://ironstate.com/property/70-columbus",
        "https://ironstate.com/property/90-columbus",
    ]:
        building_name = url_building.split("/")[-1]
        fps = _get_available_floorplan(driver, url_building)
        for fp in fps:
            units += _get_units_in_floorplan(driver, fp, building_name)
    return units


def get_units_haus25(driver):
    def _get_available_floorplan():
        driver.get("https://livehaus25.com/availability/")
        wait()
        html_content = driver.page_source
        pattern = r"https://livehaus25\.com/availability-detail/\?id=\d+"
        urls = re.findall(pattern, html_content)
        return urls

    def _extract_by_classname(card, classname):
        elem = card.find_element(By.CLASS_NAME, classname)
        if elem:
            return elem.get_attribute("textContent")

    def _parse_haus25_date(date_str):
        if date_str.lower() == "immediately":
            return "1900-01-01"

        date_obj = datetime.strptime(
            f"{date_str.strip()}, {datetime.now().year}", "%b. %d, %Y"
        )
        if date_obj < datetime.now():
            date_obj = datetime.strptime(
                f"{date_str.strip()}, {datetime.now().year + 1}", "%b. %d, %Y"
            )
        return str(date_obj).split(" ")[0]

    def _get_units_in_floorplan(fp_url):
        driver.get(fp_url)
        wait()

        cards = driver.find_elements(By.CSS_SELECTOR, 'div[class*="wpgb-card"]')
        infos = {}
        for card in cards:
            try:
                unit = _extract_by_classname(card, "unit")
            except:
                continue
            # floorplan = _extract_by_classname(card, 'floorplan')
            bedrooms = _extract_by_classname(card, "beds")
            sqft = _extract_by_classname(card, "sqft")
            rent = _extract_by_classname(card, "rent.price")
            move_in_date = _extract_by_classname(card, "move_in_date")
            price_range = _extract_by_classname(card, "rent.price-range")

            price_info = PriceInfo(
                price=shorten_price(rent),
                price_range=shorten_price(price_range).replace("\u2013", "-"),
                date_fetched=date_fetched,
            )
            unit_info = UnitInfo(
                unit=unit,
                building="haus25",
                size=sqft.lower().replace(" sqft", ""),
                available_date=_parse_haus25_date(move_in_date),
                floorplan_type=shorten_floorplan_type(bedrooms),
                prices=[price_info],
            )
            infos[unit] = unit_info
        return infos

    unit_infos = {}
    for fp_url in set(_get_available_floorplan()):
        t = _get_units_in_floorplan(fp_url)
        unit_infos |= t
    return list(unit_infos.values())


def get_units_1grove(driver):
    URL = "http://www.greystar.com/api/floorplans/d33a08e1-b488-495d-ae92-3882ab6e5e65/floorplans"
    resp = requests.get(URL)
    assert resp.status_code == 200, f"status_code = {resp.status_code}"
    floorplans = resp.json()["floorplans"]

    units = []
    for fp in floorplans:
        floorplan_type = f"{int(fp['beds'])}b{int(fp['baths'])}b"
        floorplan_link = "http://www.greystar.com/" + fp["path"]
        floorplan_note = fp["name"]

        for info in fp["unitsAvailable"]:
            unit = info["number"]
            price = info["price"].replace("$", "").replace(",", "")
            size = info["squareFeet"]
            available_date = info["available"]
            if available_date.lower() == "Today":
                available_date = "01/01/1900"

            units.append(
                UnitInfo(
                    unit=unit,
                    building="1grove",
                    size=size,
                    available_date=available_date,
                    floorplan_type=floorplan_type,
                    floorplan_link=floorplan_link,
                    floorplan_note=floorplan_note,
                    prices=[PriceInfo(price=price, date_fetched=date_fetched)],
                )
            )
    return units


def get_units_warrenatyork(driver):
    @exception_helper
    def _parse_unit(item, fp_url):
        floorplan_type = fp_url.split("/")[-1]
        floorplan_link = fp_url

        soup = BeautifulSoup(item.get_attribute("innerHTML"), "html.parser")

        # Find elements by their classes
        apartment_id_element = soup.find("td", class_="td-card-name")
        sqft_element = soup.find("td", class_="td-card-sqft")
        price_element = soup.find("td", class_="td-card-rent")
        available_element = soup.find("td", class_="td-card-available")

        # Extract text from elements
        unit_no = apartment_id_element.text.strip().split("#")[1]
        size = sqft_element.text.strip().split(":")[1].strip()
        price_text = price_element.text.strip().split(":")[1]
        price_text = price_text.replace(" to -", "").replace("$", "").replace(",", "")
        price_low, price_high = price_text.strip().split()
        date = available_element.text.strip().split(":")[1]

        if "/" not in date:
            date = "1/1/1970"
        m, d, y = date.split("/")
        m, d, y = int(m), int(d), int(y)
        date = f"{y:4d}-{m:02d}-{d:02d}"
        price_info = PriceInfo(price_low, f"{price_low} - {price_high}", date_fetched)
        unit_info = UnitInfo(
            unit_no,
            "warren-at-york",
            size,
            available_date=date,
            floorplan_link=floorplan_link,
            floorplan_type=floorplan_type,
            floorplan_note="",
            prices=[price_info],
        )
        return unit_info

    driver.get("https://www.warrenatyork.com/floorplans")
    try:
        time.sleep(10)
        driver.find_element(By.XPATH, '//a[text()="Got It"]').click()
    except:
        time.sleep(10)
        driver.find_element(By.XPATH, '//a[text()="Got It"]').click()
    html_content = driver.page_source
    pattern = r"/floorplans/\w+\d+"
    fp_urls = [
        f"https://www.warrenatyork.com{x}" for x in re.findall(pattern, html_content)
    ]

    units = {}
    for fp_url in fp_urls:
        driver.get(fp_url)
        try:
            driver.find_element(By.XPATH, '//a[text()="Got It"]').click()
        except Exception:
            time.sleep(5)
            driver.find_element(By.XPATH, '//a[text()="Got It"]').click()
        items = driver.find_elements(by=By.CLASS_NAME, value="unit-container")
        for item in items:
            if not item:
                continue
            unit_info = _parse_unit(item, fp_url)
            if not unit_info:
                continue
            units[unit_info.unit] = unit_info
    units = list(units.values())
    return units


def get_units_18park(driver):
    def _parse_unit(texts, building_url):
        floorplan_type = (
            building_url.split("/")[-1]
            .replace("-", "")
            .replace("ed", "")
            .replace("ath", "")
        )
        floorplan_link = ""
        texts = texts.replace("\n", "").lower().split(" select")[0]
        texts = (
            texts.replace("to-", "").replace("#", "").replace(",", "").replace("$", "")
        )
        unit_no, size, price_low, price_high, date = texts.split(" ")
        if "/" not in date:
            date = "1/1/1970"
        m, d, y = date.split("/")
        m, d, y = int(m), int(d), int(y)
        date = f"{y:4d}-{m:02d}-{d:02d}"
        price_info = PriceInfo(price_low, f"{price_low} - {price_high}", date_fetched)
        unit_info = UnitInfo(
            unit_no,
            "18park",
            size,
            available_date=date,
            floorplan_link=floorplan_link,
            floorplan_type=floorplan_type,
            floorplan_note="",
            prices=[price_info],
        )
        return unit_info

    units = {}
    for building_url in [
        "https://www.18park.com/floorplans/studio",
        "https://www.18park.com/floorplans/1-bed-1-bath",
        "https://www.18park.com/floorplans/2-bed-2-bath",
    ]:
        driver.get(building_url)
        for item in driver.find_elements(by=By.CLASS_NAME, value="unit-container"):
            unit = _parse_unit(item.text, building_url)
            units[unit.unit] = unit
    return list(units.values())


def get_units_235grand(driver):
    def _parse_unit(texts, building_url):
        floorplan_type = (
            building_url.split("/")[-1]
            .replace("-", "")
            .replace("edroom", "")
            .replace("athroom", "")
        )
        floorplan_link = ""
        texts = texts.replace("\n", "").lower().split(" select")[0]
        texts = (
            texts.replace("to-", "").replace("#", "").replace(",", "").replace("$", "")
        )
        unit_no, price_low, price_high, date = texts.split(" ")
        price_high = ""
        if "/" not in date:
            date = "1/1/1970"
        m, d, y = date.split("/")
        m, d, y = int(m), int(d), int(y)
        date = f"{y:4d}-{m:02d}-{d:02d}"
        price_info = PriceInfo(price_low, f"{price_low} - {price_high}", date_fetched)
        unit_info = UnitInfo(
            unit_no,
            "235grand",
            size="",
            available_date=date,
            floorplan_link=floorplan_link,
            floorplan_type=floorplan_type,
            floorplan_note="",
            prices=[price_info],
        )
        return unit_info

    def _scrape_floorplan(driver, url, max_retries=3):
        last_exception = None
        for attempt in range(max_retries):
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "unit-container"))
                )
                return [
                    _parse_unit(item.text, url)
                    for item in driver.find_elements(by=By.CLASS_NAME, value="unit-container")
                ]
            except Exception as e:
                last_exception = e
                if hasattr(logger, 'warning'):
                    logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        error_msg = f"Failed to scrape {url} after {max_retries} attempts"
        if hasattr(logger, 'error'):
            logger.error(error_msg)
        raise last_exception or Exception(error_msg)

    units = {}
    building_urls = [
        "https://www.235grand.com/floorplans/studio",
        "https://www.235grand.com/floorplans/1-bedroom---1-bathroom",
        "https://www.235grand.com/floorplans/2-bedroom---2-bathroom",
    ]

    for url in building_urls:
        try:
            scraped_units = _scrape_floorplan(driver, url)
            for unit in scraped_units:
                units[unit.unit] = unit
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            continue  # Continue with next URL even if one fails

    return list(units.values())


class WebDriverContext:
    def __init__(self, debug=False):
        self.debug = debug
        self.driver = None
        
    def __enter__(self):
        max_retries = 3
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                options = Options()
                if not self.debug:
                    options.add_argument("--headless")
                
                self.driver = webdriver.Firefox(options=options)
                self.driver.set_page_load_timeout(30)  # 30 seconds timeout
                return self.driver
                
            except Exception as e:
                last_exception = e
                if hasattr(logger, 'warning'):
                    logger.warning(f"Attempt {attempt + 1} failed to initialize WebDriver: {e}")
                elif 'logger' in globals() and hasattr(logger, 'warning'):
                    logger.warning(f"Attempt {attempt + 1} failed to initialize WebDriver: {e}")
                else:
                    print(f"[WARNING] Attempt {attempt + 1} failed to initialize WebDriver: {e}")
                
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        error_msg = f"Failed to initialize WebDriver after {max_retries} attempts"
        if hasattr(logger, 'error'):
            logger.error(error_msg)
        elif 'logger' in globals() and hasattr(logger, 'error'):
            logger.error(error_msg)
        raise Exception(error_msg) from last_exception
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                error_msg = f"Error while quitting WebDriver: {e}"
                if hasattr(logger, 'error'):
                    logger.error(error_msg)
                elif 'logger' in globals() and hasattr(logger, 'error'):
                    logger.error(error_msg)
                else:
                    print(f"[ERROR] {error_msg}")

def newDriver(debug=False):
    """
    Create a new WebDriver instance with retry logic.
    Note: Prefer using the context manager pattern:
    with newDriver(debug=False) as driver:
        # use driver here
    """
    return WebDriverContext(debug=debug)


def main():
    # Create results directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    funcs = [
        # get_units_235grand,
        # get_units_18park,
        # get_units_warrenatyork,
        get_units_columbus579,
        get_units_haus25,
        get_units_1grove,
    ]
    
    results = []
    output_file = os.path.join(
        "results",
        f"daily-results_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
    )
    
    def log(level, message, **kwargs):
        if hasattr(logger, level):
            getattr(logger, level)(message, **kwargs)
        else:
            print(f"[{level.upper()}] {message}")
    
    try:
        with newDriver(debug=False) as driver:
            for scraper_func in funcs:
                func_name = scraper_func.__name__
                log('info', f"Starting scraper: {func_name}")
                
                try:
                    scraped_data = scraper_func(driver)
                    results.extend(asdict(x) for x in scraped_data)
                    log('info', f"Successfully scraped {len(scraped_data)} items from {func_name}")
                except Exception as e:
                    log('error', f"Error in {func_name}: {e}")
                    if hasattr(logger, 'exception'):
                        logger.exception("Stack trace:")
                    continue  # Continue with next scraper even if one fails
                    
    except Exception as e:
        log('critical', f"Fatal error in main execution: {e}")
        if hasattr(logger, 'exception'):
            logger.exception("Stack trace:")
        raise
        
    # Save results
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        log('info', f"Successfully saved {len(results)} items to {output_file}")
    except IOError as e:
        log('error', f"Failed to save results: {e}")
        if hasattr(logger, 'exception'):
            logger.exception("Stack trace:")
        raise


if __name__ == "__main__":
    main()
