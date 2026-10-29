"""
UV-fluorescence image classifier for aflatoxin contamination risk.
Uses transfer learning on MobileNetV2 for a lightweight, fast-training model.
"""

import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

IMG_SIZE = (224, 224)


def build_model(num_classes=2):
    base_model = MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
    base_model.trainable = False  # freeze pretrained layers initially

    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(64, activation="relu"),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def train_model(train_dir, val_dir, epochs=10, save_path="../models/uv_classifier.h5"):
    train_ds = tf.keras.utils.image_dataset_from_directory(train_dir, image_size=IMG_SIZE)
    val_ds = tf.keras.utils.image_dataset_from_directory(val_dir, image_size=IMG_SIZE)

    model = build_model()
    model.fit(train_ds, validation_data=val_ds, epochs=epochs)
    model.save(save_path)
    return model


def load_model(path="../models/uv_classifier.h5"):
    return tf.keras.models.load_model(path)


def predict_image(model, image_path: str) -> dict:
    img = tf.keras.utils.load_img(image_path, target_size=IMG_SIZE)
    img_array = tf.keras.utils.img_to_array(img) / 255.0
    img_array = tf.expand_dims(img_array, 0)

    predictions = model.predict(img_array)[0]
    class_names = ["not_contaminated", "contaminated"]
    predicted_class = class_names[predictions.argmax()]
    confidence = float(predictions.max())

    risk_map = {"not_contaminated": "Low", "contaminated": "High"}

    return {
        "contamination_risk": risk_map[predicted_class],
        "confidence": round(confidence, 2),
    }