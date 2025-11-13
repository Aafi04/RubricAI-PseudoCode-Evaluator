import os
import sys
try:
    import google.generativeai as genai
except Exception as e:
    print('Failed to import google.generativeai:', e)
    sys.exit(1)

api_key = os.environ.get('GOOGLE_API_KEY')
if not api_key:
    print('GOOGLE_API_KEY not set in environment')
    sys.exit(1)

try:
    genai.configure(api_key=api_key)
    print('Configured genai with provided API key.')
    print('--- Available Models and Supported Methods ---')
    models = genai.list_models()
    for m in models:
        # print a readable summary; attributes may vary
        name = getattr(m, 'name', repr(m))
        methods = getattr(m, 'supported_generation_methods', getattr(m, 'methods', 'N/A'))
        print(f"Model: {name}")
        print(f"  Supported methods: {methods}")
        print('')
except Exception as e:
    print('Error listing models:', e)
    sys.exit(1)
