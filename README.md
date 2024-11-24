# SiB automation with Docker

This is a simple project that aims to help automate the usage of the SiB tool.
The core of this project is the `sib.sh` script.

## Building the container image

There are two container images:
- `Dockerfile.sib`: this is the base image taken from the original sib source.
- `Dockerfile.sibx`: this image uses the `Dockerfile.sib` image as a base, and adds the script and folder structure to help automate the usage of the sib tool.

Example commands to build the image:
```sh
docker buildx build -f Dockerfile.sib -t sib:latest . --load

docker buildx build -f Dockerfile.sibx -t sibx:latest . --load
```

## Using the containerized tool

Firstly, you should set these 3 volumes inside the container:
- `/data/source` (Read-Only): this is the folder inside the container that should contain the git repository being analyzed.
- `/data/build.sh` (Read-Only): this path should contain the shellscript with the instructions to build the project.
- `/data/patches` (Read-Only): this folder should have the patch files to be analyzed. Any *.patch file here will be applyed.

After setting up these volumes, you can run the container.
Result will be sent to stdout.

Example usage (sqlite):
```sh
docker run -it --rm -v /dev/shm/sqlite:/data/source:ro -v ./repos/sqlite/build.sh:/data/build.sh:ro -v ./patches/sqlite/sqlite-affect-all.patch:/data/patches/sqlite.patch:ro sibx:latest
```

Another example (openssl):
```sh
docker run -it --rm -v /dev/shm/openssl:/data/source:ro -v ./repos/openssl/build.sh:/data/build.sh:ro -v ./patches/openssl/openssl-not-bother.patch:/data/patches/openssl.patch:ro sibx:latest bash
```

