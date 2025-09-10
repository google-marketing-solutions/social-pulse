# Copyright 2025 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Dockerfile for building an analysis service server instance.
#
# This docker file should be built using the higher level /services directory
# as the build context.  I.e.,
#
#   cd social_pulse/services
#   docker build -t analysis_service:latest -f analysis_service/Dockerfile.runner .

FROM python:3.12-slim

WORKDIR /app

COPY . .

ARG YOYO_DB_ACCESS_URL

WORKDIR /app/services/shared_lib
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m build

WORKDIR /app/services/analysis_service
RUN pip install --no-cache-dir -r requirements.txt

RUN yoyo apply --batch  --no-cache --database=${YOYO_DB_ACCESS_URL}

# EXPOSE 8000
# CMD ["uvicorn", "src.runner_entry:app"]