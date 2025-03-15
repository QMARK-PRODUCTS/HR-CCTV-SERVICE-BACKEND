from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from contextlib import asynccontextmanager
from src.database.db import initDB, engine
from src.app.v1.DetectFaces.api.controller import *
from src.app.v1.routes import router as v1Router
import os, sys, asyncio
from src.app.v1.Functions.models.models import *
from dotenv import load_dotenv
from datetime import datetime, time
from sqlmodel import Session, select
from sqlalchemy.orm import sessionmaker

load_dotenv()


sys.dont_write_bytecode = True

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def process_function(func):
    """Run face detection for a given function"""
    print(f"Starting process for function: {func.name}")
    with SessionLocal() as session:  # Use synchronous session
        await DetectFacesBackground(func, session)
    print(f"Finished process for function: {func.name}")

async def schedule_functions():
    """Continuously checks the database for functions to run at scheduled time slots"""
    while True:
        with SessionLocal() as session:  # Use synchronous session
            now = datetime.now().time()
            functions = session.execute(select(Functions)).scalars().all()
            print(f"Checking functions at {now}")
            
            if not functions:
                print("No functions found.")
            else:
                for func in functions:
                    start_time, end_time = map(lambda x: datetime.strptime(x, "%H:%M").time(), func.timeSlot.split(" - "))
                    print(f"Function {func.name} -> Start: {start_time}, End: {end_time}, Now: {now}")
                    if start_time <= now <= end_time:
                        print(f"✅ Function {func.name} is scheduled to run!")
                        asyncio.create_task(process_function(func))
                    else:
                        print(f"❌ Function {func.name} is NOT within time range.")

        await asyncio.sleep(60)
        
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     initDB()  # Initialize the database

#     yield
    
@asynccontextmanager
async def lifespan(app: FastAPI):
    initDB()  # Initialize the database

    # Start the face detection scheduling task
    loop = asyncio.get_event_loop()
    face_detection_task = loop.create_task(schedule_functions())

    yield  # Server runs here

    # Cleanup when the app shuts down
    face_detection_task.cancel()
    try:
        await face_detection_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    lifespan=lifespan,
    title="CCTV Backend Service",
    version="v1",
    description="This is the backend service for the CCTV project.",    
    )

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(v1Router, prefix="/api/v1")
