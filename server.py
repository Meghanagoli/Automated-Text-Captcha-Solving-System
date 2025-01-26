import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request
from tensorflow import keras
from tensorflow.keras import layers

# Define constants
img_width = 200
img_height = 80
max_length = 7



char_img_2 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '=', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
#char_img_1=  ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
char_img_1 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '=', '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

char_to_num_1 = layers.StringLookup(vocabulary=list(char_img_1), mask_token=None)
char_to_num_2 = layers.StringLookup(vocabulary=list(char_img_2), mask_token=None)

# Convert integers to characters for each model
num_to_char_1 = layers.StringLookup(vocabulary=char_to_num_1.get_vocabulary(), mask_token=None, invert=True)
num_to_char_2 = layers.StringLookup(vocabulary=char_to_num_2.get_vocabulary(), mask_token=None, invert=True)

# Custom CTC layer
class LayerCTC(keras.layers.Layer):
    def __init__(self, **kwargs):
        super(LayerCTC, self).__init__(**kwargs)
        self.loss_fn = keras.backend.ctc_batch_cost

    def call(self, y_true, y_pred):
        batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
        input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
        label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")

        input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
        label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")

        loss = self.loss_fn(y_true, y_pred, input_length, label_length)
        self.add_loss(loss)

        # Return the predictions (used during inference)
        return y_pred

    @classmethod
    def from_config(cls, config):
        config.pop('trainable', None)
        return cls(**config)              

# Load the trained models with custom CTC layer

model_path_1 = "./MODELS/DATASET.h5"  # Change this to your model path for model 1
model_path_2 = "./MODELS/ALL_IN_ONE.h5" 
 # Change this to your model path for model 2
model_1 = keras.models.load_model(model_path_1, custom_objects={'CTCLayer': LayerCTC})
model_2 = keras.models.load_model(model_path_2, custom_objects={'CTCLayer': LayerCTC})

input_img_1 = model_1.input[0]  # Accessing the input layer correctly for model 1
output_pred_1 = model_1.get_layer(name="dense2").output  # Accessing the dense layer output for model 1
prediction_model_1 = keras.models.Model(inputs=input_img_1, outputs=output_pred_1)

input_img_2 = model_2.input[0]  # Accessing the input layer correctly for model 2
output_pred_2 = model_2.get_layer(name="dense2").output  # Accessing the dense layer output for model 2
prediction_model_2 = keras.models.Model(inputs=input_img_2, outputs=output_pred_2)

# Decode the predicted output
def decode_batch_predictions(pred, num_to_char_mapping):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]  # Assuming the sequence length is the width of the image
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :max_length]
    
    output_text = []
    for res in results:
        # Decode the numerical prediction to text using the num_to_char mapping
        res = tf.strings.reduce_join(num_to_char_mapping(res)).numpy().decode("utf-8")
        output_text.append(res)
    return output_text


# Preprocess the input image
def preprocess_image(image_path):
    img = tf.io.read_file(image_path)
    img = tf.io.decode_png(img, channels=1)  # Ensure it's grayscale
    img = tf.image.convert_image_dtype(img, tf.float32)  # Convert to float32
    img = tf.image.resize(img, [img_height, img_width])  # Resize image
    img = tf.transpose(img, perm=[1, 0, 2])  # Transpose to match the model input format
    img = tf.expand_dims(img, axis=0)  # Add batch dimension
    return img

# Score Calculation (could be based on softmax, confidence, etc.)
def calculate_score(preds, decoded_text):
    """
    Calculate a score for the model prediction based on the output and decoded text.
    Penalize if there are [UNK] tokens in the prediction.
    """
    # Calculate softmax probabilities (if the model outputs logits)
    softmax_preds = tf.nn.softmax(preds, axis=-1)  # Apply softmax to get probabilities
    pred_confidence = tf.reduce_max(softmax_preds, axis=-1)  # Get max probability per character

    # Penalize the score if there are [UNK] tokens
    
    confidence_score = tf.reduce_mean(pred_confidence)    # Average confidence minus penalty

    return confidence_score.numpy()  # Convert to NumPy for easy handling
# Prediction function to compare two models and return the best

app = Flask(__name__)

def predict_best_model(img):
    # Preprocess the image
    img = preprocess_image(img)

    # Get the prediction for both models (using different char_img for each model)
    preds_1 = prediction_model_1.predict(img)  # Model 1 prediction
    preds_2 = prediction_model_2.predict(img)  # Model 2 prediction
    
    # Decode the predictions to text using different character mappings
    pred_texts_1 = decode_batch_predictions(preds_1, num_to_char_1)
    pred_texts_2 = decode_batch_predictions(preds_2, num_to_char_2)
    
    # Calculate scores for both predictions
    score_1 = calculate_score(preds_1, pred_texts_1[0])
    score_2 = calculate_score(preds_2 ,pred_texts_2[0])
   
    print("model-1",pred_texts_1[0],"score",score_1)
    print("model-2",pred_texts_2[0],"score",score_2)
    # Compare the scores and return the best prediction
    if score_1 > score_2:
       
        return pred_texts_1[0], score_1  # Return the predicted text and score from model 1
    else:
        
        return pred_texts_2[0], score_2  # Return the predicted text and score from model 2





@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Save the file temporarily
        print("file rec")
        file_path = './image.png'  # Change this path as needed
        file.save(file_path)
        
        # Pass the saved file path to the prediction function
        predicted_text, score = predict_best_model(file_path)
        final=predicted_text.replace("[UNK]", "")

        return jsonify({'predicted_text': final})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
