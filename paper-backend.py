from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO
import base64
import tensorflow as tf
import numpy as np
import cv2

app = Flask(__name__)
"""
import serial
import time
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
port = 'COM5'
serialInst.port = port
serialInst.baudrate = 115200
serialInst.open()
def send(data):
    response = ""
    command = (data)
    serialInst.write(command.encode('utf-8'))
    time.sleep(1)
    while serialInst.in_waiting:
        try:
            response = serialInst.readline().decode('utf-8').rstrip()
            print(response)
        except UnicodeDecodeError:
            print("m3lsh")


serialInst.close()
"""
"""
import serial
import timel
import serial.tools.list_ports
ports = serial.tools.list_ports.comports()
serialInst = serial.Serial()
port = '/dev/cu.usbmodem1101'
serialInst.port = port
serialInst.baudrate = 115200
serialInst.open()

response = ""
while True:
    command = input("Enter command to send to Arduino:")
    serialInst.write(command.encode('utf-8'))
    time.sleep(1)
    while serialInst.in_waiting:
        response = serialInst.readline().decode('utf-8').rstrip()
        print(response)
    if command == 'q':
        break

serialInst.close()
"""


def apply_nms(boxes, scores, max_output_size, iou_threshold):
    """Apply TensorFlow's NMS and return indices of kept boxes."""
    selected_indices = tf.image.non_max_suppression(
        boxes, scores, max_output_size=max_output_size, iou_threshold=iou_threshold)
    return selected_indices.numpy()


# Load TFLite model and allocate tensors
interpreter = tf.lite.Interpreter(model_path="dirt-debris.tflite")
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

#scaleX = width / 640
#scaleY = height / 640

orig_size = (1920, 888)
model_size = (640, 640)
display_size = (390, 844)

orig_width, orig_height = orig_size
model_width, model_height = model_size
display_width, display_height = display_size

scale_width_model = model_width / orig_width
scale_height_model = model_height / orig_height

scale_width_display = display_width / orig_width
scale_height_display = display_height / orig_height

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.json:
        return jsonify({"error": "No image part"}), 400

    # Decode the base64 image
    image_data = request.json['image']
    image_data = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_data))

    original_width, original_height = image.size
    # Convert image to RGB and resize
    image = image.convert('RGB')
    image = image.resize((640, 640), Image.LANCZOS)

    # Convert image to numpy array and preprocess for the model
    input_data = np.array(image)
    input_data = np.transpose(input_data, (2, 0, 1))  # Rearrange channel to first dimension
    input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension
    input_data = input_data.astype('float32') / 255.0  # Normalize

    # Set input tensor
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # Run inference
    interpreter.allocate_tensors()
    interpreter.invoke()

    # Extract output data using .tensor()
    output_tensor = interpreter.tensor(output_details[0]['index'])()  # Access the tensor directly
    output_data = np.squeeze(output_tensor, axis=0)  # Remove batch dimension if necessary

    output_data = output_data.reshape(5, 8400)
    
    # Scaling confidence by max confidence to bring scores between 0 and 1
    max_confidence = np.max(output_data[4, :])
    scaled_confidences = output_data[4, :] 

    # Filter out detections with confidence less than 0.3
    high_conf_indices = np.where(scaled_confidences >= 0.7)[0]
    high_conf_boxes = output_data[:, high_conf_indices]

    # Extract boxes for NMS
    boxes = np.stack([
        ((high_conf_boxes[0, :] - high_conf_boxes[2, :] / 2)) , # x_min scaled
        ((high_conf_boxes[1, :] - high_conf_boxes[3, :] / 2)), # y_min scaled
        ((high_conf_boxes[0, :] + high_conf_boxes[2, :] / 2) )  ,  # x_max scaled
        ((high_conf_boxes[1, :] + high_conf_boxes[3, :] / 2) ) # y_max scaled
    ], axis=-1)
    
    
    """
    boxes = np.stack([
    (high_conf_boxes[0, :] - high_conf_boxes[2, :] / 2) * (original_width / 640),  # x_min scaled
    (high_conf_boxes[1, :] - high_conf_boxes[3, :] / 2) * (original_height / 640), # y_min scaled
    (high_conf_boxes[0, :] + high_conf_boxes[2, :] / 2) * (original_width / 640),  # x_max scaled
    (high_conf_boxes[1, :] + high_conf_boxes[3, :] / 2) * (original_height / 640)  # y_max scaled
    ], axis=-1)

    
    """
    

    final_scores = scaled_confidences[high_conf_indices]

    # Apply NMS
    nms_indices = apply_nms(boxes, final_scores, max_output_size=100, iou_threshold=0.5)
    final_boxes = boxes[nms_indices]
    final_scores = final_scores[nms_indices]

    
    # Package the results
    results = {
        "boxes": final_boxes.tolist(),
        "scores": final_scores.tolist(),
    }
    print(results)
    return jsonify(results), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
    serialInst.close()
