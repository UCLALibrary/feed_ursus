FROM python:3.11

RUN pip install pipx
RUN pipx ensurepath
COPY . /feed_ursus
RUN pipx install /feed_ursus