import unittest
from unittest import mock

import pandas as pd
import sentiment_task_mixins as test_mixins
from tasks import process_sov_brands


class ProcessSovBrandsTaskTest(
    unittest.TestCase, test_mixins.SetupMockSentimentTaskDepependenciesMixin
):

  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

    self.task = process_sov_brands.ProcessSovBrandsTask(
        execution_id="test_exec_id",
        my_required_task=self.mock_required_task,
    )

    # Mock the inputs dict for requires/input resolution
    self.mock_consolidated_brands_target = mock.Mock()
    self.task.input = mock.Mock(
        return_value={
            "sentiment_data": self.mock_input_target,
            "consolidated_brands": self.mock_consolidated_brands_target,
        }
    )

  def test_run_validates_input_data(self):
    """Validates that input data has required columns.

    Given an input DataFrame missing the 'sentiments' column
    When run is called
    Then a ValueError is raised
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        {"other_col": []}
    )
    self.mock_consolidated_brands_target.load_sentiment_data.return_value = (
        pd.DataFrame([{"consolidated_brands_json": "{}"}])
    )

    with self.assertRaisesRegex(ValueError, "missing 'sentiments' column"):
      self.task.run()

  def test_run_successful_mapping(self):
    """Successfully maps brands using consolidated lookup.

    Given input sentiment data and a consolidated brands lookup
    When run is called
    Then the productOrBrand fields are updated with consolidated values
    """
    input_sentiment_df = pd.DataFrame(
        [
            {
                "sentiments": [
                    {"productOrBrand": "ChatGPT"},
                    {"productOrBrand": "Sora"},
                ]
            }
        ]
    )
    self.mock_input_target.load_sentiment_data.return_value = input_sentiment_df

    consolidated_json = '{"ChatGPT": "OpenAI", "Sora": "OpenAI"}'
    consolidated_df = pd.DataFrame(
        [{"consolidated_brands_json": consolidated_json}]
    )
    self.mock_consolidated_brands_target.load_sentiment_data.return_value = (
        consolidated_df
    )

    mock_output_target = mock.Mock()
    self.task.output = mock.Mock(return_value=mock_output_target)

    self.task.run()

    mock_output_target.write_sentiment_data.assert_called_once()
    args, _ = mock_output_target.write_sentiment_data.call_args
    output_df = args[0]

    # Verify mapping
    sentiments = output_df.iloc[0]["sentiments"]
    self.assertEqual(sentiments[0]["productOrBrand"], "OpenAI")
    self.assertEqual(sentiments[1]["productOrBrand"], "OpenAI")

  def test_run_missing_mapping_keeps_original(self):
    """Keeps original brand if not found in lookup.

    Given input sentiment data and a lookup without the brand
    When run is called
    Then the productOrBrand field remains unchanged
    """
    input_sentiment_df = pd.DataFrame(
        [{"sentiments": [{"productOrBrand": "UnknownBrand"}]}]
    )
    self.mock_input_target.load_sentiment_data.return_value = input_sentiment_df

    consolidated_json = '{"ChatGPT": "OpenAI"}'
    consolidated_df = pd.DataFrame(
        [{"consolidated_brands_json": consolidated_json}]
    )
    self.mock_consolidated_brands_target.load_sentiment_data.return_value = (
        consolidated_df
    )

    mock_output_target = mock.Mock()
    self.task.output = mock.Mock(return_value=mock_output_target)

    self.task.run()

    mock_output_target.write_sentiment_data.assert_called_once()
    args, _ = mock_output_target.write_sentiment_data.call_args
    output_df = args[0]

    sentiments = output_df.iloc[0]["sentiments"]
    self.assertEqual(sentiments[0]["productOrBrand"], "UnknownBrand")
