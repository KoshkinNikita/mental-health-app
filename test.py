# test_tensorflow.py
import tensorflow as tf
print(f"TensorFlow version: {tf.__version__}")
print(f"Keras version: {tf.keras.__version__}")

# Простой тест
import numpy as np
model = tf.keras.Sequential([
    tf.keras.layers.Dense(10, activation='relu', input_shape=(5,)),
    tf.keras.layers.Dense(3, activation='softmax')
])
model.compile(optimizer='adam', loss='categorical_crossentropy')
print("✅ TensorFlow работает!")

# Тест с данными
x = np.random.random((100, 5))
y = tf.keras.utils.to_categorical(np.random.randint(0, 3, (100,)), num_classes=3)
history = model.fit(x, y, epochs=2, verbose=0)
print("✅ Обучение работает!")