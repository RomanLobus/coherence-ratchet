import importlib
import json
import sys

module = importlib.import_module(sys.argv[1])
print(json.dumps(module.price_response("order-42", 5, 0), sort_keys=True))

