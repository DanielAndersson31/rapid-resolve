FROM python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set the working directory
WORKDIR /app

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application code
COPY . .

# Set environment variables for UV
ENV UV_SYSTEM_PYTHON=1

# Expose port (adjust as needed)
EXPOSE 8000

# Run the application using uv
CMD ["uv", "run", "your-app-command"]