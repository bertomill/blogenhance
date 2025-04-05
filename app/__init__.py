from flask import Flask
from dotenv import load_dotenv
from flask_talisman import Talisman
from flask_login import LoginManager
from app.models import db, User, get_user
from flask_migrate import Migrate
import os
from datetime import datetime
from sqlalchemy import inspect

load_dotenv()  # Load environment variables from .env file

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-goes-here')
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///blog_enhance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    # For development, we'll simply disable CSP
    # In production, you would want to set up proper CSP rules
    Talisman(
        app, 
        content_security_policy=None,  # Disable CSP for development
        force_https=False
    )
    
    # Initialize Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user(user_id)
    
    # Create tables if they don't exist
    with app.app_context():
        # Don't create tables here since we're using migrations
        # db.create_all()
        
        # For first time setup, check if users table exists and has any users
        try:
            # If no users exist and the table is successfully queried, create a default admin
            inspector = inspect(db.engine)
            if inspector.has_table('users') and not User.query.first():
                admin = User(
                    username='admin',
                    email='admin@example.com'
                )
                admin.set_password('adminpassword')
                admin.update_profile({
                    'personality': 'thoughtful and analytical',
                    'writing_style': 'clear and conversational',
                    'expertise': 'digital marketing and content strategy',
                    'background': 'Several years of experience in content creation and blog management'
                })
                db.session.add(admin)
                db.session.commit()
        except Exception as e:
            # If there's an error (like missing columns), we'll handle it with migrations
            print(f"Database initialization error: {e}")
            print("Run 'flask db migrate' and 'flask db upgrade' to update the database schema")
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register authentication blueprint
    from app.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    # Register payment blueprint
    from app.payment import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/payment')
    
    # Add context processor for template variables
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    return app 