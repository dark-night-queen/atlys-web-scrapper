# Web Scrapper


### Installation

Please ensure you have the following dependencies installed on your system:
1. Python > 3.12
2. Redis (caching & main database)
3. uv (python package manager)

UV is used as python package and project manager.

1. To get started please install uv using [here](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer)
2. Run `uv venv` to create a virtual environment
3. Run `uv sync` to install dependencies
4. To add dependencies use `uv add <package-name>`
5. To remove dependencies use `uv remove <package-name>`


### Run in Local

1. To run the scrapper use `uv run main.py`
2. Copy .env.example to .env and add the required environment variables. `cp .env.example .env`


### Test

1. To run the scrapper please hit the api using postman at the following url `http://127.0.0.1:8000/scrape`.
2. The query params should be in the following format
    ```json
    {
        "pages": "5",
        "proxy": "https://abc.com",
        "token": "your_static_token"
    }
    ```
3. The following curl can also be used to test the scrapper:
    ```aiignore
    curl --location 'http://127.0.0.1:8000/scrape?pages=5&token=your_static_token'
    ```
4. The above url, will scrape the data from `https://dentalstall.com/shop/` and return the following as response:
    ```json
   {
        "product": {
            "scraped": {
                "total": 120
            },
            "updated": {
                "total": 120
            }
        }
   }
   ```
5. It will also export the scrapped data in `export_product.csv` file in the root directory.


### Design

#### Requirements
1. Scrape the data from the given url: `https://dentalstall.com/shop/`.
2. The scrapper should include the following settings:
    - Number of pages to scrape
    - Proxy to use
    - Token to authenticate the request
3. The product data should include:
    - Product Title
    - Product Price
    - Path to the product image
4. The scrapper should return the following:
    - Total number of products scraped
    - Total number of products updated
5. The scrapper should store the data within a db of choice.
6. It should have a retry mechanism for the scraping part. For example, if a page cannot be reached because of a destination site server error, we would like to retry it in N seconds.
7. Caching mechanism should be implemented to update the data in case price has been changed.

#### HLD
1. The scrapper will be a simple python script that will scrape the data from the given url.
2. The scrapper will use the following libraries:
    - requests
    - BeautifulSoup
    - redis
3. The scrapper will have the following components:
    - Main scrapper
    - Redis cache {Used for both caching & db, since it's a small scale project. For scaling we case use a sql based db}
    - Notification system
    - Retry mechanism
    - Product data storage
4. The scrapper will have the following flow:
   - The scrapper will hit the given url and scrape the data.
   - If there is an error, the scrapper will retry the request after `Settings.RETRY_DELAY` seconds.
   - The product data will extracted from the scrapped data, which is stored within redis db.
   - The product data will be updated in case of product price has been changed.
   - The data extracted in each cycle is stored within a csv file.
   - The scrapper will return the total number of products scraped and updated.

#### File Structure
You can check the following files for the above flow:
1. `main.py`: Starts the fastapi server using uvicorn.
2. `server/api.py`: Contains the fastapi routes.
3. `scrapper/scrapper.py`: Contains the scrapper logic.
4. `scrapper/cache.py`: Contains the redis connection + storing + retrival + export logic.
5. `scrapper/notifier.py`: Contains the notification logic.
6. `models/product.py`: Contains the product model.
