import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    import uvicorn

    from app.core.config import envs
    from app.core.logging import setup_logging

    setup_logging()

    reload = True if envs.ENVIRONMENT == "local" else False

    uvicorn.run(
        "app.app:app",
        port=envs.APP_PORT,
        host=envs.APP_HOST,
        reload=reload
    )
