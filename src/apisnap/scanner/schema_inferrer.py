"""Schema inferrer for JSON data."""

import json
from typing import Any, Optional


class SchemaInferrer:
    """Infers JSON schema from data."""

    def infer(self, data: Any) -> dict:
        """Infer JSON schema from data.
        
        Args:
            data: JSON data (dict, list, or primitive)
            
        Returns:
            JSON schema compatible dict
        """
        if data is None:
            return {"type": "null"}
        
        if isinstance(data, dict):
            return self._infer_object(data)
        
        if isinstance(data, list):
            return self._infer_array(data)
        
        return self._infer_primitive(data)

    def _infer_object(self, obj: dict) -> dict:
        """Infer schema for a dict."""
        properties = {}
        required = []
        
        for key, value in obj.items():
            properties[key] = self.infer(value)
            
            # Check if null values exist
            if value is not None:
                required.append(key)
        
        result = {
            "type": "object",
            "properties": properties,
        }
        
        if required:
            result["required"] = required
        
        return result

    def _infer_array(self, arr: list) -> dict:
        """Infer schema for a list."""
        if not arr:
            return {
                "type": "array",
                "items": {},
            }
        
        # Infer from first few items
        item_schemas = []
        max_items = min(10, len(arr))
        
        for i in range(max_items):
            item_schemas.append(self.infer(arr[i]))
        
        # Merge schemas
        if len(item_schemas) == 1:
            merged = item_schemas[0]
        else:
            merged = self._merge_schemas(item_schemas)
        
        return {
            "type": "array",
            "items": merged,
        }

    def _infer_primitive(self, value: Any) -> dict:
        """Infer schema for a primitive value."""
        return {"type": self._infer_type(value)}

    def _infer_type(self, value: Any) -> str:
        """Get JSON type for value."""
        if value is None:
            return "null"
        
        if isinstance(value, bool):
            return "boolean"
        
        if isinstance(value, int):
            return "integer"
        
        if isinstance(value, float):
            return "number"
        
        if isinstance(value, str):
            return "string"
        
        if isinstance(value, list):
            return "array"
        
        if isinstance(value, dict):
            return "object"
        
        return "string"

    def _merge_schemas(self, schemas: list[dict]) -> dict:
        """Merge multiple schemas into one.
        
        Union of fields, types become anyOf if different.
        """
        if not schemas:
            return {}
        
        if len(schemas) == 1:
            return schemas[0]
        
        # Check if all schemas are the same type
        types = set(s.get("type", "string") for s in schemas)
        
        if len(types) == 1:
            # All same type, check structure for objects
            first = schemas[0]
            if first.get("type") == "object":
                return self._merge_object_schemas(schemas)
            elif first.get("type") == "array":
                return self._merge_array_schemas(schemas)
            else:
                return first
        
        # Different types - use anyOf
        return {
            "anyOf": schemas,
        }

    def _merge_object_schemas(self, schemas: list[dict]) -> dict:
        """Merge object schemas."""
        all_properties = {}
        all_required = set()
        
        for schema in schemas:
            properties = schema.get("properties", {})
            for key, prop in properties.items():
                if key in all_properties:
                    # Merge property schemas
                    all_properties[key] = self._merge_schemas([all_properties[key], prop)
                else:
                    all_properties[key] = prop
            
            required = schema.get("required", [])
            all_required.update(required)
        
        result = {
            "type": "object",
            "properties": all_properties,
        }
        
        if all_required:
            result["required"] = list(all_required)
        
        return result

    def _merge_array_schemas(self, schemas: list[dict]) -> dict:
        """Merge array schemas."""
        items_list = []
        
        for schema in schemas:
            items = schema.get("items", {})
            if items:
                items_list.append(items)
        
        if not items_list:
            return {}
        
        merged = self._merge_schemas(items_list)
        
        return {
            "type": "array",
            "items": merged,
        }

    def _merge_schemas(self, existing: list[dict], new: dict) -> dict:
        """Merge two schemas."""
        if not existing:
            return new
        
        all_schemas = existing + [new]
        return self._merge_schemas(all_schemas)