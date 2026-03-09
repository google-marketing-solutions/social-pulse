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
"""Module for common code used by multiple scoring tasks."""


LLM_REQUEST_COL_NAME = "request"

# Prefix for the final sentiment results dataset name.  The full dataset name
# will be in the format: {SENTIMENT_RESULTS_DATASET_PREFIX}_{execution_id}
SENTIMENT_RESULTS_DATASET_PREFIX = "SentimentDataset"

# Minimum threshold of relevance score for sentiment to be generated.  If a
# pience of social content has a relevance score below this threshold, it will
# NOT have sentiment generated.
MIN_RELEVANCE_THRESHOLD_FOR_SENTIMENT_TO_BE_GENERATED = 50


BASE_SENTIMENT_RESPONSE_SCHEMA: dict[str, str] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "productOrBrand": {"type": "string"},
            "summary": {"type": "string"},
            "sentimentScore": {"type": "number"},
            "relevanceScore": {"type": "number"}
        },
    },
}


JUSTIFICATION_RESPONSE_SCHEMA: dict[str, str] = {
    "positiveJustifications": {
        "type": "array",
        "items": {
            "type": "string",
        },
    },
    "negativeJustifications": {
        "type": "array",
        "items": {
            "type": "string",
        },
    },
}
