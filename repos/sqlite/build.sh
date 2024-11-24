#!/usr/bin/env bash

./configure CC=clang-15 --disable-tcl --disable-amalgamation 'CFLAGS=-fplugin=/usr/lib/sibplugin.so -Wno-builtin-macro-redefined -D__LINE__'

make OPTIONS=-DSQLITE_OMIT_DEPRECATED sqlite3
