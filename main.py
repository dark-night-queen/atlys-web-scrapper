import asyncio
import sys

from loguru import logger


async def run_redis_server(port=6379):
        # Check if Redis is installed
        result = await asyncio.create_subprocess_exec(
            "redis-server",
            "--version",
        )
        await result.wait()
        if result.returncode != 0:
            logger.error(
                "Redis server is not installed or not in PATH. Please install it and try again."
            )
            sys.exit(1)

        # Start Redis server
        logger.info("Starting Redis server...")
        process = await asyncio.create_subprocess_exec(
            "redis-server", "--port", str(port)
        )
        await process.wait()


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
            run_redis_server(),
        )
    except KeyboardInterrupt:
        logger.warning("\nRedis server stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
