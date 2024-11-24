# AST-Frontend (Experimental)

This is a prototypical, alternative implementation of SiB's compiler plugin. Instead of using the C preprocessor, it utilizes the abstract syntax tree (AST) to determine which lines of code are used. Currently, only programs written in the C programming language are supported.

## Usage
Add `-fplugin=path/to/plugin.so` to `CFLAGS`.

## Build Instructions
```bash
make plugin.so
```
