# Should I Bother?

This is the source code for the tools described in the paper _Should I Bother? Fast Patch Filtering for Statically-Configured Software Variants_ published in the proceedings of _SPLC '24: 28th ACM International Systems and Software Product Line Conference_.

**TL;DR**: The Clang plugin records all lines of code included by the C preprocessor during the compilation of a program. The SiB tool then collects this information for all compiled static configurations of the program. Given a patch, SiB can decide which configurations are affected by comparing the patch against the code used by the different configurations.

## Usage
1. Add `-fplugin=path/to/plugin.so` to `CFLAGS`/`CXXFLAGS`.
2. After compilation, run:
    ```bash
    mpc analyze --filter-asm --commit $(git rev-parse --short HEAD) --variant $VARNAME --storage path/to/storage --compile-commands --dump-only path/to/your/project`
    ```
3. After applying a patch, run:
    ```bash
    mpc analyze --filter-asm --commit $(git rev-parse --short HEAD) --storage path/to/storage --check-storage path/to/your/project
    ```

## Repository Structure
This repository consists of the following four projects. More detailed documentation is located in the corresponding directories. For a conceptual overview, please consult the paper.

### Clang Plugin
The Clang compiler plugin is located in `plugin/`.

### SiB CLI
The CLI referred to in the paper as _SiB_ is located in `mpc/`.

### AST-Frontend (Experimental)
The prototype for AST-Level line range information is located in `ast-frontend/`.

### Evaluation Scripts
All evaluation scripts including a `Dockerfile` for a reproducible environment are located in `eval/`.
