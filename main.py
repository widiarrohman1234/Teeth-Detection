from flask import Flask, request, jsonify, send_file
import cv2
import numpy as np
from ultralytics import YOLO
import io
import base64

app = Flask(__name__)

model = YOLO("best.pt")


def get_roi(image):
    # Run YOLO model on the image
    results = model(image)
    rois = []
    for i, box in enumerate(results[0].boxes):
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        roi = image[y1:y2, x1:x2]
        rois.append(roi)
    return rois


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        # Read the image file in memory
        file_bytes = np.frombuffer(file.read(), np.uint8)
        source = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # Get ROIs from the image
        rois = get_roi(source)

        if len(rois) == 0:
            return jsonify({"error": "No objects detected"}), 404

        # Convert the first ROI to PNG and return as a response
        roi = rois[0]
        _, buffer = cv2.imencode(".png", roi)
        roi_bytes = io.BytesIO(buffer)
        
        type_response = request.form.get("type_response")
        if type_response == "image":
            return send_file(roi_bytes, mimetype='image/png')
        # Encode the ROI as a Base64 string
        elif type_response == "base_64":
            roi_base64 = base64.b64encode(roi_bytes.getvalue()).decode("utf-8")
            return jsonify({"roi_base64": roi_base64}), 200
        else:
            return send_file(roi_bytes, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "Healthy"})


if __name__ == "__main__":
    app.run(debug=True)
