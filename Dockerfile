FROM python:3.7.4
MAINTAINER UDIVS

WORKDIR /usr/local/bin

COPY templates ./templates/
COPY static ./static/
COPY *.py ./

RUN pip3 install boto3
RUN pip3 install numpy
RUN pip3 install pandas
RUN pip3 install Flask-RESTful
RUN pip3 install requests
RUN pip3 install Flask-JWT
RUN pip3 install flask-jwt-extended
RUN pip3 install PyJWT
RUN pip3 install sendgrid
RUN pip3 install s3transfer
RUN pip3 install bcrypt
RUN pip3 install seaborn
RUN pip3 install Send2Trash
RUN pip3 install unicodecsv
RUN pip install psycopg2 
RUN mkdir uploads
RUN mkdir downloads

CMD ["udivs.py"]
