#!/usr/bin/env python
# coding: utf-8

# # Resnet
# 
# ## Please watch Ng C4W2L01-C4W2L04, the first of which is found [here](https://www.youtube.com/watch?v=-bvTzZCEOdM&list=PLkDaE6sCZn6Gl29AoE31iwdVwSG-KnDzF&index=12).
# 
# The convolutional neural network that we developed and ran was adequate for use on a small problem with a few classes, but it lacks the explanatory power to produce highly accurate results for more difficult datasets.  Instead, more interesting neural networks have been developed which have greater explanatory power.  One of the most powerful architectures today is called ResNet, which is short for residual network.  
# 
# In principle, you could take the network that you've been working on and make it more flexible by adding more convolutional layers, which is to say that we could add more sequences of feature map generation.  This is what is meant when people use the term "deep" learning.  However, if you did this, you would quickly run into the problem that your network would struggle to learn weights in the lower (closer to the inputs) layers of the network.  This is a result of the way that neural networks are trained.  In particular they rely on the ability to take the derivative of a misfit function (e.g. least squares) with respect to a parameter, and to adjust the weight based on that derivative.  However in (naive) deep networks, this gradient has the tendency to become negligibly small as the impact of that weight gets lost in the myriad layers of convolutions and activations closer to the output.  
# 
# ResNet solves this problem by ensuring that the information in each weight gets propagated to the output.  It does this by simply adding the layer's input to each layer's output, so instead of 
# $$
# \mathbf{x}_{l+1} = \mathcal{F}_{l}(\mathbf{x}_l),
# $$
# at each layer, the neural network performs the operation
# $$
# \mathbf{x}_{l+1} = \mathcal{F}_{l}(\mathbf{x}_l) + \mathbf{x}_l.
# $$
# Rearranging this equation, we can see why this architecture is called a residual network:
# $$
# \mathbf{x}_{l+1} - \mathbf{x}_l = \mathcal{F}_{l}(\mathbf{x}_l).
# $$
# Each layer is modeling the residual between consecutive feature maps.  The pedantic amongst us will note that this only works when the output of $\mathcal{F}_{l}(\mathbf{x}_l)$ is the same size as the input.  This is dealt with by performing a suitable linear transformation on $\mathbf{x}_l$, making the equation
# $$
# \mathbf{x}_{l+1} = \mathcal{F}_{l}(\mathbf{x}_l) + W \mathbf{x}_l,
# $$
# where $W$ is a matrix that has learnable weights.  The matrix $W$ is most often formulated as a convolution with a 1x1 kernel size.   
# 
# The addition of the input is known as a *skip connection* because it looks like this:
# <img src=res_net.svg width=600/>
# The input is run through a normal conv layer (perhaps several) and then added to the output, where it can then be maxpooled or run through an activation or whatever.  
# 
# Keras makes these sorts of networks pretty easy to program.  To start with, let's apply this network to the CIFAR-10 classification problem, but we'll do it for all 10 classes.  All the non-model definition code should look the same as our previous example.   

# In[13]:


import keras
import keras.datasets as kd

(x_train, y_train), (x_test, y_test) = kd.cifar10.load_data()
labels = ['airplane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']

x_train = x_train/255.
x_test = x_test/255.

# Convert class vectors to binary class matrices.
N = len(labels)

y_train = keras.utils.to_categorical(y_train, N)
y_test = keras.utils.to_categorical(y_test, N)


# Now things get more interesting.  Obviously, ResNet as described above is more of a concept than a specific architecture: we'll need to make some more specific design choices.  One good way of doing this is to look at the literature and copy what others have done.  In particular, the [original ResNet Paper](https://arxiv.org/abs/1512.03385) provides an example of ResNet being applied to CIFAR-10 that yielded excellent accuracy (state of the art c. 2015).  Here, we'll emulate their network architecture, which looks like this:
# <img src=cifar_10_res_net.svg width=900/>
# More concretely, the layers of this network up to (and including) the location of the star in the figure above, look like this.

# In[14]:


import keras.layers as kl
import keras.regularizers as kr

# Note the alternative method for model specification: no model.add(.), instead we 
# perform sequential operations on layers, then we will make the resulting model later.

# Specify the shape of the input image
input_shape = x_train.shape[1:]
inputs = kl.Input(shape=input_shape)

# First convolution + BN + act
conv = kl.Conv2D(16,(3,3),padding='same',kernel_regularizer=kr.l2(1e-4))(inputs)
bn = kl.BatchNormalization()(conv)
act1 = kl.Activation('relu')(bn)

# Perform 3 convolution blocks
for i in range(3):
    conv = kl.Conv2D(16,(3,3),padding='same',kernel_regularizer=kr.l2(1e-4))(act1)
    bn = kl.BatchNormalization()(conv)
    act = kl.Activation('relu')(bn)
    
    conv = kl.Conv2D(16,(3,3),padding='same',kernel_regularizer=kr.l2(1e-4))(act)
    bn = kl.BatchNormalization()(conv)

    # Skip layer addition
    skip = kl.add([act1,bn])
    act1 = kl.Activation('relu')(skip)  

# Downsampling with strided convolution
conv = kl.Conv2D(32,(3,3),padding='same',strides=2,kernel_regularizer=kr.l2(1e-4))(act1)
bn = kl.BatchNormalization()(conv)
act = kl.Activation('relu')(bn)
conv = kl.Conv2D(32,(3,3),padding='same',kernel_regularizer=kr.l2(1e-4))(act)
bn = kl.BatchNormalization()(conv)

# Downsampling with strided 1x1 convolution
act1_downsampled = kl.Conv2D(32,(1,1),padding='same',strides=2,kernel_regularizer=kr.l2(1e-4))(act1)
# Downsampling skip layer
skip_downsampled = kl.add([act1_downsampled,bn])
act1 = kl.Activation('relu')(skip_downsampled)

# This final layer is denoted by a star in the above figure
for _ in range(2):
    conv = kl.Conv2D(32, (3, 3), padding="same", kernel_regularizer=kr.l2(1e-4))(act1)
    bn = kl.BatchNormalization()(conv)
    act = kl.Activation('relu')(bn)
    
    conv = kl.Conv2D(32, (3,3), padding='same', kernel_regularizer=kr.l2(1e-4))(act)
    bn = kl.BatchNormalization()(conv)
    
    # Skip layer addition
    skip = kl.add([act1,bn])
    act1 = kl.Activation('relu')(skip)
    
# Downsampling with strided convolution
conv = kl.Conv2D(64, (3,3), padding='same', strides=2, kernel_regularizer=kr.l2(1e-4))(act1)
bn = kl.BatchNormalization()(conv)
act = kl.Activation('relu')(bn)
conv = kl.Conv2D(64, (3,3), padding='same', kernel_regularizer=kr.l2(1e-4))(act)
bn = kl.BatchNormalization()(conv)

# Downsampling with strided 1x1 convolution
act1_downsampled = kl.Conv2D(64,(1,1),padding='same',strides=2,kernel_regularizer=kr.l2(1e-4))(act1)
# Downsampling skip layer
skip_downsampled = kl.add([act1_downsampled,bn])
act1 = kl.Activation('relu')(skip_downsampled)

# This final layer is denoted by a star in the above figure
for _ in range(2):
    conv = kl.Conv2D(64, (3, 3), padding="same", kernel_regularizer=kr.l2(1e-4))(act1)
    bn = kl.BatchNormalization()(conv)
    act = kl.Activation('relu')(bn)
    conv = kl.Conv2D(64, (3,3), padding='same', kernel_regularizer=kr.l2(1e-4))(act)
    bn = kl.BatchNormalization()(conv)
    
    # Skip layer addition
    skip = kl.add([act1,bn])
    act1 = kl.Activation('relu')(skip)


# To ensure that we have the output shape that we expect at this stage, we can look at the shape of act1  

# In[15]:


act1


# Which is an object of size 16x16x32, the correct size based on our chosen architecture (note the first question mark indicates an unknown number of input images: thus if we ran the model on a single photo, this would be a 1, if we ran it on the entire CIFAR training set at once it would be 50000).  As before, we can use this model for classification by doing global average pooling, then the softmax function.

# In[16]:


gap = kl.GlobalAveragePooling2D()(act1)
bn = kl.BatchNormalization()(gap)
final_dense = kl.Dense(N)(bn)
softmax = kl.Activation('softmax')(final_dense)


# In[17]:


import keras.models as km
model = km.Model(inputs=inputs,outputs=softmax)

# initiate adam optimizer
opt = keras.optimizers.rmsprop(lr=0.001,decay=1e-6)

model.compile(loss='categorical_crossentropy',
              optimizer=opt,
              metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=128,
          epochs=100,
          validation_data
          =(x_test, y_test),
          shuffle=True)


# While the code as is works, it is *not* the complete architecture given in the figure above.  **Implement the remainder of the network, and train the model for 100 epochs.** The complete architecture has quite a few parameters, so you'll definitely want to use a GPU, i.e. run it on the cluster (reference the job script included in this repo).
# 
# There are also a few extra tidbits to make this work better.  First, we'll want to checkpoint the model, which is to say that we'll want to save the weights anytime the model improves during the training process.  We can do this easily in Keras with a checkpoint function:

# In[ ]:


import keras.callbacks as kc
filepath = './checkpoints'

# Prepare callbacks for model saving and for learning rate adjustment.
checkpoint = kc.ModelCheckpoint(filepath=filepath,
                             monitor='val_acc',
                             verbose=1,
                             save_best_only=True)


# Note that these weights can then be loaded into a model on your local machine for more convenient post-processing and visualization of results.  We'll also want to reduce the learning rate as the model reaches an optimal solution.  We can do this with a *learning rate schedule*.
# 

# In[ ]:


def lr_schedule(epoch):
    lr = 1e-3
    if epoch > 60:
        lr *= 1e-3
    print('Learning rate: ', lr)
    return lr
lr_scheduler = kc.LearningRateScheduler(lr_schedule)


# We can include these two functions as *callbacks* to the optimizer:

# In[ ]:


model.fit(x_train, y_train,
          batch_size=128,
          epochs=100,
          validation_data=(x_test, y_test),
          shuffle=True,
          callbacks=[checkpoint,lr_scheduler])


# Once your model is fitted, **adapt your class activation mapping routine to run on this more advanced architecture, and compute a few examples?  How do these activation maps differ from those computed for the smaller network?**

# In[ ]:




