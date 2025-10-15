from app import create_app, db
import os
import sys

try:
    app = create_app()
    print(f"Flask app created successfully")
except Exception as e:
    print(f"Error creating Flask app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    try:
        port = int(os.environ.get('PORT', 8080))
        print(f"Starting Flask app on 0.0.0.0:{port}")
        app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

