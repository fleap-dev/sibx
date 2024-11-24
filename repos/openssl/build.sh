#!/usr/bin/env bash

./Configure CC=clang-15 'CFLAGS=-fplugin=/usr/lib/sibplugin.so -Wno-builtin-macro-redefined -D__LINE__'

make -j12
