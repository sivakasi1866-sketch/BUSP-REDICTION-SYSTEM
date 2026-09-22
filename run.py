import uvicorn
import os
import sys

if __name__ == "__main__":
    # Ensure tables and seed data exist
    from data.seed_data import seed_database
    try:
        seed_database()
    except Exception as e:
        print(f"Database check/seed: {e}")

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
