import os

import requests
from fastapi import FastAPI, Query, HTTPException, Depends
from loguru import logger

from service.scrapper import ProductScrapper

app = FastAPI()

# Authentication
TOKEN = os.getenv("API_TOKEN")


def authenticate(token: str) -> None:
    """
    Authenticate the request using auth token defined in .env file
    """
    if token != TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/scrape")
async def scrape_catalog(
    pages: int = Query(default=None),
    proxy: str = Query(default=None),
    token: str = Depends(authenticate),
):
    """
    Scrape the catalog using the provided parameters
    :param pages:
    :param proxy:
    :param token:
    :return: A report detailing the data scrapped from current cycle + stored in db
    """
    scraped_data = []
    scrapper = ProductScrapper(pages=pages, proxy=proxy)

    try:
        await scrapper.run()
    except requests.exceptions.ProxyError:
        raise HTTPException(status_code=400, detail="Unable to connect to proxy")
    except Exception as e:
        logger.error(f"Error occurred while scrapping: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    return scrapper.generate_report()
