import json
import re

from loguru import logger

from service.cache import cache
from service.notifier import ConsoleNotifier


class Product:
    def __init__(
        self,
        path_to_image: str,
        product_title: str,
        product_price: str,
    ) -> None:
        self.path_to_image = path_to_image
        self.product_title = product_title
        self.product_price = self.get_price(product_price)

    @staticmethod
    def get_price(value: str) -> str:
        """
        Extract float price from the string
        :param value:
        :return:
        """
        pattern = r"[-+]?\d*\.\d+|\d+"
        regex = re.findall(pattern, value)

        return regex[0] if regex else "Price not available"

    def _save(self) -> "Product":
        """
        Save product in cache
        :return:
        """
        cache.set(self.product_title, json.dumps(self.__dict__))
        return self

    def update_cache(self) -> tuple[bool, "Product"]:
        """
        Update cache if product price is changed or product is not available in cache
        :return: is_updated, Object of Product
        """
        cached_product = cache.get(self.product_title)
        if not cached_product:
            return True, self._save()

        cached_product = json.loads(cached_product.decode("utf-8"))
        if cached_product["product_price"] != self.product_price:
            return True, self._save()

        return False, self

    @staticmethod
    def _notify_user(message: str) -> None:
        """
        Generate a report of scrapped data and notify the user
        """
        ConsoleNotifier.notify(message)

    @classmethod
    async def export(cls) -> None:
        """
        Export product details to a csv file
        :return:
        """
        headers = ["path_to_image", "product_title", "product_price"]
        cache.export(filename="product", headers=headers)
        cls._notify_user("Data has been successfully exported.")
