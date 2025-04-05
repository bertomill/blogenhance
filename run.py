from app import create_app
import argparse

app = create_app()

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the BlogEnhance application')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on (default: 5001)')
    args = parser.parse_args()
    
    # Run the app with the specified port
    app.run(debug=True, port=args.port) 