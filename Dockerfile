# Official Playwright image (includes browsers + OS deps)
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

# Set working directory at repo root in image
WORKDIR /app

# Copy only backend service files into the image
COPY backend/ ./backend/

# Install Python dependencies from backend
RUN pip install --no-cache-dir -r backend/requirements.txt

# Run the API from backend folder so local imports (e.g., run_pipeline) keep working
WORKDIR /app/backend

# Expose port (Render uses 10000 by default)
EXPOSE 10000

# Start your FastAPI app
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "10000"]
