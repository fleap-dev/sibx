# SiB CLI

This is SiB's command-line interface (CLI). It collects used lines extracted via the compiler plugin for all compiled static configurations of the program and stores it in the line-range database (LRDB). Given a patch, SiB can decide which configurations are affected by comparing the patch against the code used by the different configurations.

## Usage
See global [README.md](../README.md).

## Build Instructions
```bash
cargo build --release
```
