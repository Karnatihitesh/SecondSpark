import os
import sys
from app import create_app

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    if '--seed' in sys.argv:
        from seed_data import seed_database
        seed_database()
        print("Database seeded successfully.")
    
    port = int(os.environ.get('PORT', 5000))
    print(f"SecondSpark server starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
