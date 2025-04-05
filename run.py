from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Use port from environment variable if available (for deployment)
    port = int(os.environ.get('PORT', 5001))
    # Enable debug mode in development
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', debug=debug, port=port) 