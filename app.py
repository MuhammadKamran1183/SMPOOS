import os

from dash_app import app

if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8050"))
    app.run(host=host, port=port, debug=False)
