import abc
import asyncio

import requests
from bs4 import BeautifulSoup
from loguru import logger

from models.product import Product
from service.notifier import ConsoleNotifier


class Settings:
    URL = "https://dentalstall.com/shop/"
    PAGE_DEPTH = 1
    PROXY = None

    RETRY_COUNT = 3
    RETRY_DELAY = 5


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

    def _scrap_page(self, url: str) -> BeautifulSoup:
        """
        Scrap the page using the provided URL and proxy
        """
        logger.info(f"Scraping page: {url}")

        # Proxy setup
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy else None

        response = requests.get(url, proxies=proxies)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html5lib")

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
        """ """
        url = f"{self.url}/page/{page}"
        scrapped_data = self._scrap_page(url)
        extracted_data = self._extract_data(scrapped_data)
        self.item_scraped.extend(extracted_data)
        self._store_data(extracted_data)

    async def run(self) -> None:
        """
        Run the scrapper, scrap the data, store it and notify the user.
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
        logger.info(f"Storing {len(extracted_data)} products")

        item_updated = []
        for product in extracted_data:
            is_updated, _ = product.update_cache()
            if is_updated:
                item_updated.append(product)

        self.item_updated.extend(item_updated)
        logger.info(f"Updated {len(item_updated)} products")

    async def run(self) -> None:
        await super().run()
        await Product.export()
