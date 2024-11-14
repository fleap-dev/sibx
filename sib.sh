#!/usr/bin/env bash

PATCH_DIR="./patches"
SOURCE_DIR="./source"

# Step 1: build the project on the current state, before patch.
# This is a script that builds the project. $CFLAGS and $CXXFLAGS are configured to use the clang plugin.
echo "[STEP 1] Building project..."
(cd $SOURCE_DIR && ./build.sh)

# Step 2: use mpc to create the current LRDB
echo "[STEP 2] Analyzing project..."
mkdir ./lrdb
mpc analyze --storage ./lrdb --commit=HEAD --variant=current --dump-only ${SOURCE_DIR}

# Step 3: apply patches
echo "[STEP 3] Applying patches..."
for patch in "$PATCH_DIR"/*.patch; do
    # Check if there are no patch files
    if [ ! -f "$patch" ]; then
        echo "No patches found in $PATCH_DIR."
        exit 1
    fi

    # Apply the patch
    echo "Applying patch $patch..."
    patch -d "$SOURCE_DIR" -p1 < "$patch"

    # Check if the patch was successful
    if [ $? -ne 0 ]; then
        echo "Failed to apply patch $patch."
        exit 1
    fi
done

# Step 4: use mpc to analyze the current source, after patches
echo "[STEP 4] Analyzing results..."
mpc analyze --storage ./lrdb --commit HEAD --check-storage ${SOURCE_DIR}

