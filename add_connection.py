from airflow import settings
from airflow.models import Connection

# Creating a connection to Postgres database
postgres_localhost = Connection(
    conn_id="postgres_localhost",
    conn_type="postgres",
    host="host.docker.internal",
    login="airflow",
    password="airflow",
    port=5433,
    schema="test"
)

# Creating a connection to MinIO bucket
minio_conn = Connection(
    conn_id="minio_conn",
    conn_type="aws",
    login="ROOTUSER",
    password="CHANGEME123",
    extra={
    "aws_access_key_id": "ROOTUSER",
    "aws_secret_access_key": "CHANGEME123",
    "endpoint_url": "http://minio:9000"
    }
)

spark_conn = Connection(
    conn_id="spark_default",
    conn_type="spark",
    host="yarn",  # Initial host value (will change to local[*])
)

session = settings.Session()

existing_postgres_localhost = session.query(Connection).filter(Connection.conn_id == "postgres_localhost").first()
if not existing_postgres_localhost:
    session.add(postgres_localhost)
    session.commit()
    print("Connection to PostgreSQL successfully created!")
else:
    print("Connection to PostgreSQL already exists!.")


existing_minio_conn = session.query(Connection).filter(Connection.conn_id == "minio_conn").first()
if not existing_minio_conn:
    session.add(minio_conn)
    session.commit()
    print("Connection to MinIO successfully created!")
else:
    print("Connection to MinIO already exists!.")


# Handling Spark connection (changing host to local[*])
existing_spark_conn = session.query(Connection).filter(Connection.conn_id == "spark_default").first()
if existing_spark_conn:
    existing_spark_conn.host = "local[*]"  # Changing host to local[*]
    session.commit()
    print("Spark connection host updated to 'local[*]'!")
else:
    session.add(spark_conn)
    session.commit()
    print("Spark connection to local[*] successfully created!")

session.close()
