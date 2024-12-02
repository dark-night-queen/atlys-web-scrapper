import abc
import asyncio

import requests
from bs4 import BeautifulSoup
from loguru import logger

from models.product import Product
from service.notifier import ConsoleNotifier


class Settings:
    URL = "https://dentalstall.com/shop"
    PAGE_DEPTH = 1
    PROXY = None

    RETRY_COUNT = 3
    RETRY_DELAY = 2


class Scrapper:
    def __init__(self, pages: int | None, proxy: str | None) -> None:
        logger.info(f"Initializing scrapper with pages: {pages} and proxy: {proxy}")

        self.url = None
        self.retry_count = Settings.RETRY_COUNT
        self.retry_delay = Settings.RETRY_DELAY

        self.page_depth = pages or Settings.PAGE_DEPTH
        self.proxy = proxy or Settings.PROXY

        self.item_scraped = []
        self.item_updated = []

    def validate_input(self, raise_validation: bool = True) -> bool:
        is_valid = True

        if not isinstance(self.page_depth, int):
            is_valid = False
            if raise_validation:
                raise ValueError("Page depth must be an integer")

        if self.proxy and not isinstance(self.proxy, str):
            is_valid = False
            if raise_validation:
                raise ValueError("Proxy must be a string")

        return is_valid

    async def _scrap_page(self, url: str) -> BeautifulSoup:
        """
        Scrap the page using the provided URL and proxy.
        If failed, will retry the request for the number of times specified in the settings.
        :param url: URL to scrap
        :return: BeautifulSoup object
        """
        logger.info(f"Scraping page: {url}")

        # Proxy setup
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

        for attempt in range(1, self.retry_count + 1):
            try:
                response = requests.get(url, proxies=proxies, timeout=5)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html5lib")

            except requests.RequestException as e:
                logger.warning(
                    f"Attempt {attempt}/{self.retry_count} failed for {url}: {e}"
                )
                if attempt == self.retry_count:
                    raise e
                else:
                    logger.info(
                        f"Retrying in {self.retry_delay} seconds... (Attempt {attempt})"
                    )
                    await asyncio.sleep(self.retry_delay)  # Delay before retrying
            else:
                return soup

    @abc.abstractmethod
    def _extract_data(self, scrapped_data: BeautifulSoup) -> list:
        """
        Extract meaningful data from the scrapped data
        """

    @abc.abstractmethod
    def _store_data(self, *args, **kwargs) -> None:
        """
        Store the scrapped data in the database
        """

    def generate_report(self) -> dict:
        """
        Generate a report of scrapped data + data stored within db
        :return: Dictionary containing the report
        """
        return {
            "product": {
                "scraped": {
                    "total": len(self.item_scraped),
                },
                "updated": {
                    "total": len(self.item_updated),
                },
            }
        }

    async def scrap_data(self, page: int) -> None:
        """
        Scrap data from the given page
        :param page:
        :return:
        """
        url = f"{self.url}/page/{page}"
        scrapped_data = await self._scrap_page(url)
        extracted_data = self._extract_data(scrapped_data)
        self.item_scraped.extend(extracted_data)
        self._store_data(extracted_data)

    async def run(self) -> None:
        """
        Run the scrapper, scrap the data, store it.
        """
        logger.info("Started Scrapping...")
        self.validate_input()

        tasks = [
            asyncio.create_task(self.scrap_data(page))
            for page in range(1, self.page_depth + 1)
        ]
        await asyncio.gather(*tasks)


class ProductScrapper(Scrapper):
    def __init__(self, pages: int | None, proxy: str | None) -> None:
        super().__init__(pages, proxy)
        self.url = Settings.URL

    def _extract_data(self, scrapped_data: BeautifulSoup) -> list:
        """
        Extract product data from the scrapped data.
        :param scrapped_data: Data obtained from crawler
        :return: A list of Product details
        """
        super()._extract_data(scrapped_data)

        products = scrapped_data.findAll(
            "div", attrs={"class": "product-inner clearfix"}
        )
        logger.info(f"Extracting data from {len(products)} products")

        extract_data = []
        for product in products:
            name = product.find("div", attrs={"class": "addtocart-buynow-btn"}).a[
                "data-title"
            ]
            image = product.select_one(".attachment-woocommerce_thumbnail")["src"]
            # price can be unavailable
            price = product.select_one(".woocommerce-Price-amount")
            price = price.text.strip() if price else ""

            product = Product(
                path_to_image=image,
                product_title=name,
                product_price=price,
            )
            extract_data.append(product)
        return extract_data

    def _store_data(self, extracted_data: list[Product]) -> None:
        """
        Store the scrapped data in the redis database
        :param extracted_data: List of Product objects
        """
        logger.info(f"Storing {len(extracted_data)} products")

        item_updated = []
        for product in extracted_data:
            is_updated, _ = product.update_cache()
            if is_updated:
                item_updated.append(product)

        self.item_updated.extend(item_updated)
        logger.info(f"Updated {len(item_updated)} products")

    async def run(self) -> None:
        """
        Run the scrapper, scrap the data, store it in redis, export csv file and notify the user on console.
        """
        await super().run()
        await Product.export()
