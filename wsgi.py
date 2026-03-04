import os
import sys

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from __init__ import create_app, db

app = create_app()

# Note: Automated background services (Location & Learning) 
# have been removed to prioritize Manual AI Analysis and CPU efficiency.

if __name__ == "__main__":
    with app.app_context():
        # Tables create karega agar nahi bani hain
        db.create_all()
        print("✅ Database initialized successfully")

    # App run karega
    print("🚀 Missing Person AI Platform starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)