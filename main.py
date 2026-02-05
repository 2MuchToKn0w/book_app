from fastapi import FastAPI
import uvicorn
import httpx

from app.routers import books, favorites, users
from app.services.open_library import OpenLibraryService

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    http_client = httpx.AsyncClient(base_url="https://openlibrary.org")
    app.state.open_library_service = OpenLibraryService(http_client)
    yield  # here FastAPI handles requests
    # shutdown
    await app.state.open_library_service.client.aclose()


# Connecting lifespan to FastAPI
app = FastAPI(
    title="FastAPI Library",
    version="0.1.0",
    lifespan=lifespan
)


# connecting routers
app.include_router(books.router)
app.include_router(favorites.router)
app.include_router(users.router)


# root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Library API"}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
