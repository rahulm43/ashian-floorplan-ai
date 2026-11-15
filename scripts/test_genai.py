try:
    from google import genai
    print("Google GenAI SDK is available!")
except ImportError:
    try:
        import google.generativeai as genai
        print("Legacy google-generativeai is available!")
    except ImportError:
        print("No google genai installed")
