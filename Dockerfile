FROM --platform=linux/amd64 selenium/standalone-chrome:126.0.6478.114

# Set the working directory
WORKDIR /suno-scraper

# Copy the current directory contents into the container
COPY . /suno-scraper/

# Install Python, Pip, and additional dependencies in one layer
USER root

RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y wget
RUN apt-get install -y unzip
RUN rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ntp && ntpd -gq

# Install Python dependencies
RUN pip3 install -r requirements.txt

# Command to run on container start
CMD ["python3", "create_song.py"]