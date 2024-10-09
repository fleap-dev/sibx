################################### Build Rust Tool ###################################
FROM rust:1.78.0@sha256:5907e96b0293eb53bcc8f09b4883d71449808af289862950ede9a0e3cca44ff5

COPY mpc mpc/

RUN cd mpc && cargo build --release

################################### Build Clang Plugin ###################################
FROM ubuntu:23.10

COPY plugin plugin/

RUN apt-get update && apt-get -qq install make clang-15 libclang-15-dev llvm-15-dev && CXX=clang++-15 make -C plugin -j $(nproc) plugin.so

################################### Evaluation Environment ###################################
FROM ubuntu:23.10

ENV COMPILER clang-15

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin apt-get install -qq "$COMPILER" flex gcc git libelf-dev libssl-dev make python3 pipx tzdata file tclsh \
bc bison cpio lz4 lzop zstd ccache \
nano \
&& PIPX_BIN_DIR=/usr/local/bin pipx install compiledb \
&& rm -rf /var/lib/apt/lists/*

ENV NUM_COMMITS 200

ENV LINUX_VERSION v5.19
RUN git clone --branch $LINUX_VERSION --depth $(($NUM_COMMITS+3)) git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable.git /linux

ENV OPENSSL_VERSION openssl-3.0.5
RUN git clone --branch $OPENSSL_VERSION --depth $(($NUM_COMMITS+3)) https://github.com/openssl/openssl

ENV SQLITE_VERSION version-3.37.2
RUN git clone --branch $SQLITE_VERSION --depth $(($NUM_COMMITS+3)) https://github.com/sqlite/sqlite.git

ENV BOCHS_VERSION REL_2_8_FINAL
RUN git clone --branch $BOCHS_VERSION --depth $(($NUM_COMMITS+3)) https://github.com/bochs-emu/Bochs.git /bochs

RUN apt-get update \
&& DEBIAN_FRONTEND=noninteractive TZ=Europe/Berlin apt-get install -qq libx11-dev \
&& rm -rf /var/lib/apt/lists/*

ENV VARIANTS 15
COPY eval/linux_config_gen.sh .
RUN mkdir /config && ./linux_config_gen.sh $VARIANTS /linux /config

RUN ccache --set-config=max_size=1000G

# Tools
COPY --from=0 mpc/target/release/mpc /
COPY --from=1 plugin/plugin.so /
COPY eval/*.py /
COPY eval/*.sh /

VOLUME /data

CMD /eval.sh
