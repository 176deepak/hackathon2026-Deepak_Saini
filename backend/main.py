import warnings
warnings.filterwarnings("ignore")

if __name__ == "__main__":
    import uvicorn

    from app.core.config import envs

    reload = True if envs.ENVIRONMENT == "local" else False

    uvicorn.run(
        "app.app:app",
        port=envs.APP_PORT,
        host=envs.APP_HOST,
        reload=reload,
        reload_dirs=["app"],
        reload_includes=["*.py"],
        reload_excludes=[
            "LOGS/*",
            "LOGS/**",
            "*.jsonl",
            "*.log",
            "*.lock",
            "__pycache__/*",
            "*.pyc",
        ],
    )
