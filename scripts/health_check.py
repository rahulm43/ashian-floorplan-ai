import urllib.request

try:
    resp = urllib.request.urlopen("http://localhost:8501/_stcore/health", timeout=5)
    print("Streamlit health check HTTP status:", resp.getcode())
except Exception as e:
    print("Health check error:", e)
