FROM apache/airflow:2.10.4-python3.11


# JAVA 8 DOWNLOADING START !!! !!!
USER root

# Donwloading java
RUN apt-get update && apt-get install -y wget tar && \
    wget -qO- https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u382-b05/OpenJDK8U-jdk_x64_linux_hotspot_8u382b05.tar.gz | tar xvz -C /opt && \
    mv /opt/jdk8u382-b05 /opt/java8 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
# Устанавливаем JAVA_HOME
ENV JAVA_HOME=/opt/java8
ENV PATH="$JAVA_HOME/bin:$PATH"

# JAVA 8 DOWNLOADING END !!! !!!


USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt

