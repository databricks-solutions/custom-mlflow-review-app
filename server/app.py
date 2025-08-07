"""FastAPI application for MLflow Review App.

This is the main entry point for the FastAPI application that serves as the backend
for the MLflow Review App. It provides APIs for managing review apps, labeling sessions,
and integrating with MLflow and Databricks services.

The application includes:
- Comprehensive error handling with structured logging
- CORS middleware for frontend integration
- Static file serving for the React frontend
- Health check endpoint
- Modular router organization for different API domains
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.middleware import AuthMiddleware, ErrorHandlerMiddleware
from server.middleware.profiler import DetailedTimingMiddleware, ProfilerMiddleware
from server.middleware.timing import TimingMiddleware
from server.routers import router

# Load environment variables using python-dotenv
load_dotenv('.env')
load_dotenv('.env.local')


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Manage application lifespan."""
  yield


app = FastAPI(
  title='MLflow Review App API',
  description='Backend API for MLflow Review App - manage trace evaluations and labeling sessions',
  version='0.1.0',
  lifespan=lifespan,
)

# Add error handling middleware (must be first to catch all errors)
app.add_middleware(ErrorHandlerMiddleware)

# Add profiling middleware for performance debugging (early in chain)
app.add_middleware(ProfilerMiddleware, slow_threshold_ms=500)
app.add_middleware(DetailedTimingMiddleware)

# Add authentication middleware to extract user tokens
app.add_middleware(AuthMiddleware)

# Add timing middleware for performance tracking
app.add_middleware(TimingMiddleware)

# Add GZip compression middleware for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add CORS middleware
app.add_middleware(
  CORSMiddleware,
  allow_origins=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://localhost:5174',
  ],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

app.include_router(router, prefix='/api', tags=['api'])


@app.get('/health')
async def health():
  """Health check endpoint."""
  return {'status': 'healthy'}


# ============================================================================
# SERVE STATIC FILES FROM CLIENT BUILD DIRECTORY (MUST BE LAST!)
# ============================================================================
# This static file mount MUST be the last route registered!
# It catches all unmatched requests and serves the React app.
# Any routes added after this will be unreachable!

if os.path.exists('client/build'):
  # Mount static files for Vite assets
  assets_dir = 'client/build/assets'
  if os.path.exists(assets_dir):
    app.mount('/assets', StaticFiles(directory=assets_dir), name='vite-assets')

  # Catch-all route for React Router - serve index.html for all non-API routes
  @app.get('/{path:path}')
  async def catch_all(request: Request, path: str):
    """Serve React app index.html for all routes that don't match API endpoints."""
    # If it's an API route, this shouldn't be reached due to router precedence
    # If it's a static asset request (Vite assets), serve it directly
    static_file_path = f'client/build/{path}'
    if path.startswith('assets/') and os.path.exists(static_file_path):
      return FileResponse(static_file_path)

    # For all other routes (React Router routes), serve index.html
    index_path = 'client/build/index.html'
    if os.path.exists(index_path):
      return FileResponse(index_path)
    else:
      # Fallback if build doesn't exist
      return {'error': 'React app not built. Run: cd client && npm run build'}
