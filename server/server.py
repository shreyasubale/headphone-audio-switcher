from flask import Flask, request, jsonify, send_file
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import io
import os
from datetime import datetime

app = Flask(__name__)

# Create a directory for output images if it doesn't exist
OUTPUT_DIR = 'output_images'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Initialize YOLO model
model = YOLO('models/yolov11n_headphone.pt')

@app.route('/output_images/<path:filename>')
def serve_image(filename):
    return send_file(os.path.join(OUTPUT_DIR, filename))

@app.route('/predict', methods=['POST'])
def predict():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        # Read and process image
        image_file = request.files['image']
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Run inference
        results = model(image)
        
        # Generate unique filename for the output image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'prediction_{timestamp}.jpg'
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        # Plot results and save
        result_plot = results[0].plot()  # BGR numpy array
        cv2.imwrite(output_path, result_plot)
        
        # Process results for JSON response
        predictions = []
        for result in results:
            for box in result.boxes:
                prediction = {
                    'class': result.names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist()
                }
                predictions.append(prediction)
        
        # Construct image URL
        image_url = f'/output_images/{output_filename}'
        
        return jsonify({
            'success': True,
            'predictions': predictions,
            'image_url': image_url
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
