FROM python:3.10-slim-bookworm

# Set up environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set the working directory
WORKDIR /media_proxy

# Copy only the requirements file first to leverage Docker caching
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libmagic-dev \
    libmagic1 \
    python3-magic \
    file

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Expose the port your application will run on
EXPOSE 8080

COPY set_env.sh /media_proxy/set_env.sh
RUN chmod +x /media_proxy/set_env.sh
CMD ["bash", "-c", "/media_proxy/set_env.sh && env && python app.py"]
