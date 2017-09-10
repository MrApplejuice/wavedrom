FROM base/archlinux:latest

RUN pacman -Sy
RUN pacman -S --noconfirm phantomjs

RUN mkdir /wavedrom

WORKDIR /wavedrom
COPY ["server/serverside-renderer.js", "wavedrom.min.js", "/wavedrom/"]
RUN chmod -R 777 .

RUN useradd -m user

USER user
ENTRYPOINT phantomjs serverside-renderer.js $0 $@

