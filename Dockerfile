# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Install system build dependencies needed for some Python packages
# Install curl for rustup, then Rust for packages like fastuuid
RUN apt-get update && apt-get install -y gcc python3-dev curl && rm -rf /var/lib/apt/lists/* \
 && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt (upgrade pip first for better wheel handling)
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .