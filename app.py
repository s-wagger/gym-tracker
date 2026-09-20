from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager~!    

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize database and login manager
    db.init_app(app)
    login_manager.init_app(app)

    # Root route redirect to fix 404 at http://127.0.0.1:5000/
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.subscription import subscription_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(admin_bp)

    # Create SQLite database tables automatically on startup
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)