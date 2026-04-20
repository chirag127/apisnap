"""Tests for schema inferrer."""

import pytest

from apisnap.scanner.schema_inferrer import SchemaInferrer


class TestSchemaInferrer:
    """Tests for SchemaInferrer."""

    def test_infer_simple_object(self):
        """Test inferring simple object."""
        inferrer = SchemaInferrer()

        data = {"name": "John", "age": 30}
        schema = inferrer.infer(data)

        assert schema["type"] == "object"
        assert "name" in schema["properties"]
        assert "age" in schema["properties"]

    def test_infer_nested_object(self):
        """Test inferring nested object."""
        inferrer = SchemaInferrer()

        data = {"user": {"id": 1, "email": "a@b.com"}}
        schema = inferrer.infer(data)

        assert schema["type"] == "object"
        assert schema["properties"]["user"]["type"] == "object"

    def test_infer_array_of_objects(self):
        """Test inferring array of objects."""
        inferrer = SchemaInferrer()

        data = [{"id": 1}, {"id": 2}, {"id": 3}]
        schema = inferrer.infer(data)

        assert schema["type"] == "array"
        assert schema["items"]["type"] == "object"

    def test_infer_primitive_types(self):
        """Test inferring primitive types."""
        inferrer = SchemaInferrer()

        assert inferrer._infer_type("hello") == "string"
        assert inferrer._infer_type(123) == "integer"
        assert inferrer._infer_type(1.5) == "number"
        assert inferrer._infer_type(True) == "boolean"
        assert inferrer._infer_type(None) == "null"

    def test_infer_empty_object(self):
        """Test inferring empty object."""
        inferrer = SchemaInferrer()

        schema = inferrer.infer({})

        assert schema["type"] == "object"
        assert schema["properties"] == {}

    def test_infer_empty_array(self):
        """Test inferring empty array."""
        inferrer = SchemaInferrer()

        schema = inferrer.infer([])

        assert schema["type"] == "array"
        assert "items" in schema

    def test_infer_mixed_types(self):
        """Test inferring mixed type array."""
        inferrer = SchemaInferrer()

        data = [1, "hello", True]
        schema = inferrer.infer(data)

        assert schema["type"] == "array"
        assert "anyOf" in schema["items"]

    def test_merge_schemas(self):
        """Test merging schemas."""
        inferrer = SchemaInferrer()

        schemas = [
            {"type": "object", "properties": {"id": {"type": "integer"}}},
            {"type": "object", "properties": {"name": {"type": "string"}}},
        ]

        merged = inferrer._merge_schemas(schemas)

        assert merged["type"] == "object"
        assert "id" in merged["properties"]
        assert "name" in merged["properties"]
