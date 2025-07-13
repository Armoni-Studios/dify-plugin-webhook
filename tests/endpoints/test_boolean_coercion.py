import unittest
from unittest.mock import Mock, patch
from werkzeug import Request, Response
from dify_plugin.core.runtime import Session
from endpoints.invoke_endpoint import WebhookEndpoint


class TestBooleanCoercion(unittest.TestCase):
    def setUp(self):
        # Create a mock session
        self.mock_session = Mock(spec=Session)
        self.mock_session.app = Mock()
        self.mock_session.app.workflow = Mock()
        self.mock_session.app.chat = Mock()

        # Create the endpoint with the mock session
        self.endpoint = WebhookEndpoint(session=self.mock_session)

        # Create a mock request
        self.mock_request = Mock(spec=Request)
        self.mock_request.get_json = Mock(return_value={"inputs": {"test": "value"}})
        self.mock_request.headers = {}
        self.mock_request.default_middleware_json = None
        self.mock_request.path = "/single-workflow"

        # Default workflow response
        self.workflow_response = {
            "data": {"outputs": {"result": "Test workflow output"}}
        }
        self.mock_session.app.workflow.invoke.return_value = self.workflow_response

    def test_coerce_boolean_settings_string_true(self):
        """Test that string 'true' is converted to boolean True"""
        settings = {
            "explicit_inputs": "true",
            "raw_data_output": "true", 
            "json_string_input": "true",
            "other_setting": "some_value"
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertTrue(coerced["explicit_inputs"])
        self.assertTrue(coerced["raw_data_output"])
        self.assertTrue(coerced["json_string_input"])
        self.assertEqual(coerced["other_setting"], "some_value")

    def test_coerce_boolean_settings_string_false(self):
        """Test that string 'false' is converted to boolean False"""
        settings = {
            "explicit_inputs": "false",
            "raw_data_output": "false",
            "json_string_input": "false"
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertFalse(coerced["explicit_inputs"])
        self.assertFalse(coerced["raw_data_output"])
        self.assertFalse(coerced["json_string_input"])

    def test_coerce_boolean_settings_mixed_case(self):
        """Test that mixed case strings are handled correctly"""
        settings = {
            "explicit_inputs": "True",
            "raw_data_output": "FALSE",
            "json_string_input": "TrUe"
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertTrue(coerced["explicit_inputs"])
        self.assertFalse(coerced["raw_data_output"])
        self.assertTrue(coerced["json_string_input"])

    def test_coerce_boolean_settings_actual_booleans(self):
        """Test that actual boolean values are left unchanged"""
        settings = {
            "explicit_inputs": True,
            "raw_data_output": False,
            "json_string_input": True
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertTrue(coerced["explicit_inputs"])
        self.assertFalse(coerced["raw_data_output"])
        self.assertTrue(coerced["json_string_input"])

    def test_coerce_boolean_settings_mixed_types(self):
        """Test that mixed string and boolean values work correctly"""
        settings = {
            "explicit_inputs": "true",
            "raw_data_output": False,
            "json_string_input": "false"
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertTrue(coerced["explicit_inputs"])
        self.assertFalse(coerced["raw_data_output"])
        self.assertFalse(coerced["json_string_input"])

    def test_coerce_boolean_settings_missing_fields(self):
        """Test that missing boolean fields don't cause errors"""
        settings = {
            "other_setting": "value"
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertEqual(coerced["other_setting"], "value")
        self.assertNotIn("explicit_inputs", coerced)
        self.assertNotIn("raw_data_output", coerced)
        self.assertNotIn("json_string_input", coerced)

    def test_coerce_boolean_settings_invalid_string_values(self):
        """Test that invalid string values are converted to False"""
        settings = {
            "explicit_inputs": "invalid",
            "raw_data_output": "yes",
            "json_string_input": "1"
        }
        
        coerced = self.endpoint._coerce_boolean_settings(settings)
        
        self.assertFalse(coerced["explicit_inputs"])
        self.assertFalse(coerced["raw_data_output"])
        self.assertFalse(coerced["json_string_input"])

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_invoke_uses_coerced_settings_explicit_inputs(self, mock_validate_api_key, mock_apply_middleware):
        """Test that _invoke method uses coerced explicit_inputs setting"""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        settings = {
            "explicit_inputs": "false",
            "static_app_id": "test-app-id"
        }
        
        self.mock_request.get_json.return_value = {
            "param1": "value1",
            "param2": "value2"
        }

        response = self.endpoint._invoke(self.mock_request, {}, settings)

        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={"param1": "value1", "param2": "value2"},
            response_mode="blocking"
        )

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_invoke_uses_coerced_settings_raw_data_output(self, mock_validate_api_key, mock_apply_middleware):
        """Test that _invoke method uses coerced raw_data_output setting"""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        settings = {
            "raw_data_output": "true",
            "static_app_id": "test-app-id"
        }

        response = self.endpoint._invoke(self.mock_request, {}, settings)

        self.assertEqual(response.status_code, 200)
        import json
        response_data = json.loads(response.data)
        self.assertEqual(response_data, self.workflow_response["data"]["outputs"])


if __name__ == '__main__':
    unittest.main()
