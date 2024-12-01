from fastapi import FastAPI, Query

from service.scrapper import ProductScrapper

app = FastAPI()


@app.get("/scrape")
async def scrape_catalog(
    pages: int = Query(default=None), proxy: str = Query(default=None)
):
    scraped_data = []
    scrapper = ProductScrapper(pages=pages, proxy=proxy)
    scrapper.run()

    return scrapper.generate_report()
