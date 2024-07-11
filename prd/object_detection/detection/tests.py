from django.test import TestCase

# Create your tests here.
import cv2
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Function to extract the dominant color
def get_dominant_color(image, k=4):
    # Reshape the image to be a list of pixels
    pixels = image.reshape((-1, 3))

    # Cluster pixels
    kmeans = KMeans(n_clusters=k)
    kmeans.fit(pixels)

    # Find the most common color
    counts = np.bincount(kmeans.labels_)
    dominant_color = kmeans.cluster_centers_[counts.argmax()]

    return dominant_color

# Load image and YOLO model
image = cv2.imread(r'D:\prd\object_detection\images\WhatsApp_Image_2024-07-04_at_2.02.47_PM_5dzA1zJ.jpeg')
net = cv2.dnn.readNet('yolov4.weights', 'yolov4.cfg')
layer_names = net.getLayerNames()
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]

# Preprocess the image
blob = cv2.dnn.blobFromImage(image, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
net.setInput(blob)
outs = net.forward(output_layers)

# Extract bounding boxes
height, width, channels = image.shape
boxes = []
confidences = []
class_ids = []

for out in outs:
    for detection in out:
        scores = detection[5:]
        class_id = np.argmax(scores)
        confidence = scores[class_id]
        if confidence > 0.5:
            center_x = int(detection[0] * width)
            center_y = int(detection[1] * height)
            w = int(detection[2] * width)
            h = int(detection[3] * height)

            x = int(center_x - w / 2)
            y = int(center_y - h / 2)

            boxes.append([x, y, w, h])
            confidences.append(float(confidence))
            class_ids.append(class_id)

# Non-maximum suppression to remove overlapping bounding boxes
indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

# Extract and analyze each detected object
for i in indices:
    i = i[0]
    box = boxes[i]
    x, y, w, h = box[0], box[1], box[2], box[3]
    cropped_image = image[y:y+h, x:x+w]

    # Get the dominant color
    dominant_color = get_dominant_color(cropped_image, k=4)

    # Draw bounding box and color
    label = "Color: {}".format(dominant_color)
    cv2.rectangle(image, (x, y), (x + w, y + h), dominant_color.astype(int).tolist(), 2)
    cv2.putText(image, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, dominant_color.astype(int).tolist(), 2)

# Show the final image
cv2.imshow('Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
