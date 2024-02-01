#!/bin/sh

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup-init.sh
chmod a+x rustup-init.sh
./rustup-init.sh -y --profile minimal --default-toolchain nightly-2023-08-28

export PATH="${PATH}":"${HOME}"/.cargo/bin
cargo install cargo-xbuild
rustup component add rust-src
