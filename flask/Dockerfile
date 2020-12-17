FROM python:3
WORKDIR /usr/src/jopents
COPY . .
RUN apt -y update
RUN apt -y install libpq-dev cron nano
RUN pip3 install flask jinja2 psycopg2-binary requests_html
EXPOSE 3100
COPY cron /etc/cron.d/jopents
RUN chmod 0644 /etc/cron.d/jopents
RUN touch /var/log/cron.log
RUN crontab /etc/cron.d/jopents
RUN cron
CMD ["python3", "./app.py"]