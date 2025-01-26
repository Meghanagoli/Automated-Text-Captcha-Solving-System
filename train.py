import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# Path to the Dataset
dataset_path = Path("/Users/vineeshreddy/Downloads/DATASETS/IRCTC")
img_paths = sorted(list(map(str, dataset_path.glob("*.png"))))
img_labels = [img.split(os.path.sep)[-1].split(".png")[0] for img in img_paths]
unique_chars = sorted(set(char for label in img_labels for char in label))

print("Number of images found:", len(img_paths))
print("Number of labels found:", len(img_labels))
print("Unique characters:", unique_chars)

# Training Parameters
batch_size = 6
img_width, img_height = 200, 80
downsample_factor = 4
max_length = max(len(label) for label in img_labels)

# Character mapping
char_to_num = layers.StringLookup(vocabulary=list(unique_chars), mask_token=None)
num_to_char = layers.StringLookup(vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True)

# Split Dataset
def data_split(img_paths, img_labels, train_size=0.9, shuffle=True):
    size = len(img_paths)
    indices = np.arange(size)
    if shuffle:
        np.random.shuffle(indices)
    train_samples = int(size * train_size)
    x_train, y_train = np.array(img_paths)[indices[:train_samples]], np.array(img_labels)[indices[:train_samples]]
    x_valid, y_valid = np.array(img_paths)[indices[train_samples:]], np.array(img_labels)[indices[train_samples:]]
    return x_train, x_valid, y_train, y_valid

x_train, x_valid, y_train, y_valid = data_split(img_paths, img_labels)


def encode_sample(img_path, label):
    img = tf.io.read_file(img_path)
    img = tf.io.decode_png(img, channels=3)
    if img.shape[-1] == 3:
        img = tf.image.rgb_to_grayscale(img)
    img = tf.image.convert_image_dtype(img, tf.float32)
    img = tf.image.resize(img, [img_height, img_width])
    img = tf.transpose(img, perm=[1, 0, 2])
    label = char_to_num(tf.strings.unicode_split(label, input_encoding="UTF-8"))
    
    # Pad or trim the label to match max_length
    label = tf.pad(label, [[0, max_length - tf.shape(label)[0]]], constant_values=0)
    label = tf.reshape(label, [max_length])
    
    return {"image": img, "label": label}


# Dataset Preparation
train_data = tf.data.Dataset.from_tensor_slices((x_train, y_train))
train_data = train_data.map(encode_sample, num_parallel_calls=tf.data.AUTOTUNE).batch(batch_size).prefetch(tf.data.AUTOTUNE)
val_data = tf.data.Dataset.from_tensor_slices((x_valid, y_valid))
val_data = val_data.map(encode_sample, num_parallel_calls=tf.data.AUTOTUNE).batch(batch_size).prefetch(tf.data.AUTOTUNE)

# CTC Loss Layer
class CTCLayer(keras.layers.Layer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.loss_fn = keras.backend.ctc_batch_cost

    def call(self, y_true, y_pred):
        batch_len = tf.cast(tf.shape(y_true)[0], dtype="int64")
        input_length = tf.cast(tf.shape(y_pred)[1], dtype="int64")
        label_length = tf.cast(tf.shape(y_true)[1], dtype="int64")
        input_length = input_length * tf.ones(shape=(batch_len, 1), dtype="int64")
        label_length = label_length * tf.ones(shape=(batch_len, 1), dtype="int64")
        loss = self.loss_fn(y_true, y_pred, input_length, label_length)
        self.add_loss(loss)
        return y_pred

# Model Building
def build_model():
    input_img = layers.Input(shape=(img_width, img_height, 1), name="image", dtype="float32")
    labels = layers.Input(name="label", shape=(None,), dtype="float32")

    x = layers.Conv2D(32, (3, 3), activation="relu", kernel_initializer="he_normal", padding="same", name="Conv1")(input_img)
    x = layers.MaxPooling2D((2, 2), name="pool1")(x)
    x = layers.Conv2D(64, (3, 3), activation="relu", kernel_initializer="he_normal", padding="same", name="Conv2")(x)
    x = layers.MaxPooling2D((2, 2), name="pool2")(x)
    new_shape = ((img_width // 4), (img_height // 4) * 64)
    x = layers.Reshape(target_shape=new_shape, name="reshape")(x)
    x = layers.Dense(64, activation="relu", name="dense1")(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.25))(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True, dropout=0.25))(x)
    x = layers.Dense(len(char_to_num.get_vocabulary()) + 1, activation="softmax", name="dense2")(x)
    output = CTCLayer(name="ctc_loss")(labels, x)
    
    model = keras.models.Model(inputs=[input_img, labels], outputs=output, name="ocr_model_v1")
    model.compile(optimizer=keras.optimizers.Adam())
    return model

model = build_model()
model.summary()

# Early Stopping Parameters and Training
epochs = 100
early_stopping = keras.callbacks.EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)

# Model Path
model_path = "./MODELS/DATASET.h5"
if os.path.exists(model_path):
    model = keras.models.load_model(model_path, custom_objects={'CTCLayer': CTCLayer})
    print("Model loaded from", model_path)
else:
    model.fit(train_data, validation_data=val_data, epochs=epochs, callbacks=[early_stopping])
    model.save(model_path)

# Prediction Model
input_img = model.input[0]
output_pred = model.get_layer(name="dense2").output
prediction_model = keras.models.Model(inputs=input_img, outputs=output_pred)

# Decoding Predictions
def decode_batch_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :max_length]
    output_text = [tf.strings.reduce_join(num_to_char(res)).numpy().decode("utf-8") for res in results]
    return output_text

# Save Predicted Images
output_dir = "predicted_images"
preprocessed_dir = "preprocessed_images"
os.makedirs(output_dir, exist_ok=True)
os.makedirs(preprocessed_dir, exist_ok=True)

for batch in val_data.take(1):
    batch_images = batch["image"]
    batch_labels = batch["label"]
    preds = prediction_model.predict(batch_images)
    pred_texts = decode_batch_predictions(preds)
    orig_texts = [tf.strings.reduce_join(num_to_char(label)).numpy().decode("utf-8") for label in batch_labels]

    for i in range(len(pred_texts)):
        img = (batch_images[i, :, :, 0] * 255).numpy().astype(np.uint8).T
        preprocessed_output_path = os.path.join(preprocessed_dir, f"preprocessed_{i}.png")
        plt.imsave(preprocessed_output_path, img, cmap="gray")
        print(f"Saved Preprocessed Image: {preprocessed_output_path}")

        output_path = os.path.join(output_dir, f"predicted_{i}_text_{pred_texts[i]}.png")
        plt.imsave(output_path, img, cmap="gray")
        print(f"Saved Predicted Image: {output_path}")
        plt.imshow(img, cmap="gray")
        plt.title(f"Pred: {pred_texts[i]}\nTrue: {orig_texts[i]}")
        plt.axis("off")
        plt.show()
