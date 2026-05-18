"""入口。"""
import os, ssl
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
ssl._create_default_https_context = ssl._create_unverified_context

from app.route.route import create_app
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
