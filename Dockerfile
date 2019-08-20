FROM python:3.7.4
MAINTAINER UDIVS

WORKDIR /usr/local/bin

COPY requirements.txt .
COPY templates ./template/
COPY static ./static/
COPY *.py ./

RUN pip3 install numpy
RUN pip3 install pandas
RUN pip3 install -r requirements.txt

CMD ["udivs.py"]
