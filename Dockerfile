# Use the official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Create the uploads folder inside static
RUN mkdir -p static/uploads

# Expose the port Flask runs on
EXPOSE 7860

# Command to run the app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]