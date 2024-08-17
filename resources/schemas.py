def get_notfollowers_schema_followers():
    return {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "media_list_data": {
                            "type": "array",
                            "items": {"type": "object"}
                        },
                        "string_list_data": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "href": {"type": "string", "format": "uri"},
                                    "value": {"type": "string"},
                                    "timestamp": {"type": "integer"}
                                },
                                "required": ["href", "value", "timestamp"]
                            }
                        }
                    },
                    "required": ["title", "media_list_data", "string_list_data"]
                }
            }


def get_notfollowers_schema_following():
    return {
                "type": "object",
                "properties": {
                    "relationships_following": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "media_list_data": {
                                    "type": "array",
                                    "items": {"type": "object"}
                                },
                                "string_list_data": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "href": {"type": "string", "format": "uri"},
                                            "value": {"type": "string"},
                                            "timestamp": {"type": "integer"}
                                        },
                                        "required": ["href", "value", "timestamp"]
                                    }
                                }
                            },
                            "required": ["title", "media_list_data", "string_list_data"]
                        }
                    }
                },
                "required": ["relationships_following"]
            }
            