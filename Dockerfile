################################### Build Rust Tool ###################################
FROM rust:1.78.0@sha256:5907e96b0293eb53bcc8f09b4883d71449808af289862950ede9a0e3cca44ff5

COPY sibsrc/mpc mpc/

RUN cd mpc && cargo build

################################### Build Clang Plugin ###################################
FROM ubuntu:23.10

COPY sibsrc/plugin plugin/

RUN apt-get update && apt-get -qq install make clang-15 libclang-15-dev llvm-15-dev && CXX=clang++-15 make -C plugin -j $(nproc) plugin.so

################################### Evaluation Environment ###################################
FROM ubuntu:23.10

ENV COMPILER clang-15

RUN apt-get update && apt-get -qq install make clang-15 libclang-15-dev llvm-15-dev bear

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin apt-get install -qq "$COMPILER" flex gcc git libelf-dev libssl-dev make python3 pipx tzdata file tclsh \
bc bison cpio lz4 lzop zstd ccache \
nano \
&& PIPX_BIN_DIR=/usr/local/bin pipx install compiledb

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin apt-get install -qq libx11-dev \
&& rm -rf /var/lib/apt/lists/*

VOLUME /data
WORKDIR /data

COPY --from=0 mpc/target/debug/mpc .
COPY --from=1 plugin/plugin.so .
COPY ./repos ./repos

ENV CXX=clang++-15
ENV CC=clang-15
ENV CFLAGS=-fplugin=/data/plugin.so
ENV CXXFLAGS=-fplugin=/data/plugin.so

RUN mkdir /data/storage
RUN rm -rf /data/repos/openssl/.git
RUN git config --global user.email "test@example.com"
RUN git config --global user.name "test@example.com"

RUN cd repos/openssl && git init
RUN cd repos/openssl && git add .
RUN cd repos/openssl && git commit -m "first"
RUN cd repos/openssl && ./Configure
RUN cd repos/openssl && make -j14
RUN cd repos/openssl && bear -- make

COPY openssl-example.patch .

CMD bash
