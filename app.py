from flask import Flask, request
import requests
import qrcode
import io
import base64
from PIL import Image

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello"


# URL Shortener
@app.route("/url/shorten", methods=["POST"])
def shortenUrl():
    longUrl = request.json.get("longUrl")
    domain = request.json.get("domain", "is.gd")
    custom = request.json.get("custom", "")

    if (longUrl is None):
        return {"success": False, "message": "No URL provided!"}
    
    response = None
    shortened = None
    try:
        if (domain == "v.gd"):
            response = requests.get(f"https://v.gd/create.php?format=json&url={longUrl}&shorturl={custom}").json()
            shortened = response.get("shorturl")
        else:
            response = requests.get(f"https://is.gd/create.php?format=json&url={longUrl}&shorturl={custom}").json()
            print(response)
            shortened = response.get("shorturl")
    except Exception as e:
        print(str(e))
        return {"success": False, "message": "Failed to Shorten URL"}

    if (shortened is None):
        return {"success": False, "message": response.get("errormessage")}

    return {"success": True, "shortUrl": shortened}

@app.route("/url/lookup", methods=["POST"])
def lookupUrl():
    shortUrl = request.json.get("shortUrl")

    response = None
    original = None

    try:
        if ("v.gd" in shortUrl):
            response = requests.get(f"https://v.gd/forward.php?format=json&shorturl={shortUrl}").json()
            original = response.get("url")
        else:
            response = requests.get(f"https://is.gd/forward.php?format=json&shorturl={shortUrl}").json()
            original = response.get("url")
    except Exception as e:
        print(str(e))
        return {"success": False, "message": "Failed to get Original URL"}
    
    if (original is None):
        return {"success": False, "message": response.get("errormessage")}

    return {"success": True, "shortUrl": original}


# QRCode Generator
@app.route("/qrcode/gen", methods=["POST"])
def genQrCode():
    text = request.json.get("text")
    if (text is None):
        return {"success": False, "message": "No data provided"}

    try:
        
        img = qrcode.make(text)

        img_io = io.BytesIO()
        img.save(img_io)
        img_io.seek(0)

        base64_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
        img_data_url = f"data:image/png;base64,{base64_data}"

        return {"success": True, "img": img_data_url}
    except Exception as e:
        print(str(e))
        return {"success": False, "message": "Some error Occurred"}



if (__name__ == "__main__"):
    app.run(debug=True)