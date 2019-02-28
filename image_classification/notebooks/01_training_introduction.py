#!/usr/bin/env python
# coding: utf-8

# # Introduction to Training Image Classification Models

# In this notebook, we will give an introduction to using fast.ai for image classification. We will use a small dataset of four differenet beverages to train and evaluate a model. We'll also cover one of the most common ways to store your data in your file system for image classification modelling.

# Check out fastai version.

# In[10]:


import fastai
fastai.__version__


# Ensure edits to libraries are loaded and plotting is shown in the notebook.

# In[11]:


get_ipython().run_line_magic('reload_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')
get_ipython().run_line_magic('matplotlib', 'inline')


# Import fastai. For now, we'll import all (`import *`) so that we can easily use different utilies provided by the fastai library.

# In[12]:


import sys
sys.path.append("../")
from pathlib import Path
from utils_ic.datasets import Urls, unzip_url, data_path
from fastai.vision import *
from fastai.metrics import error_rate, accuracy


# Set some parameters. We'll use the `unzip_url` helper function to download and unzip our data.

# In[13]:


DATA_PATH     = unzip_url(Urls.fridge_objects_path)
EPOCHS        = 5
LEARNING_RATE = 1e-4
IMAGE_SIZE    = 299
BATCH_SIZE    = 16
ARCHITECTURE  = models.resnet50


# In[14]:


Urls.fridge_objects_path


# ---

# ## File Structure for Image Classification

# In this notebook, we'll use images from the `fridge_objects` dataset, which has been downloaded and unzip to  `image_classification/data`.
# 
# Lets set that directory to our `path` variable, which we'll use throughout the notebook, and checkout what's inside:

# In[15]:


path = Path(DATA_PATH)
path.ls()


# You'll notice that we have four different folders inside:
# - `/milk_bottle`
# - `/carton`
# - `/water_bottle`
# - `/can`

# The most common data format for multiclass image classification is to have a folder titled the label with the images inside:
# 
# ```
# /images
# +-- can (class 1)
# |   +-- image1.jpg
# |   +-- image2.jpg
# |   +-- ...
# +-- carton (class 2)
# |   +-- image31.jpg
# |   +-- image32.jpg
# |   +-- ...
# +-- ...
# ```
# 
# Good thing our data is already structured in that format!

# ## Loading images with fast.ai

# To use fastai, we want to create an ImageDataBunch so that the library can easily use multiple images (mini-batches) during training time. We create an ImageDataBunch by using fastai's [data_block apis](https://docs.fast.ai/data_block.html).

# In[16]:


np.random.seed(42)
data = ImageItemList     .from_folder(path)     .random_split_by_pct(valid_pct=0.2, seed=10)     .label_from_folder()     .transform(size=IMAGE_SIZE)     .databunch(bs=BATCH_SIZE)     .normalize(imagenet_stats)


# Lets take a look at our data using the databunch we created.

# In[17]:


data.show_batch(rows=3, figsize=(15,11))


# Lets see all available classes:

# In[18]:


print(f'number of classes: {data.c}')
print(data.classes)


# We can also see how many images we have in our training and validation set.

# In[19]:


data.batch_stats


# Above, you'll notice that the validation set is 20% of the total images. 
# 
# You'll also notice that the test set will be set to `None`. This is because we treat it as a second holdout set that is only used right at the end of a project.

# ## Training

# For the model, we use a concolutional neural network. 
# 
# When training a model, there are many hypter parameters to select, such as the learning rate, the model architecture, layers to tune, and many more. 
# 
# With fastai, we can use the `create_cnn` function that allows us to specify the model architecture and a performance indicator (metric). At this point, we already benefit from transfer learning since we download the parameters used to train imagenet. 

# In[20]:


learn = create_cnn(data, ARCHITECTURE, metrics=accuracy)


# Unfreeze our CNN so that we're training all the layers.

# In[21]:


learn.unfreeze()


# We can call the `fit` function to train the dnn.

# In[22]:


learn.fit(EPOCHS, LEARNING_RATE)


# ## Evaluating

# To evaluate our model, lets take a look at the accuracy on the validation set.

# In[23]:


_, metric = learn.validate(learn.data.valid_dl, metrics=[accuracy])
print(f'Accuracy on validation set: {float(metric)}')


# When evaluating our results, we want to see where the model messes up, and whether or not we can do better. So we're interested in seeing images where the model predicted the image incorrectly but with high confidence (images with the highest loss).

# In[24]:


interp = ClassificationInterpretation.from_learner(learn)


# In[25]:


interp.plot_confusion_matrix()


# In[26]:


interp.plot_top_losses(9, figsize=(15,11))
