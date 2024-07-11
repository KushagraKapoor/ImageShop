from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from .forms import ImageUploadForm
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import os
import webcolors
import re
from django.template.defaultfilters import register
from .custom_filters import rating_percentage
# __init__.py

from django import template

register = template.Library()

# Import custom filters
from .custom_filters import *


from .scrape import scrape_amazon  

# COCO labels
COCO_LABELS = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
    'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
    'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'TV', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
    'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
    'hair drier', 'toothbrush'
]

def closest_color(requested_color):
    min_colors = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colors[(rd + gd + bd)] = name
    return min_colors[min(min_colors.keys())]

def get_dominant_color(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pixels = image.reshape((-1, 3))
    pixels = np.float32(pixels)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    k = 1
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    dominant_color = centers[0].astype(int)
    color_name = closest_color(dominant_color)
    return color_name
def upload_image(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_instance = form.save()
            image_path = image_instance.image.path

            # Load pretrained model
            model = YOLO("yolov8n.pt")

            # Predict on the uploaded image
            image = Image.open(image_path)
            image_np = np.array(image)
            results = model(image_np)

            # Extract detected objects and their colors
            detected_objects = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls)
                    label = COCO_LABELS[class_id] if class_id < len(COCO_LABELS) else "Unknown"
                    confidence = float(box.conf)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Extract the object region from the image
                    object_roi = image_np[y1:y2, x1:x2]
                    dominant_color = get_dominant_color(object_roi)
                    detected_objects.append((label, confidence, x1, y1, x2, y2, dominant_color))

            # Save the results to a text file
            results_path = r'D:\prd\object_detection\detection\result.txt'
            os.makedirs(os.path.dirname(results_path), exist_ok=True)
            scraped_data = []
            with open(results_path, 'w', encoding='utf-8') as file:
                for obj in detected_objects:
                    file.write(f"Label: {obj[0]} Dominant Color: {obj[6]}\n")
                    # Scrape Amazon for products based on label and color
                    scraped_data.extend(scrape_amazon(obj[0], obj[6]))

                # Write scraped product data
                for i, product in enumerate(scraped_data, 1):
                    file.write(f"Product {i} Title: {product['title']}\n")
                    file.write(f"Product {i} Image: {product['image']}\n")
                    file.write(f"Product {i} Link: {product['link']}\n")
                    file.write(f"Product {i} Price: {product['price']}\n")
                    file.write(f"Product {i} Rating: {product['rating']}\n")
                    file.write(f"Product {i} Reviews: {product['reviews']}\n")
                    file.write(f"Product {i} Availability: {product['availability']}\n")
                    file.write("\n")

            return redirect('results', results_file=results_path)

    else:
        form = ImageUploadForm()
    return render(request, 'upload.html', {'form': form})

from django.shortcuts import render
from .summarizer import prd_info  # Assuming your summarizer function is in summarizer.py

def product_summary(request):
    url = request.GET.get('url')
    if not url:
        return render(request, 'error.html', {'message': 'Product URL not provided.'})
    
    product_details = prd_info(url)
    
    return render(request, 'product_summary.html', {'product': product_details})


def results(request, results_file):
    results_data = []
    try:
        with open(results_file, 'r', encoding='utf-8') as file:
            label = None
            color = None
            products = []

            for line in file:
                line = line.strip()
                if not label or not color:
                    label_match = re.match(r"Label: (.+) Dominant Color: (.+)", line)
                    if label_match:
                        label, color = label_match.groups()
                elif line.startswith("Product"):
                    product_info = {}
                    parts = line.split(": ", 1)
                    if len(parts) == 2:
                        key, value = parts
                        product_info['title'] = value
                        # Read the next lines to get other product details
                        for _ in range(6):  # Adjusted to read 6 additional lines including the image
                            parts = next(file).strip().split(": ", 1)
                            if len(parts) == 2:
                                k, v = parts
                                product_info[k.replace(f"Product {key.split(' ')[1]} ", "").lower()] = v
                        products.append(product_info)
            
            if label and color and products:
                results_data.append({'label': label, 'color': color, 'products': products})

    except FileNotFoundError:
        return render(request, 'error.html', {'message': 'Results file not found.'})

    return render(request, 'results.html', {'results': results_data})
