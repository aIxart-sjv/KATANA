#!/usr/bin/env bash

set -e

ROOT=$(cd "$(dirname "$0")/.." && pwd)

PROGRAMS="$ROOT/programs"

BUILD="$ROOT/build"

mkdir -p "$BUILD"

echo "Building KATANA eBPF..."

for file in "$PROGRAMS"/*.bpf.c
do
    name=$(basename "$file" .bpf.c)

    clang \
        -g \
        -O2 \
        -target bpf \
        -D__TARGET_ARCH_x86 \
        -I"$ROOT/headers" \
        -I"$ROOT/headers/generated" \
        -I/usr/include \
        -c "$file" \
        -o "$BUILD/$name.bpf.o"

    echo "Built $name"
done

echo
echo "Done."