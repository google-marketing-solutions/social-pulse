#!/bin/bash

#  Copyright 2025 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

# Copyright 2025 Google LLC
#
# Helper script to update requirements.txt files with new SHA256 hashes.
# Usage: ./update_requirements_hash.sh <NEW_HASH> <REQUIREMENTS_FILE>

set -e

NEW_HASH="$1"
REQ_FILE="$2"

if [ -z "$NEW_HASH" ] || [ -z "$REQ_FILE" ]; then
    echo "Usage: $0 <NEW_HASH> <REQUIREMENTS_FILE>"
    exit 1
fi

if [ ! -f "$REQ_FILE" ]; then
    echo "Warning: Requirements file not found, skipping: $REQ_FILE"
    exit 0
fi

echo "Updating requirements file: $REQ_FILE"

# Use awk to replace the hashes for socialpulse-common
# We create a temp file then move it back
awk -v new_hash="$NEW_HASH" '
    BEGIN { in_spc_block = 0 }
    /^socialpulse-common/ {
        print
        printf "    --hash=sha256:%s\n", new_hash
        in_spc_block = 1
        next
    }
    in_spc_block == 1 && /^    --hash=/ {
        next
    }
    in_spc_block == 1 && !/^    --hash=/ {
        in_spc_block = 0
    }
    { print }
' "$REQ_FILE" > "$REQ_FILE.tmp"

mv "$REQ_FILE.tmp" "$REQ_FILE"
echo "Successfully updated $REQ_FILE."
