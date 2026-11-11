class AIError(Exception):
    pass

class ConfigError(Exception):
    pass

class AIConnectionError(AIError):
    pass

class MalformedResponseError(AIError):
    pass

class SchemaValidationError(AIError):
    pass

