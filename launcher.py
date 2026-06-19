import threading
import webbrowser
import uvicorn
from app import app

def start_server():
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )

threading.Thread(
    target=start_server,
    daemon=True
).start()

webbrowser.open(
    "http://127.0.0.1:8000"
)

input("종료하려면 엔터")