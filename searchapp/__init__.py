from flask import Flask, request, render_template, current_app

def create_app(config):
    app = Flask('searchapp')
    app.config.from_object(config)
    with app.app_context():
        from . import routes
        app.register_blueprint(routes.search_bp, url_prefix=app.config['APPLICATION_ROOT'])
        return app
