import requests

def check_xss(url):
    payload = "<script>alert('XSS')</script>"
    params = {"search": payload}
    response = requests.get(url, params=params)
    
    if payload in response.text:
        print(f"Vulnerable to XSS: {url}")
    else:
        print("No XSS vulnerability detected")

check_xss("https://pornxnow.me/?s=")