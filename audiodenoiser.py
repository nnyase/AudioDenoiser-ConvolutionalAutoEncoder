# -*- coding: utf-8 -*-
"""audio (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mEthrr-wBEtlq1Lb-mwOC5KVZ-GbNmph
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import librosa
import IPython

import pickle
    
# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("device=", device)

def signal2pytorch(x):
    #Function to convert a signal vector x, like a mono audio signal, into a 3-d Tensor that conv1d of Pytorch expects,
    #https://pytorch.org/docs/stable/nn.html
    #Argument x: a 1-d signal as numpy array
    #input x[batch,sample]
    #output: 3-d Tensor X for conv1d input.
    #for conv1d Input: (N,Cin,Lin), Cin: numer of input channels (e.g. for stereo), Lin: length of signal, N: number of Batches (signals) 
    X = np.expand_dims(x, axis=0)  #add channels dimension (here only 1 channel)
    if len(x.shape)==1: #mono:
        X = np.expand_dims(X, axis=0)  #add batch dimension (here only 1 batch)
    X=torch.from_numpy(X)
    X=X.type(torch.Tensor)
    X=X.permute(1,0,2)  #make batch dimension first
    return X

class Convautoenc(nn.Module):
    def __init__(self):
        super(Convautoenc, self).__init__()
        #Analysis Filterbank with downsampling of N=1024, filter length of 2N, but only N/2 outputs:
        self.conv1=nn.Conv1d(in_channels=1, out_channels=32, kernel_size=2048, stride=32,padding= 1012,bias=True) #Padding for 'same' filters (kernel_size/2-1)

        #Synthesis filter bank:
        self.synconv1=nn.ConvTranspose1d(in_channels=32, out_channels=1, kernel_size=2048, padding= 1012,stride=32, bias=True)

    def encoder(self, x):
        #Analysis:
        x = self.conv1(x)
        y = torch.tanh(x)
        return y
      
    def decoder(self, y):
        #Synthesis:
        xrek= self.synconv1(y)
        return xrek
      
    def forward(self, x):
        y=self.encoder(x)
        #y=torch.round(y/0.125)*0.125
        xrek=self.decoder(y)
        return xrek

from google.colab import drive
drive.mount('/content/drive')

# Convert from pickle to wavfiles

dataset = "/content/drive/MyDrive/Deep Learning Course/denoise_dataset.pkl"
testset = "/content/drive/MyDrive/Deep Learning Course/denoise_testset_noisy.pkl"

x,y = np.load(dataset, allow_pickle=True)
test = np.load(testset, allow_pickle=True)

print("Clean sample: ", x.shape)
print("Noisy sample: ", y.shape)
print("test sample: ",test.shape)

IPython.display.Audio(x[0], rate = x.shape[1])

IPython.display.Audio(y[0], rate = y.shape[1])

IPython.display.Audio(test[1], rate = test.shape[1])

def evaluate(clean, denoised):
    """"
    This function compares two set of signals by calculating the MSE (Mean squared error), MAE (Mean absolute error),
    and SNR (signal to noise ratio) in db averaged over all the signals.
    Receives two matrices of shape N, D. That correspond to N signals of length D.
    clean: a 2D numpy array containing the clean (original) signals.
    denoised: a 2D numpy array containing the denoised (reconstructed) versions of the original signals.
    """

    #MSE and MAE
    se = ((denoised - clean) ** 2).mean(-1)
    mse = se.mean()
    mae = np.abs(denoised - clean).mean(-1).mean()

    #SNR and PSNR
    num = (clean**2).sum(-1)
    den = ((denoised - clean) ** 2).sum(-1)
    ep = 1e-9
    SNR = 20*np.log10(np.sqrt(num)/(np.sqrt(den) + ep)).mean()

    return mse, mae, SNR

from librosa import display
display.waveplot(x[0],sr = 11000)

display.waveplot(y[0],sr =5500)

from scipy import signal
#new_y= signal.resample_poly(y[0], 2,1)
#print(x[0].shape)
#new_y.shape
testing = np.empty([9600,11000])

for i in range(len(y)):
  array = signal.resample_poly(y[i], 2, 1)
  testing[i] = array

print(testing.shape)

batch = 1

X_train=signal2pytorch(x).to(device) #Convert to pytorch format, batch is first dimension    
X_test=signal2pytorch(testing).to(device) #Convert to pytorch format, batch is first dimension

print("Clean sample: ", X_train.shape)
print("Noisy sample: ", X_test.shape)
print("test sample: ",test.shape)

print("Generate Model:")
model = Convautoenc().to(device)
print('Total number of parameters: %i' % (sum(p.numel() for p in model.parameters() if p.requires_grad)))
print("Def. loss function:")
loss_fn = nn.MSELoss()  #MSE
#loss_fn = nn.L1Loss()
    
Ypred=model(X_train).to(device)
print("Ypred shape: ",Ypred.shape)
#Ypred=Ypred.detach()
outputlen=len(Ypred[0,0,:]) #length of the signal at the output of the network.
print("outputlen=", outputlen)
    
Y=X_train[:,:,:11000]  #the target signal with same length as model output
    
print("Input X.shape=", X_train.shape )
print("Target Y.shape=", Y.shape)
print("Ypred", Ypred.shape)
print("Target Y=", Y)
#print("max(max(Y))=", max(max(max(Y))))
#print("min(min(Y))=", min(min(min(Y))))
print("Y.type()=", Y.type())

print(model)

learning_rate = 1e-4
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)#, betas=(0.9, 0.999))
"""
try:
    checkpoint = torch.load("audio_autoenc.torch",map_location='cpu')
    model.load_state_dict(checkpoint['model_state_dict'])
    #optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
except IOError:
    print("fresh start")
""";
    
#optimrandomdir_pytorch.optimizer(model, loss_fn, X, Ypred, iterations=300, startingscale=1.0, endscale=0.0)
outX_train=model(X_train)
#Ypred=Ypred.detach()
print("Ypred=", outX_train)
outX_train.to(device)
outX_train.to(device)
    
#randdir=True # True for optimization of random direction, False for pytorch optimization
randdir=False
    
if randdir==True:
#optimization of weights using method of random directions:
    optimrandomdir_pytorch.optimizer(model, loss_fn, X_train, Y, iterations=100000, startingscale=0.25, endscale=0.0)
    #--End optimization of random directions------------------------
else:
    for epoch in range(4000):
        #distortions: shift and noise:

        """
        Xlast=X_train[:,:,-1].clone() 
        X_train[:,:,1:]=X_train[:,:,:-1].clone() #round Robbin, shift 1 right
        X_train[:,:,0]=Xlast.clone()
        Ylast=Y[:,:,-1].clone() 
        Y[:,:,1:]=Y[:,:,:-1].clone() #round Robbin, shift 1 right
        Y[:,:,0]=Ylast.clone()
      
        
        
        noise = torch.randn(X_train.size())*0.05
        noise = noise.to(device)"""

        Ypred=model(X_test)
        #print("Ypred.shape=", Ypred.shape)
        #loss wants batch in the beginning! (Batch, Classes,...)
        #Ypredp=Ypred.permute(1,2,0)
        #Yp=Y.permute(1,0)
        #print("Ypredp.shape=", Ypredp.shape, "Yp.shape=", Yp.shape )
        loss=loss_fn(Ypred, Y)
        if epoch%10==0:
            print(epoch, loss.item())
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

ww = model.cpu().state_dict()
 #read obtained weights
print("ww=", ww)
#Plot obtained weights:
plt.figure(figsize=(10,6))
plt.plot(np.transpose(np.array(ww['conv1.weight'][0:1,0,:])))
plt.plot(np.transpose(np.array(ww['synconv1.weight'][0:1,0,:])))
plt.legend(('Encoder Analysis filter 0', 'Decoder Filter 0'))
plt.xlabel('Sample')
plt.ylabel('Value')
plt.title('The Encoder and Decoder Filter Coefficients')
plt.grid()

#Test on training set:
X_test =signal2pytorch(testing).to(device)
model=model.to(device)
#Xnoise=torch.cat((torch.zeros(1,1,100), Xnoise),dim=-1)
predictions=model(X_test) # Make Predictions based on the obtained weights, on training set
predictions=predictions.detach()
predictions=predictions.cpu()
predictions=np.array(predictions)
try: 
  Y=np.array(Y) 
except TypeError as TE:
  Y=np.array(Y.cpu())
#target
#print("Y=",Y)
print("predictions.shape=", predictions.shape)
#convert to numpy:
#https://discuss.pytorch.org/t/how-to-transform-variable-into-numpy/104/2
#Plot target signal and output of autoencoder:
plt.figure(figsize=(10,8))
for b in range(1):
    plt.plot(np.array(X_test[b,0,:].cpu()))
    plt.plot(np.array(Y[b,0,:]))
    plt.plot(predictions[b,0,:])
    #plt.plot(np.array(outX_train[b].detach().cpu()))
    plt.legend(('Noisy','Clean', 'Predicted'))
    plt.title('The noisy, clean and predicted Signal, Audio Fragement '+str(b+1))
    plt.xlabel('Sample')
    plt.show()

X_test=X_test.detach()
X_test = X_test.cpu()
X_test=np.array(X_test)
X_test=X_test[:,0,:]
#xnoise=np.transpose(xnoise)
#xnoise=np.clip(xnoise, -1.0,1.0)
    
xrek=predictions[:,0,:]  #remove unnecessary dimension for playback
#xrek=np.transpose(xrek)
#xrek=np.clip(xrek, -1.0,1.0)

IPython.display.Audio(X_test[0], rate = x.shape[1])

IPython.display.Audio(predictions[0], rate = x.shape[1])

IPython.display.Audio(x[0], rate = x.shape[1])

X_train.shape

outX_train.shape

predictions.shape

IPython.display.Audio(np.array(outX_train[0].detach().cpu()), rate = x.shape[1])

evaluate(np.array(Ypred.detach().cpu()),predictions)

def evaluate(clean, denoised):
    """"
    This function compares two set of signals by calculating the MSE (Mean squared error), MAE (Mean absolute error),
    and SNR (signal to noise ratio) in db averaged over all the signals.
    Receives two matrices of shape N, D. That correspond to N signals of length D.
    clean: a 2D numpy array containing the clean (original) signals.
    denoised: a 2D numpy array containing the denoised (reconstructed) versions of the original signals.
    """

    #MSE and MAE
    se = ((denoised - clean) ** 2).mean(-1)
    mse = se.mean()
    mae = np.abs(denoised - clean).mean(-1).mean()

    #SNR and PSNR
    num = (clean**2).sum(-1)
    den = ((denoised - clean) ** 2).sum(-1)
    ep = 1e-9
    SNR = 20*np.log10(np.sqrt(num)/(np.sqrt(den) + ep)).mean()

    return np.format_float_positional(mse, trim='-'), np.format_float_positional(mae, trim='-'), SNR

noisy = np.empty([test.shape[0],11000])
print(noisy.shape)
print(test.shape)

for i in range(test.shape[0]):
  noisy[i]  = signal.resample_poly(test[i], 2, 1)

print(noisy.shape)

testset =signal2pytorch(noisy).to(device) #Convert to pytorch format, batch is first dimension    
print("test sample: ",noisy.shape)
model.load_state_dict(ww)
model.eval()

#model.load_state_dict(torch.load(PATH))


ans = model(testset)

ans.shape

plt.figure(figsize=(10,8))
for b in range(10):
    plt.plot(np.array(testset[b,0,:].cpu()))
    plt.plot(ans[b,0,:].detach().cpu())
    plt.legend(('Noisy','Predicted'))
    plt.title('The Noisy and Predicted Signal of the testset, Audio Fragment '+str(b+1))
    plt.xlabel('Sample')
    plt.show()
xrek=predictions[:,0,:]

IPython.display.Audio(noisy[1], rate = x.shape[1])

IPython.display.Audio(ans.detach().cpu()[0], rate = x.shape[1])

output = np.array(ans.detach().cpu())
output = np.reshape(output, (320,11000))

output.shape

import zipfile

with open('answer.txt', 'w') as fp:
    pass

from tqdm import tqdm


with open("answer.txt", 'w+') as r:
  string = ""
  for audio in output:
    for sound in audio:
      string += str(sound) + ";"
    string += '\n'
  r.write(string)

with zipfile.ZipFile('answer.zip','w',zipfile.ZIP_DEFLATED) as myzip:
  myzip.write('answer.txt')

new = ''
for audio in output[:3]:

  for sound in audio:
    new += str(sound) + ';'
  new += '\n'

sub = []
for strin in new:
  sub.append(

from torchviz import make_dot

make_dot(model(testset), params=dict(model.named_parameters()),show_attrs=True)