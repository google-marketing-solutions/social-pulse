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

import unittest
from prompts.configs import core


class SchemaResponseSchemaBuilderTest(unittest.TestCase):

  def test_base_schema_contains_summary_and_sentiments(self):
    builder = core.SentimentResponseSchemaBuilder()
    schema = builder.build()

    self.assertIn("summary", schema["properties"])
    self.assertIn("sentiments", schema["properties"])
    self.assertEqual(schema["properties"]["summary"]["type"], "string")
    self.assertEqual(schema["properties"]["sentiments"]["type"], "array")

  def test_default_sentiment_item_properties(self):
    builder = core.SentimentResponseSchemaBuilder()
    schema = builder.build()
    sentiment_item_properties = (
        schema["properties"]["sentiments"]["items"]["properties"])

    self.assertIn("productOrBrand", sentiment_item_properties)
    self.assertEqual(
        sentiment_item_properties["productOrBrand"]["type"], "string"
    )

    self.assertIn("sentimentScore", sentiment_item_properties)
    self.assertEqual(
        sentiment_item_properties["sentimentScore"]["type"],
        "number"
    )

    self.assertIn("relevanceScore", sentiment_item_properties)
    self.assertEqual(
        sentiment_item_properties["relevanceScore"]["type"], "number"
    )

  def test_add_property_adds_new_property_to_sentiment_item(self):
    builder = core.SentimentResponseSchemaBuilder()
    builder.add_property({"newProp": {"type": "boolean"}})
    schema = builder.build()
    sentiment_item_properties = (
        schema["properties"]["sentiments"]["items"]["properties"])

    self.assertIn("newProp", sentiment_item_properties)
    self.assertEqual(sentiment_item_properties["newProp"]["type"], "boolean")

  def test_add_property_overwrites_existing_property(self):
    builder = core.SentimentResponseSchemaBuilder()
    builder.add_property({"sentimentScore": {"type": "string"}})
    schema = builder.build()
    sentiment_item_properties = (
        schema["properties"]["sentiments"]["items"]["properties"])

    self.assertIn("sentimentScore", sentiment_item_properties)
    self.assertEqual(
        sentiment_item_properties["sentimentScore"]["type"], "string"
    )
