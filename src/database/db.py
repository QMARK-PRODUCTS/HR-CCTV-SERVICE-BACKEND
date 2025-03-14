from sqlmodel import create_engine, SQLModel, Session
import os
from dotenv import load_dotenv
import src.app.v1.CameraSources.models
import src.app.v1.People.models
import src.app.v1.Users.models

load_dotenv()

# Define the database URL
DATABASE_URL = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}"

# Create the engine for MySQL
engine = create_engine(DATABASE_URL)

def initDB():
    # Create the databases
    SQLModel.metadata.create_all(engine)
    
def get_session():
    with Session(engine) as session:
        yield session
    
    
    
# docker run --name test-cctv \
#   -e MYSQL_ROOT_PASSWORD=cctv_test \
#   -e MYSQL_DATABASE=qviz \   # Automatically create the qviz database
#   -p 3306:3306 \             # Expose MySQL port to host
#   -d mysql:8.2