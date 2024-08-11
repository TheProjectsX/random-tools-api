from flask import Flask, request
import requests
import qrcode
from pyzbar.pyzbar import decode
import io
import base64
from PIL import Image
import json
import geocoder


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

@app.route("/qrcode/decode", methods=["POST"])
def decQrCode():
    if "image" not in request.files:
        return {"success": False, "message": "No Image Sent"}
    
    file = request.files["image"]
    print(request.files, file.filename)
    
    if file.filename == "" or not file:
        return {"success": False, "message": "No Image Sent"}
    
    decodedData = []
    
    if file:
        try:
            img = Image.open(file.stream)
            img = img.convert("RGB")

            decodedQR = decode(img)
            for item in decodedQR:
                decodedData.append(item.data.decode('ascii'))
        except Exception as e:
            print(str(e))
    
    if (len(decodedData) == 0):
        return {"success": False, "message": "No QR Code Found!"}
    
    return {"success": True, "data": decodedData}

# JSON Formatter
@app.route("/json-formatter", methods=["POST"])
def jsonFormatter():
    jsonStrData = request.json.get("json")
    indent = request.json.get("indent", 4)
    separators = request.json.get("separators", {})
    sortKeys = request.json.get("sortKeys", False)

    try:
        indent = int(indent)
    except Exception as e:
        indent = 4

    if (jsonStrData is None):
        return {"success": False, "message": "No JSON Data provided"}
    
    jsonData = None
    try:
        jsonData = json.loads(jsonStrData)
    except Exception as e:
        print(str(e))
    
    if (jsonData is None):
        return {"success": False, "message": "Invalid JSON Data provided"}

    try:
        formattedData = json.dumps(jsonData, indent=indent, separators=(separators.get("object", ","), separators.get("value", ": ")), sort_keys=sortKeys)
    except Exception as e:
        return {"success": False, "message": "Failed to Format JSON Data"}
    
    return {"success": True, "json": formattedData}

# IP Lookup
@app.route("/ip-lookup", methods=["POST"])
def ipLookup():
    ip = request.json.get("ip")
    if (ip is None):
        return {"success": False, "message": "No IP Provided"}

    ipDetails = None
    try:
        ipDetails = geocoder.ip(ip)
    except Exception as e:
        print(str(e))
    
    if (ipDetails is None):
        return {"success": False, "message": "Failed to get IP Info"}
    elif (not ipDetails.ok):
        return {"success": False, "message": "Failed to get IP Info"}

    formattedData = ipDetails.geojson.get("features", {})[0].get("properties", {}).get("raw", {})
    del formattedData["readme"]
    formattedData["lat"] = ipDetails.geojson.get("features", {})[0].get("properties", {}).get("lat")
    formattedData["long"] = ipDetails.geojson.get("features", {})[0].get("properties", {}).get("lng")

    return {"success": True, "data": formattedData}




if (__name__ == "__main__"):
    app.run(debug=True)