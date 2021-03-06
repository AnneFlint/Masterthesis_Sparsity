# -*- coding: utf-8 -*-
"""GitHub_MasterFile.ipynb

Code for Masterthesis of Anne Flint
(Spring Semester 2020)

Title: Modelling sparsity in deep neural networks - application to healthcare data

Joint Masters Programme in Health Informatics at Karolinska Institutet and Stockholm University
"""

pip install -q tensorflow-model-optimization

# Commented out IPython magic to ensure Python compatibility.
import tempfile
import os
import random

import tensorflow as tf
import numpy as np
import pandas as pd

from tensorflow import keras
from tensorflow.keras import layers

# %load_ext tensorboard

from google.colab import drive

# This will prompt for authorization.
drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
#Set working directory (change according to your own folder structure)
# %cd /content/drive/My\ Drive/CheXpert-v1.0-small

"""# Load CheXpert Data
## Load files
"""

#For this thesis, the CheXpert dataset was preprocessed and downscaled to a 28x28 size.
train_data = np.load("chexpert_train_28_28.npz")
train_images = train_data["images"] 
train_labels = train_data["targets"]

#If validation set is used as test set, load this dataframe also
valid_data = np.load("chexpert_valid_28_28.npz")
test_images = valid_data["images"] 
test_labels = valid_data["targets"]

"""## Balance Data
Balance data with random under sampling. Source: [imbalanced learn](https://imbalanced-learn.readthedocs.io/en/stable/generated/imblearn.under_sampling.RandomUnderSampler.html#imblearn.under_sampling.RandomUnderSampler)
"""

from imblearn.under_sampling import RandomUnderSampler

# Flatten version of the images for compatibility resons
train_images_flatten = list()
for i in range(len(train_images)):
    train_images_flatten.append(train_images[i].flatten())

# Balance the data with ramdom undersampling 
print(f"n before under sampling: {len(train_labels)}")
under_sampler = RandomUnderSampler(random_state=0, return_indices=True)
_, _, balanced_indices = under_sampler.fit_resample(train_images_flatten, train_labels)
train_images = train_images[balanced_indices]
train_labels = train_labels[balanced_indices]

"""## Split in train and test data
Use a random split to split the original train data in 90% train and 10% test data.
"""

from sklearn.model_selection import StratifiedShuffleSplit

# Flatten version of the images for compatibility resons
train_images_flatten = list()
for i in range(len(train_images)):
    train_images_flatten.append(train_images[i].flatten())

rs = StratifiedShuffleSplit(n_splits=1, test_size=0.1, random_state=0)
train_indices, test_indices = next(rs.split(train_images_flatten, train_labels))


#new 29.7 
test_images = train_images[test_indices]
test_labels = train_labels[test_indices]
train_images = train_images[train_indices]
train_labels = train_labels[train_indices]

"""# Load MNIST dataset"""

# Load MNIST dataset, skip this step if you are using CheXpert
mnist = keras.datasets.mnist
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()

"""# Data Inspection
Visulize the data for senity checks.
"""

from IPython.display import display
from PIL import Image
print(f"n train data: {len(train_labels)}")
print(f"n test data: {len(test_labels)}")
print("\n== train images ==")
display(Image.fromarray(train_images[0]))
print(pd.DataFrame(train_images[0]))
print(pd.DataFrame(train_images[0].flatten()).describe())
print("\n== train labels ==")
print(pd.DataFrame(train_labels))
print(pd.DataFrame(train_labels).describe())

"""# Data Normalization
## Option A:
Normalize the input image so that each pixel value is between 0 to 1.
"""

train_images_max = np.max(train_images) # should be 255.0
train_images = train_images / train_images_max
test_images = test_images / train_images_max
#valid_images = valid_images / train_images_max

"""## Option B:
Normilze the input images with a standard scale. z = (x - u) / s
Example source: [StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
"""

train_images_mean = np.mean(train_images)
train_images_std = np.std(train_images)
train_images = (train_images - train_images_mean) / train_images_std
test_images = (test_images - train_images_mean) / train_images_std
#valid_images = (valid_images - train_images_mean) / train_images_std

"""## Visual inspection
Visulize data after normalization:
"""

print(pd.DataFrame(train_images[0]))

"""# Option A: Train baseline model"""

#Set Seed
random.seed(3)

# Define the model architecture.
model = keras.Sequential([
  keras.layers.InputLayer(input_shape=(28, 28)),
  keras.layers.Reshape(target_shape=(28, 28, 1)),
  keras.layers.Conv2D(filters=12, kernel_size=(3, 3), activation='relu'),
  keras.layers.MaxPooling2D(pool_size=(2, 2)),
  keras.layers.Flatten(),
  keras.layers.Dense(10)
])

# Train the digit classification model
model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])

history = model.fit(
  train_images,
  train_labels,
  epochs=10,
  validation_split=0.2,
)

"""# Option B: Train model inkl. L1-Regularization"""

from tensorflow.keras import regularizers

random.seed(3)


# Define the model architecture, kernel/weight regularizer added in conv. layer
model = keras.Sequential([
  keras.layers.InputLayer(input_shape=(28, 28)),
  keras.layers.Reshape(target_shape=(28, 28, 1)),
  keras.layers.Conv2D(filters=12, kernel_size=(3, 3), activation='relu',kernel_regularizer=regularizers.l1(0.01)), #bias_regularizer=regularizers.l1(0.01)),
  keras.layers.MaxPooling2D(pool_size=(2, 2)),
  keras.layers.Flatten(),
  keras.layers.Dense(10)
])

# Compile the model
model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])

history = model.fit(
  train_images,
  train_labels,
  epochs=10,
  validation_split=0.2,
)

"""# Evaluate Model Performance"""

_, baseline_model_accuracy = model.evaluate(
    test_images, test_labels, verbose=0)

print('Baseline test accuracy:', baseline_model_accuracy)

_, keras_file = tempfile.mkstemp('.h5')
tf.keras.models.save_model(model, keras_file, include_optimizer=False)
print('Saved baseline model to:', keras_file)

#Packages for Visualization and File Download
import matplotlib.pyplot as plt
from google.colab import files

# summarize history for training accuracy
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('L1 Regulated MNIST training accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper right')
#Change name of file when running with different training set
plt.savefig('mnist_trainingaccuracy_l1.png')
#files.download('TrainingAccuracy_baseline.png')
plt.show()

# summarize history for training loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('L1 Regulated MNIST training loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper left')
#Change name of file when running with different training set
plt.savefig('mnist_trainingoss_l1.png')
#files.download('TrainingLoss_baseline.png')
plt.show()

"""# Apply Magnitude Pruning to baseline model from Option A"""

import tensorflow_model_optimization as tfmot

prune_low_magnitude = tfmot.sparsity.keras.prune_low_magnitude

random.seed(3)

# Make alterations here, depending on the set that gets pruned. 
batch_size = 128  
epochs = 10
validation_split = 0.2 # 20% of training set will be used for validation set  

num_images = train_images.shape[0] * (1 - validation_split)
end_step = np.ceil(num_images / batch_size).astype(np.int32) * epochs

# Define model for pruning, prune 50% - XX% of the parameters
pruning_params = {
      'pruning_schedule': tfmot.sparsity.keras.PolynomialDecay(initial_sparsity=0.50,
                                                               final_sparsity=0.90,
                                                               begin_step=0,
                                                               end_step=end_step)
}

model_for_pruning = prune_low_magnitude(model, **pruning_params)

# `prune_low_magnitude` requires a recompile.
model_for_pruning.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])

model_for_pruning.summary()

logdir = tempfile.mkdtemp()

callbacks = [
  tfmot.sparsity.keras.UpdatePruningStep(),
  tfmot.sparsity.keras.PruningSummaries(log_dir=logdir),
]
  
history2 = model_for_pruning.fit(train_images, train_labels,
                  batch_size=batch_size, epochs=epochs, validation_split=validation_split,
                  callbacks=callbacks)

"""Compare accuracy of baseline model and pruned model"""

_, model_for_pruning_accuracy = model_for_pruning.evaluate(
   test_images, test_labels, verbose=0)

print('Baseline test accuracy:', baseline_model_accuracy) 
print('Pruned test accuracy:', model_for_pruning_accuracy) #this is the accuracy after 10 epochs

# summarize history for training accuracy
plt.plot(history2.history['accuracy'])
plt.plot(history2.history['val_accuracy'])
plt.title('Pruned CheXpert training accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper left')
#Change name of file when running with different training set
plt.savefig('chexpert_TrainingAccuracy_pruning50.png')
#files.download('TrainingAccuracy_baseline.png')
plt.show()

# summarize history for training loss
plt.plot(history2.history['loss'])
plt.plot(history2.history['val_loss'])
plt.title('Pruned CheXpert training loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='upper left')
#Change name of file when running with different training set
plt.savefig('chexpert_TrainingLoss_pruning50.png')
#files.download('TrainingLoss_baseline.png')
plt.show()

"""# Check Storage Requirements"""

model_for_export = tfmot.sparsity.keras.strip_pruning(model_for_pruning)

_, pruned_keras_file = tempfile.mkstemp('.h5')
tf.keras.models.save_model(model_for_export, pruned_keras_file, include_optimizer=False)
print('Saved pruned Keras model to:', pruned_keras_file)

#Option to apply TFLite Converter as another mean to save the pruned model 
converter = tf.lite.TFLiteConverter.from_keras_model(model_for_export)
pruned_tflite_model = converter.convert()

_, pruned_tflite_file = tempfile.mkstemp('.tflite')

with open(pruned_tflite_file, 'wb') as f:
  f.write(pruned_tflite_model)

print('Saved pruned TFLite model to:', pruned_tflite_file)

def get_gzipped_model_size(file):
  # Returns size of gzipped model, in bytes.
  import os
  import zipfile

  _, zipped_file = tempfile.mkstemp('.zip')
  with zipfile.ZipFile(zipped_file, 'w', compression=zipfile.ZIP_DEFLATED) as f:
    f.write(file)

  return os.path.getsize(zipped_file)

"""Compare size of models"""

print("Size of gzipped baseline Keras model: %.2f bytes" % (get_gzipped_model_size(keras_file)))
print("Size of gzipped pruned Keras model: %.2f bytes" % (get_gzipped_model_size(pruned_keras_file)))
print("Size of gzipped pruned TFlite model: %.2f bytes" % (get_gzipped_model_size(pruned_tflite_file)))
