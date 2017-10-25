FROM base/archlinux:latest

RUN pacman -Sy
RUN pacman -S --noconfirm phantomjs ttf-freefont ttf-dejavu

# Requirements for the server
RUN pacman -S --noconfirm python python-pip
RUN pip install jinja2 falcon pillow gunicorn

COPY ["*.js", "/wavedrom/"]
COPY ["server", "/wavedrom/server"]
COPY ["python", "/wavedrom/python"]
COPY ["skins", "/wavedrom/skins"]
RUN chmod -R 777 /wavedrom

RUN useradd -m user

EXPOSE 8000

ENV WORKER_COUNT=4

USER user
WORKDIR /wavedrom/python/render_server
ENTRYPOINT gunicorn main:fapi -w${WORKER_COUNT} -b 0.0.0.0:8000

