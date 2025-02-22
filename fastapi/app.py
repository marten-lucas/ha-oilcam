from fastapi import FastAPI, File, UploadFile, Query
from fastapi.responses import FileResponse, StreamingResponse, Response
import locale
import numpy as np
import cv2
import imutils
from datetime import datetime
import matplotlib.pyplot as plt
from enum import Enum 
import io
import httpx
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

def debug_log(message: str):
    logging.info(message)

async def fetch_and_load_image(image_url: str):
    """Fetches an image from a URL and converts it to an OpenCV format."""
    debug_log(f"Fetching image from: {image_url}")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(image_url)
            debug_log(f"Response Code: {response.status_code}")
        except Exception as e:
            debug_log(f"Error fetching image: {e}")
            return None
    
    if response.status_code != 200:
        debug_log(f"Failed to fetch image, HTTP {response.status_code}")
        return None
    
    image_data = np.frombuffer(response.content, np.uint8)
    debug_log(f"Image data received: {image_data.shape}")
    
    image_cv = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    if image_cv is None:
        debug_log("Failed to decode image")
    return image_cv


def preprocess_image(image, region):
    """Processes the image by converting it to grayscale and applying blur."""
    debug_log(f"Preprocessing image with region: {region}")
    x1, y1, x2, y2 = map(int, region.split(','))
    
    img_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img_gray, (7, 7), 0)
    img_crop = img_blur[y1:y2, x1:x2]
    img_inv = cv2.bitwise_not(img_crop)
    
    debug_log("Image preprocessing complete")
    return img_inv

def apply_threshold(image, min_val, max_val):
    """Applies a binary threshold to the image."""
    debug_log(f"Applying threshold: min={min_val}, max={max_val}")
    _, img_thresh = cv2.threshold(image, min_val, max_val, cv2.THRESH_BINARY)
    # Apply morphological opening to remove noise
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    img_thresh = cv2.morphologyEx(img_thresh, cv2.MORPH_OPEN, kernel)
    return img_thresh

def find_biggest_contour(image):
    """Finds the largest contour in the processed image."""
    contours = cv2.findContours(image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)
    if not contours:
        debug_log("No contours found")
        return None
    largest_contour = max(contours, key=cv2.contourArea)
    return cv2.boundingRect(largest_contour)

def hex_to_bgr(hex):
    hex = hex.lstrip('#')
    rgb = tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))
    return rgb[::-1]  # Reverse to get BGR


def draw_fillinglevel(image, region, h, color):
    # Parse region and extract coordinates
    region_x1, region_y1, region_x2, region_y2 = map(int, region.split(','))
    # Draw a rectangle around the detected contour
    filling_x1 = region_x1 # muss 880
    filling_y1 = region_y2 - h # muss 710 sein
    filling_x2 = region_x2 # muss 910
    filling_y2 = region_y2 # muss 1070
    debug_log(f"Draw Filling Rectange for Height of {h} at {filling_x1},{filling_y1},{filling_x2},{filling_y2}")
    cv2.rectangle(image, (filling_x1, filling_y1), (filling_x2, filling_y2), hex_to_bgr(color), 2)
    return image

def draw_region(image_cv, region, color):
    # Parse region and extract coordinates
    x1, y1, x2, y2 = map(int, region.split(','))
    # Draw a rectangle indicating the specified region
    cv2.rectangle(image_cv, (x1, y1), (x2, y2), hex_to_bgr(color), 2)

def get_filling_level(filling_height, region):
    # Parse region and extract coordinates
    _, y1, _, y2 = map(int, region.split(','))
    # Calculate filling level as a percentage of the total height
    full_height = y2-y1
    filling_level = (filling_height / full_height) * 100 if full_height else 0
    return round(filling_level, 1)  # Round to 1 decimal place


def get_filling_color(level, valueLow, valueMid, colorLow, colorMedium, colorFull):
    if level <= valueLow:
        return colorLow
    elif level <= valueMid:
        return colorMedium
    else:
        return colorFull

def calculate_capacity(filling_level, capacity):
    filled_capacity = round((filling_level / 100) * capacity)
    empty_capacity = round(capacity - filled_capacity)
    return empty_capacity, filled_capacity

async def get_oilprice(zipcode: str, quantity: int) -> tuple[float, float, str]:
    """Fetch oil prices and return unit price, total price, and currency."""
    url = f"https://www.baywa.de/waerme_strom/heizoel/heizoelpreisrechner/suche/heizoel/?zipCode={zipcode}&quantity={quantity}&deliveryFacility=&deliveryDeadline=5&deliveryTime=24&tanker=11&pipe=9&sourcePage=startPage"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": f"Failed to fetch data: {response.status_code}"}

    soup = BeautifulSoup(response.content, 'html.parser')    

    # Find the first product listing
    first_article = soup.find('div', class_='ps-result-list__item')
    if not first_article:
        return None, None, None
    
    # Set locale for German number formatting (e.g., "1.234,56 €")
    locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')  # Use German locale
    conv = locale.localeconv()

    # Extract unit price (small price)
    unit_price_div = first_article.select_one('.ps-result-list__item__price--small .ps-result-list__item__price__unit')
    unit_price_raw = unit_price_div.text.strip() if unit_price_div else None
    unit_price = locale.atof(unit_price_raw.strip(conv['currency_symbol'])) if unit_price_raw else None
    
    # Extract total price (big price)
    total_price_div = first_article.select_one('.ps-result-list__item__price--big .ps-result-list__item__price__unit')
    total_price_raw = total_price_div.text.strip() if total_price_div else None
    total_price = locale.atof(total_price_raw.strip(conv['currency_symbol'])) if total_price_raw else None
    
    return unit_price, total_price, conv['currency_symbol']

@app.get("/filling-image/")
async def filling_image(
    image_url: str = Query("http://thingino:thingino@192.168.42.4/image.jpg", description="URL des Bildes"),
    region: str = "1160,40,1200,1050",
    threshold_min: int = 120,
    threshold_max: int = 255,
    levelLow: int = 10,
    levelMedium: int = 50,
    colorLow: str = "#FF0000",  
    colorMedium: str = "#FFFF00",  
    colorFull: str = "#00FF00",  
    colorBox: str = "#0000FF"
):
    
    image_cv = await fetch_and_load_image(image_url)

    if region:
        # Zeichne eine Markierung um die Region

        # Bild für die Füllstandsanalyse vorbereiten
        image_ready = preprocess_image(image_cv, region)

        # Thresholding anwenden
        image_thresh = apply_threshold(image_ready, threshold_min, threshold_max)

        try:
            x, y, w, h = find_biggest_contour(image_thresh)
            filling_level = get_filling_level(h, region)
            
            debug_log(f"Found Biggest Contour at height {h}")
            debug_log(f"Calculated Filling Level of {filling_level} %")

            filling_color = get_filling_color(filling_level, levelLow, levelMedium, colorLow, colorMedium, colorFull)
            draw_region(image_cv, region, colorBox)
            img_result = draw_fillinglevel(image_cv, region, h, filling_color)
        except ValueError as e:
            return {"error": str(e)}

        # Ergebnisbild als WebP kodieren
        _, encoded_image = cv2.imencode(".webp", img_result, [cv2.IMWRITE_WEBP_QUALITY, 90])

        return Response(content=encoded_image.tobytes(), media_type="image/webp")

    # Falls keine Region angegeben wurde, Originalbild zurückgeben
    _, encoded_image = cv2.imencode(".webp", image_cv, [cv2.IMWRITE_WEBP_QUALITY, 90])
    return Response(content=encoded_image.tobytes(), media_type="image/webp")

@app.get("/filling-data/")
async def filling_data(
    image_url: str = Query("http://thingino:thingino@192.168.42.4/image.jpg", description="URL des Bildes"),
    region: str = "1160,40,1200,1050",
    threshold_min: int = 120,
    threshold_max: int = 255,
    capacity: int = 2400,  
    zipcode: str = "97222"
):
    # Read and save the uploaded image
    image_cv = await fetch_and_load_image(image_url)

    # Process the image to detect filling level
    if region:
        image_ready = preprocess_image(image_cv, region)
        image_thresh = apply_threshold(image_ready, threshold_min, threshold_max)

        try:
            x, y, w, h = find_biggest_contour(image_thresh)
            filling_level = get_filling_level(h, region)
            empty_capacity, filled_capacity = calculate_capacity(filling_level, capacity)
            oilprice, refillprice, currency = await get_oilprice(zipcode, empty_capacity)

            if oilprice is None or refillprice is None:
                return {"error": "Failed to fetch oil prices"}

        except ValueError as e:
            return {"error": str(e)}

        return {
            "contour_height": h,
            "filling_level": filling_level,
            "filled_capacity": filled_capacity,
            "empty_capacity": empty_capacity,
            "oilprice": oilprice,        # Now a float (e.g., 103.30)
            "refillprice": refillprice,  # Now a float (e.g., 1941.08)
            "currency": currency,        # Separate key (e.g., "€")
            "ts_lastupdate": datetime.utcnow().isoformat()
        }

    return {"error": "Region parameter is required"}
    
# Enum for process steps
class ProcessStep(str, Enum):
    preprocess = "preprocess"
    threshold = "threshold"
    contours = "contours"
    largest_contour = "largest contour"

# Debug endpoint
@app.get("/filling-debug/")
async def debug_image(
    image_url: str = Query("http://thingino:thingino@192.168.42.4/image.jpg", description="URL des Bildes"),    
    threshold_min: int = 120,
    threshold_max: int = 255,
    process_step: ProcessStep = ProcessStep.preprocess,
    region: str = "1160,40,1200,1050"  # Default region for simplicity
):
    # Read the uploaded image
    image_cv = await fetch_and_load_image(image_url)

    # Process the image based on step
    if process_step == ProcessStep.preprocess:
        img_ready = preprocess_image(image_cv, region)
        modified_image_path = "debug/debug_preprocess_image.webp"
        cv2.imwrite(modified_image_path, img_ready, [cv2.IMWRITE_WEBP_QUALITY, 90])  # Set quality between 0 and 100
        return FileResponse(modified_image_path, media_type='image/webp')

    elif process_step == ProcessStep.threshold:
        img_ready = preprocess_image(image_cv, region)
        # Generate histogram as an image
        plt.hist(img_ready.ravel(), bins=256, range=(0, 256), color="gray")
        plt.xlabel("Pixel Intensity")
        plt.ylabel("Frequency")
        plt.axvline(threshold_min, color='r', linestyle='dashed', linewidth=2, label='Threshold Min')
        plt.axvline(threshold_max, color='r', linestyle='dashed', linewidth=2, label='Threshold Max')
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        temp_file_path = "/tmp/debug_histogram_image.webp"
        with open(temp_file_path, "wb") as f:
            f.write(buf.getvalue())
        return FileResponse(temp_file_path, media_type="image/webp")

    elif process_step == ProcessStep.contours:
        img_ready = preprocess_image(image_cv, region)
        img_thresholded = apply_threshold(img_ready, threshold_min, threshold_max)
        contours = cv2.findContours(img_thresholded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        img_contours = cv2.cvtColor(img_thresholded, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(img_contours, contours, -1, (0, 255, 0), 2)
        
        modified_image_path = "debug/debug_contours_image.webp"
        cv2.imwrite(modified_image_path, img_contours, [cv2.IMWRITE_WEBP_QUALITY, 90])  # Set quality between 0 and 100
        return FileResponse(modified_image_path, media_type='image/webp')
    
    elif process_step == ProcessStep.largest_contour:
        img_ready = preprocess_image(image_cv, region)
        img_thresholded = apply_threshold(img_ready, threshold_min, threshold_max)
        x, y, w, h = find_biggest_contour(img_thresholded)
        return {"x": x, "y": y, "w":w,"h":h}


    return JSONResponse({"error": "Invalid process step"}, status_code=400)

@app.get("/oilprice")
async def oilprice_endpoint(zipcode: str, quantity: int):
    unit_price, total_price = get_oilprice(zipcode, quantity)
    return {"unit_price": unit_price, "unitprice_currency": "EUR","total_price": total_price, "totalprice_currency":"EUR"}
