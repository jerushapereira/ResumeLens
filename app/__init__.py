from flask import Flask, jsonify

from .config import Config
from .routes import main_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.register_blueprint(main_bp)

    @app.errorhandler(413)
    def file_too_large(_error):
        return jsonify({"error": "File is too large. Please upload a resume under 8 MB."}), 413

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "The requested route was not found."}), 404

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({"error": "Something went wrong on the server. Please try again."}), 500

    return app
