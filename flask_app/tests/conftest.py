import logging

def pytest_configure():
    logging.getLogger("azure").setLevel(logging.CRITICAL) 
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger("httpx").setLevel(logging.CRITICAL)

    
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
