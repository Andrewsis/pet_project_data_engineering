#!/bin/sh

echo "Creating MinIO buckets..."

# Настроить alias для MinIO внутри контейнера MinIO
docker exec minio1 sh -c "mc mb data/crypto-currency &" || { echo "Error creating MinIO bucket"; exit 1; }

echo "Buckets created successfully."
