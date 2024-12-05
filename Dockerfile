#base image
FROM 5hojib/vegapunk:latest
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt install ffmpeg
COPY . .
CMD ["bash","start.sh"]
