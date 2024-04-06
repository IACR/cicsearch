from os import path

basedir = path.abspath(path.dirname(__file__))

class Config:
    XAPIAN_DB_PATH = 'searchapp/index/xapian.db'
    TEST_XAPIAN_DB_PATH = 'searchapp/index/test.xapian.db'
    TESTING = False
    APPLICATION_ROOT='/'
    AUTH_TOKENS = set()

class ProdConfig(Config):
    FLASK_ENV = 'production'
    XAPIAN_DB_PATH = '/var/www/wsgi/cicsearch/searchapp/index/xapian.db'
    TEST_XAPIAN_DB_PATH = '/var/www/wsgi/cicsearch/searchapp/index/test.xapian.db'
    AUTH_TOKENS = {'changed_in_production'}
    
class DebugConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
