FROM ubuntu:16.04

MAINTAINER UDIVS

RUN apt-get -y update && apt-get install -y python3-pip python3-dev

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Copy the rest of the files
COPY templates /app/template
COPY static /app/static
COPY *.py /app

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]

CMD [ "udivs.py" ]