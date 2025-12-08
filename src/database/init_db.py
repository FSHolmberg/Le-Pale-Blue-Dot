from src.database.models import init_db

if __name__ == "__main__":
    print("Creating database tables...")
    init_db()
    print("Done! Tables created in lpbd_dev")