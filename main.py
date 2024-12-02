import asyncio
import sys

from loguru import logger
from dotenv import load_dotenv


async def run_uvicorn(host="127.0.0.1", port=8000):
    logger.info(f"Starting the API service at: http://{host}:{port}")
    process = await asyncio.create_subprocess_exec(
        "uvicorn",
        "service.api:app",
        "--host",
        host,
        "--port",
        str(port),
    )
    await process.wait()


async def main():
    try:
        await asyncio.gather(
            run_uvicorn(),
        )
    except KeyboardInterrupt:
        logger.warning("\nRedis server stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    load_dotenv(override=True)
    asyncio.run(main())
