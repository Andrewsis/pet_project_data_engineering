#!/bin/sh

echo "Waiting for MinIO to start..."
sleep 5

echo "Creating MinIO buckets..."
mc mb data/crypto-currency

echo "Buckets created successfully."
