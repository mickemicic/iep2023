FROM python:3

RUN mkdir -p /opt/src/store/courier
WORKDIR /opt/src/store

COPY configuration.py ./configuration.py
COPY models.py ./models.py
COPY requirements.txt ./requirements.txt
COPY roleDecorator.py ./roleDecorator.py
COPY courier/application.py ./courier/application.py
COPY blokic.py ./blokic.py

COPY sol_abi.abi ./sol_abi.abi
COPY sol_bytecode.bin ./sol_bytecode.bin

RUN pip install -r ./requirements.txt

ENV PYTHONPATH="/opt/src/store/"

ENTRYPOINT ["python", "courier/application.py"]