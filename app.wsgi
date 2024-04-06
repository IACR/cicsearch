from pathlib import Path
import sys
sys.path.insert(0, '/var/www/wsgi/cicsearch')
from searchapp import config, create_app

config = config.ProdConfig()
application = create_app(config)
