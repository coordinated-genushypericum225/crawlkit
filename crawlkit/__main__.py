"""Entry point: python -m crawlkit"""
import os
import uvicorn
from crawlkit.api.server import app

port = int(os.environ.get("PORT", "8080"))
uvicorn.run(app, host="0.0.0.0", port=port)
