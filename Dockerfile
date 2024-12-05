FROM 5hojib/vegapunk:latest
WORKDIR /app
COPY . .
CMD ["bash", "start.sh"]
