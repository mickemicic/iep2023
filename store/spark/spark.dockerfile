FROM bde2020/spark-python-template:3.3.0-hadoop3.3

COPY spark.py /app/

ENV SPARK_APPLICATION_PYTHON_LOCATION /app/spark.py
ENV PRODUCTION=True

CMD [ "python3", "/app/spark.py" ]