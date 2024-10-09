#!/usr/bin/env bash

COUNT=$1
REPO=$2
DEST=$3

CC="/usr/bin/$COMPILER"

echo "Building Linux configs"

make -C $REPO tinyconfig CC="$CC" KCONFIG_CONFIG=$(realpath $DEST)/tinyconfig &> /dev/null
$REPO/scripts/config --file $(realpath $DEST)/tinyconfig --enable CONFIG_RANDSTRUCT_NONE --disable CONFIG_RANDSTRUCT_FULL --disable CONFIG_RANDSTRUCT --disable CONFIG_IKHEADERS

make -C $REPO defconfig CC="$CC" KCONFIG_CONFIG=$(realpath $DEST)/defconfig > /dev/null
$REPO/scripts/config --file $(realpath $DEST)/defconfig --enable CONFIG_RANDSTRUCT_NONE --disable CONFIG_RANDSTRUCT_FULL --disable CONFIG_RANDSTRUCT --disable CONFIG_IKHEADERS

for ((i = 2 ; i < $COUNT ; i++)); do
    make -C $REPO randconfig CC="$CC" KCONFIG_SEED=$i KCONFIG_PROBABILITY=10 KCONFIG_CONFIG=$(realpath $DEST)/randconfig_$i > /dev/null
    $REPO/scripts/config --file $(realpath $DEST)/randconfig_$i --enable CONFIG_RANDSTRUCT_NONE --disable CONFIG_RANDSTRUCT_FULL --disable CONFIG_RANDSTRUCT --disable CONFIG_IKCONFIG --disable CONFIG_IKCONFIG_PROC --disable CONFIG_IKHEADERS --disable CONFIG_DEBUG_INFO --disable CONFIG_DEBUG_KERNEL --disable CONFIG_DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT
done
