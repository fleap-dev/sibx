# Clang Compiler Plugin

This is SiB's compiler plugin. It utilizes the C preprocessor to determine which lines of code are used. It supports programs written in C/C++.

## Usage
Add `-fplugin=path/to/plugin.so` to `CFLAGS`/`CXXFLAGS`.

## Build Instructions
```bash
make plugin.so
```
