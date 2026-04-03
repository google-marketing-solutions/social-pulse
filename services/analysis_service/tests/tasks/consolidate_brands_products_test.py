import unittest
from unittest import mock

import pandas as pd
import sentiment_task_mixins as test_mixins
from socialpulse_common import service
from tasks import generate_products_brands_lookup
from tasks.ports import apis


class ConsolidateBrandsProductsTaskTest(
    unittest.TestCase, test_mixins.SetupMockSentimentTaskDepependenciesMixin
):

  def setUp(self):
    super().setUp()
    self.setup_all_mock_dependencies()

    # Mock the LlmApiClient registered in the service registry
    self.mock_analyzer = mock.Mock(spec=apis.LlmApiClient)
    service.registry.register(apis.LlmApiClient, self.mock_analyzer)

    self.task = (
        generate_products_brands_lookup.GenerateConsolidatedBrandsTask(
            execution_id="test_exec_id",
            my_required_task=self.mock_required_task,
        )
    )

  def test_extract_brands_success(self):
    """Successfully extracts unique brands.

    Given valid input DataFrame with sentiments
    When _extract_brands is called
    Then it returns a unique list of brands
    """
    input_df = pd.DataFrame(
        [
            {
                "sentiments": [
                    {"productOrBrand": "BrandA", "sentimentScore": 0.9},
                    {"productOrBrand": "BrandB", "sentimentScore": 0.8},
                ]
            },
            {
                "sentiments": [
                    {"productOrBrand": "BrandA", "sentimentScore": 0.9},
                    {"productOrBrand": "BrandC", "sentimentScore": 0.7},
                ]
            },
            {"sentiments": []},
            {"sentiments": None},
        ]
    )

    brands = self.task._extract_brands(input_df)
    self.assertEqual(set(brands), {"BrandA", "BrandB", "BrandC"})

  def test_extract_brands_empty_input(self):
    """Handles empty input gracefully.

    Given an empty DataFrame
    When _extract_brands is called
    Then it returns an empty list
    """
    brands = self.task._extract_brands(pd.DataFrame())
    self.assertEqual(brands, [])

  def test_extract_brands_missing_column(self):
    """Handles DataFrame missing sentiments column.

    Given a DataFrame missing 'sentiments' column
    When _extract_brands is called
    Then it returns an empty list
    """
    brands = self.task._extract_brands(pd.DataFrame({"other_col": []}))
    self.assertEqual(brands, [])

  def test_extract_brands_whitespace_handling(self):
    """Handles whitespace in brands.

    Given a DataFrame with whitespaces in brands
    When _extract_brands is called
    Then it returns a unique list of stripped brands
    """
    input_df = pd.DataFrame(
        [
            {
                "sentiments": [
                    {"productOrBrand": " BrandA ", "sentimentScore": 0.9},
                    {"productOrBrand": "BrandB\n", "sentimentScore": 0.8},
                ]
            }
        ]
    )
    brands = self.task._extract_brands(input_df)
    self.assertEqual(set(brands), {"BrandA", "BrandB"})

  def test_run_validates_input_data(self):
    """Validates that input data has required columns.

    Given an input DataFrame missing the 'sentiments' column
    When run is called
    Then a ValueError is raised
    """
    self.mock_input_target.load_sentiment_data.return_value = pd.DataFrame(
        {"other_col": []}
    )
    with mock.patch.object(
        self.task, "input", return_value=self.mock_input_target
    ):
      with self.assertRaisesRegex(ValueError, "missing 'sentiments' column"):
        self.task.run()

  def test_run_generates_empty_consolidated_brands(self):
    """Outputs empty consolidated brands if no brands are found.

    Given input DataFrame with no sentiments
    When run is called
    Then it gracefully returns an empty JSON object
    """
    input_df = pd.DataFrame([{"sentiments": []}])
    self.mock_input_target.load_sentiment_data.return_value = input_df

    mock_output_target = mock.Mock()
    with (
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_target
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      self.mock_analyzer.analyze_content.assert_not_called()
      mock_output_target.write_sentiment_data.assert_called_once()

      args, _ = mock_output_target.write_sentiment_data.call_args
      output_df = args[0]
      self.assertEqual(len(output_df), 1)
      self.assertEqual(output_df.iloc[0]["consolidated_brands_json"], "{}")

  def test_run_successful_execution(self):
    """Successfully executes the consolidation flow.

    Given valid input DataFrame with sentiments
    When run is called
    Then the LLM is prompted for consolidation and the output is saved
    """
    input_df = pd.DataFrame(
        [
            {
                "sentiments": [
                    {"productOrBrand": "OpenAI"},
                    {"productOrBrand": "ChatGPT"},
                ]
            }
        ]
    )
    self.mock_input_target.load_sentiment_data.return_value = input_df

    mock_response = '{"ChatGPT": "OpenAI", "OpenAI": "OpenAI"}'
    self.mock_analyzer.analyze_content.return_value = mock_response

    mock_output_target = mock.Mock()
    with (
        mock.patch.object(
            self.task, "input", return_value=self.mock_input_target
        ),
        mock.patch.object(self.task, "output", return_value=mock_output_target),
    ):
      self.task.run()

      self.mock_analyzer.analyze_content.assert_called_once()
      mock_output_target.write_sentiment_data.assert_called_once()

      args, _ = mock_output_target.write_sentiment_data.call_args
      output_df = args[0]
      self.assertEqual(len(output_df), 1)
      self.assertEqual(
          output_df.iloc[0]["consolidated_brands_json"], mock_response
      )
