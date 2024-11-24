# SiB automation

Example usage:
```
docker run -it --rm -v /dev/shm/sqlite:/data/source:ro -v ./repos/sqlite/build.sh:/data/build.sh:ro -v ./patches/sqlite/sqlite-affect-all.patch:/data/patches/sqlite.patch:ro sibx:latest
```

