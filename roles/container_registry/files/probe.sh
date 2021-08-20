#!/bin/bash

wget --server-response "$1" 2>&1 | awk '/^  HTTP/{print $2}'
