# 📊 Crypto Price Tracker

This project is designed for **real-time cryptocurrency price tracking** using **Airflow, MinIO, Kafka, PySpark, and PostgreSQL**. The data is fetched from the Binance API and processed through a data pipeline.


## 🚀 Features
- Fetches real-time cryptocurrency price data from **Binance API**.
- Stores raw data in **MinIO**, with **a separate bucket created daily** for each day's data.
- Streams data using **Kafka** for real-time processing.
- Processes and aggregates data with **PySpark**.
- Saves structured and aggregated historical data in **PostgreSQL**.
- Automates workflows using **Airflow DAGs**.

## 🏗️ Tech Stack
- **Apache Airflow** – Workflow automation.
- **MinIO** – Object storage.
- **Apache Kafka** – Streaming data processing.
- **PySpark** – Data processing.
- **PostgreSQL** – Database storage.
- **Docker** – Containerization.

## 📦 Installation & Setup

### 1️⃣ Clone the repository
```sh
git clone https://github.com/Andrewsis/pet_project_data_engineering
cd pet_project_data_engineering
```

### 2️⃣ Start with Docker Compose
```sh
docker-compose up -d
docker-compose up airflow-init
```
⚠️ Ensure Docker and Docker Compose are installed


## 📈 Monitoring & UI Access
  - **MinIO UI**: http://localhost:9001
  - **MinIO server**: localhost:9000 
  - **Postgres**:localhost:5433
  - **Airflow Webserver**: http://localhost:8080
  - **Zookeeper**: localhost:2181
  - **Kafka**: localhost:9092
