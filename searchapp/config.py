from os import path

basedir = path.abspath(path.dirname(__file__))

class Config:
    # XAPIAN_PATHS allows you to maintain multiple indices and
    # direct documents or queries to one of them. All authentication
    # is done globally, so you can't really use this to run multiple
    # databases if you have separate authentication requirements.
    # There should be a 'default' value present.
    XAPIAN_PATHS = {'default': 'searchapp/index/xapian.db',
                    'debug': 'searchapp/index/test.xapian.db'}
    TESTING = False
    APPLICATION_ROOT='/'
    AUTH_TOKENS = set()

class ProdConfig(Config):
    FLASK_ENV = 'production'
    XAPIAN_PATHS = {'default': '/var/www/wsgi/cicsearch/searchapp/index/xapian.db',
                    'debug': '/var/www/wsgi/cicsearch/searchapp/index/test.xapian.db'}
    AUTH_TOKENS = {'changed_in_production'}
    
class DebugConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = True
