from uvicorn import run
from src.web.api import app
from src.settings import Settings


if __name__ == "__main__":
    """This is the main entry point of the application.
    
    It runs the web server on the port specified in the Settings module.
    """
    run(app, host="0.0.0.0", port=Settings.port)
