FROM python:3.12-slim
WORKDIR /app
COPY . /app
ENV OMNIFORGE_PORT=8787
EXPOSE 8787
CMD ["python", "-m", "omniforge", "gateway"]
