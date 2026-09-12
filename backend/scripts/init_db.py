import sys
import os
from pathlib import Path

# Add backend dir to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from infrastructure.config import load_env_file, load_config
load_env_file()

config = load_config()

from infrastructure.db import database
from infrastructure.db.database import init_db, Base
init_db(config.db.url)

from infrastructure.db.models import User, ResearchJob

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=database.engine)
    print("Tables created.")

if __name__ == "__main__":
    init()
