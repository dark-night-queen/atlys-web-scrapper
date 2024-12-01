class Product:
    def __init__(
        self,
        path_to_image: str,
        product_title: str,
        product_price: str,
        short_description: str,
    ) -> None:
        self.path_to_image = path_to_image
        self.product_title = product_title
        self.product_price = product_price
        self.short_description = short_description
