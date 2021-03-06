import os
# makes OS dependent functionality accessible in a python code
import sys
# system specific parameters, provides access to some variables used or maintained
# by the interpreter, and to functions that interact storngly with the interpreter
import time
# time acccess and conversions
from numpy import *
import gzip
# support for gzip files
import theano
# a Python library that allows you to define, optimize, and evaluate 
# mathematical expressions involving multi-dimensional arrays efficiently
import theano.tensor as T
# types and operations for sybolic numpy
from theano.tensor.shared_randomstreams import RandomStreams
# friednly random numbers
import cPickle
# Python object serializtion -- a faster way compared to pickle
from utils import tile_raster_images
# see tile_raster_images in utils.py file
from logistic_sgd import load_data
# see logistic_sgd.py file
from PIL import Image
# Python Imaging Library
import random
# generate pseudo random numbers
import itertools
# functions creating iterators for efficient looping
import matplotlib.pyplot as plt
# for plotting figures
import scipy.io
# for loading MATLAB files

'''
def random_combination(iterable, r):
	"Random selection from itertools.combinations(iterable, r)"
	pool = tuple(iterable)
	n = len(pool)
	indices = sorted(random.sample(xrange(n), r))
	return tuple(pool[i] for i in indices)  
'''

# think it's another option to load data, apart from
# the load_data in the logistic_sgd.py file
def load__data(dataset):
	data_dir, data_file = os.path.split(dataset)
	if data_dir == "" and not os.path.isfile(dataset):
		# Check if dataset is in the data directory.
		new_path = os.path.join(os.path.split(__file__)[0],
			"..",
			"data",
			dataset)

		if os.path.isfile(new_path) or data_file == 'mnist.pkl.gz':
			dataset = new_path

	print 'Loading data ...'

	# Load the dataset
	print dataset
	f = gzip.open(dataset, 'rb')
	train_set, valid_set, test_set = cPickle.load(f)
	f.close()
	
	# train_set, valid_set, test_set format: tuple(input, target)
	# input is an numpy.ndarray of 2 dimensions (a matrix)
	# which row's correspond to an example. target is a
	# numpy.ndarray of 1 dimensions (vector)) that have the same length as
	# the number of rows in the input. It should give the target

class multiViewAutoEncoder(object):
	def __init__(self,
			numpy_rng=None,
			theano_rng=None,
			input=None,
			n_visible=784,
			n_hidden=500,
			W1=None,
			W2=None,
			b1hid=None,
			b2hid=None,
			b1vis=None,
			b2vis=None,
			batch_size=20,
			lamda=1,
			perMatW1=None,
			perMatW2=None):
	
		self.n_visible = n_visible
		self.n_hidden = n_hidden
		if not numpy_rng:
			numpy_rng = numpy.random.RandomState(123)

		if not theano_rng:
			theano_rng = RandomStreams(numpy_rng.randint(2**30))

		if not W1:
			initial_W1 = numpy.asarray(numpy_rng.uniform(
				low=-4*numpy.sqrt(6./ (n_hidden+n_visible)),
				high=4*numpy.sqrt(6./(n_hidden+n_visible)),
				size=(n_visible,n_hidden)),
				dtype=theano.config.floatX)
			W1 = theano.shared(value=initial_W1, name='W1', borrow=True)
		
		if not W2:
			'''initial_W2=numpy.asarray(
					numpy_rng.uniform(
						low=-4*numpy.sqrt(6./ (n_hidden+n_visible)),
						high=4*numpy.sqrt(6./(n_hidden+n_visible)),
						size=(n_visible,n_hidden)),
					dtype=theano.config.floatX
				)'''

			initial_W2 = W1.get_value()
			W2 = theano.shared(value=initial_W2,name='W2',borrow=True)

		if not b1vis:
			b1vis = theano.shared(
				value=numpy.zeros(
					n_visible,
					dtype=theano.config.floatX
					),
				borrow=True
				)

		if not b2vis:
			b2vis= theano.shared(
				value=numpy.zeros(
					n_visible,
					dtype=theano.config.floatX
					),
				borrow=True
				)

		if not b1hid:
			b1hid = theano.shared(
				value=numpy.zeros(
						n_hidden,
						dtype=theano.config.floatX
						),
					name='b1',
					borrow=True
					)

		if not b2hid:
			b2hid = theano.shared(value=numpy.zeros(
							n_hidden,
							dtype=theano.config.floatX
						),
					name='b2',
					borrow=True
					)
		
		if not perMatW1:        
			perMatW1 = theano.shared(numpy.zeros((n_hidden, 10*n_hidden)))

		if not perMatW2:
			perMatW2 = theano.shared(numpy.zeros((n_hidden, 10*n_hidden)))

		self.W1 = W1
		self.W2 = W2

		self.b1 = b1hid
		self.b2 = b2hid

		self.b1_prime = b1vis
		self.b2_prime = b2vis

		self.theano_rng = theano_rng

		self.W1_prime=self.W1.T
		self.W2_prime=self.W2.T

		self.lamda=lamda
			
		self.permMatW1=perMatW1
		self.permMatW2=perMatW2
			
		self.flag=False
		self.Firstflag=True

		self.batch_size=batch_size
	
		if input is None:   
			self.x=T.dmatrix(name='input')
		else:
			self.x=input
			self.params=[self.W1, self.b1, self.b1_prime, self.W2, self.b2, self.b2_prime]
	
	def get_reconstructed_input1(self, hidden):
		return T.nnet.sigmoid(T.dot(hidden, self.W1_prime) + self.b1_prime)

	def get_reconstructed_input2(self, hidden):
		return T.nnet.sigmoid(T.dot(hidden, self.W2_prime) + self.b2_prime)

	def get_hidden_values1(self, input):
		return T.nnet.sigmoid(T.dot(input, self.W1) + self.b1)

	def get_hidden_values2(self, input):
		return T.nnet.sigmoid(T.dot(input, self.W2) + self.b2)
			
	def get_perm_hidden_values1(self, input):
		permW1 = T.dot(self.W1,self.permMatW1)
		return T.nnet.sigmoid(T.dot(input, permW1))

	def get_perm_hidden_values2(self, input):
		permW2 = T.dot(self.W2,self.permMatW2)
		return T.nnet.sigmoid(T.dot(input, permW2))
	
	def save_matrices(self, n):
		numpy.save("resultsb1_" + str(n), self.b1.get_value(borrow=True))
		numpy.save("resultsb1p_" + str(n), self.b1_prime.get_value(borrow=True))
		numpy.save("resultsw1_" + str(n), self.W1.get_value(borrow=True))
		numpy.save("resultsb2_" + str(n), self.b2.get_value(borrow=True))
		numpy.save("resultsb2p_" + str(n), self.b2_prime.get_value(borrow=True))
		numpy.save("resultsw2_" + str(n), self.W2.get_value(borrow=True))
	
	def get_cost_updates(self,learning_rate):
		y1 = self.get_hidden_values1(self.x)
		z1 = self.get_reconstructed_input1(y1)
		
		y2 = self.get_hidden_values2(self.x)
		z2 = self.get_reconstructed_input2(y2)

		random_pick_hidden_activation1=self.get_perm_hidden_values1(self.x)     
		random_pick_hidden_activation2=self.get_perm_hidden_values2(self.x)

		L1 =- T.sum(self.x*T.log(z1) + (1-self.x)*T.log(1-z1), axis=1)
		L2 =- T.sum(self.x*T.log(z2) + (1-self.x)*T.log(1-z2), axis=1)

		'''
		comb=itertools.combinations_with_replacement(range(self.n_hidden),2)     
		rand_comb=random_combination(comb,self.n_hidden)
		#correlation=list()
		
		random_pick_hidden_activation1=theano.shared(numpy.zeros((self.batch_size,self.n_hidden),dtype=theano.config.floatX))
		random_pick_hidden_activation2=theano.shared(numpy.zeros((self.batch_size,self.n_hidden),dtype=theano.config.floatX))
				j=0

		for  i in rand_comb:
			random_pick_hidden_activation1=T.set_subtensor(random_pick_hidden_activation1[:,j],(y1[:,i[0]]))    
			random_pick_hidden_activation2=T.set_subtensor(random_pick_hidden_activation2[:,j],(y2[:,i[1]]))    
			j=j+1
		'''

		random_pick_hidden_activation1 = random_pick_hidden_activation1 - \
			numpy.ones((self.batch_size,10*self.n_hidden))*T.mean(random_pick_hidden_activation1,axis=0)      
		random_pick_hidden_activation2 = random_pick_hidden_activation2 - \
			numpy.ones((self.batch_size,10*self.n_hidden))*T.mean(random_pick_hidden_activation2,axis=0)

		correlation = T.sum(random_pick_hidden_activation1*random_pick_hidden_activation2, axis=0)+0.00001
		sigma_random_hidden_activation1 = T.sum(random_pick_hidden_activation1*random_pick_hidden_activation1,
			axis=0)+0.00001
		sigma_random_hidden_activation2 = T.sum(random_pick_hidden_activation2*random_pick_hidden_activation2,
			axis=0)+0.00001
		correlation = (correlation/T.sqrt(sigma_random_hidden_activation1*sigma_random_hidden_activation2))**2
		tot_correlation = T.sum(correlation)

	
		'''
		for i in range(self.n_hidden):
			y1[:,i]=y1[:,i]-numpy.ones(self.batch_size)*(T.sum(y1[:,i])/self.batch_size)    
			y2[:,i]=y2[:,i]-numpy.ones(self.batch_size)*(T.sum(y2[:,i])/self.batch_size)
			
			y1=y1-numpy.ones(self.batch_size)*((T.sum(y1,axis=0))/self.batch_size)
			y2=y2-numpy.ones(self.batch_size)*((T.sum(y2,axis=0))/self.batch_size)
			corr=T.sum(y1*y2,axis=0)/T.sqrt(T.sum(y1*y1,axis=0)*T.sum(y2*y2,axis=0))
		'''
		
		'''
		getL1Cost=theano.function([self.x],[T.mean(L1)])
		getTotCorr=theano.function([self.x],[tot_correlation])
		if(self.Firstflag==True):
				self.Firstflag=False
			self.lamda=getL1Cost(self.x)/getTotCorr(self.x)
		elif(self.flag==True):
			self.Firstflag=True
			self.flag=False
		'''

		L = L1 + L2 + (self.lamda*tot_correlation)
		cost=T.mean(L)
		gradients = T.grad(cost,self.params)
		updates = []
		for param, gparam in zip(self.params,gradients):
			updates.append((param, param - learning_rate*gparam))
		return (cost, updates, T.mean(L1), T.mean(L2), self.lamda*tot_correlation)


def get_permat(m,n):
	mat = numpy.zeros((m,n))
	
	for i in range(n):
		mat[random.uniform(0, m), i] = 1
	
	return mat

##################################################################        
def testMultiviewAutoEncodersWebkb(learning_rate=.1,
		batch_size=20,
		training_epochs=100,
		dataset='mnist.pkl.gz',
		output_folder='webKbMultiviewSplit'):

	datasets1 = scipy.io.loadmat('webkb_view1.mat')
	datasets2 = scipy.io.loadmat('webkb_view2.mat')
	datamat1 = datasets1['webkbBBOW'].astype(float)
	datamat2 = datasets2['webkbBBOW'].astype(float)
	datamat = numpy.hstack((datamat1[:, 0:-1],datamat2[:, 0:-1]))
	train_set_x = theano.shared(datamat)

	n_train_batches = train_set_x.get_value().shape[0]/batch_size
	n_features = train_set_x.get_value().shape[1]

	index = T.lscalar()
	perMat1 = T.matrix()
	perMat2 = T.matrix()

	x = T.matrix('x')

	if not os.path.isdir(output_folder):
		os.makedirs(output_folder)

	os.chdir(output_folder)

	multiViewAE=multiViewAutoEncoder(numpy_rng=None,theano_rng=None,input=x,n_visible=n_features,n_hidden=n_features/10)

	multiViewAE.save_matrices(0)
	print 'Multiview Auto Encoder object initialized...'
	cost, updates, L1, L2, corr = multiViewAE.get_cost_updates(learning_rate=0.1)
	print 'Cost updates calculated'
	train_MVAE = theano.function([index],
		[cost,L1,L2,corr],
		updates=updates,
		givens={x:train_set_x[index*batch_size:(index+1)*batch_size]},
		on_unused_input='warn')
	print 'Train function defined'
	start_time = time.clock()
	epoch_wise_cost = list()
	epoch_wise_L1 = list()
	epoch_wise_L2 = list()
	epoch_wise_corr = list()
	for epoch in range(training_epochs):
		c = list()
		reconError1 = list()
		reconError2 = list()
		corr = list()
		print 'Epoch %d started' % epoch
		for batch_index in range(n_train_batches):
			if(batch_index%10 == 0 and batch_index != 0):
				print("finished training %dbatches,cost so far= %f")%(batch_index,mean(c))
				print "total error:%f "%itr_cost
				print "reconstruction error:%f "%L1
				print "reconstruction error:%f "%L2
				print itr_cost-(L1+L2)
			
			perMat1=get_permat(multiViewAE.n_hidden, 10*multiViewAE.n_hidden)
			perMat2=get_permat(multiViewAE.n_hidden, 10*multiViewAE.n_hidden)
			multiViewAE.permMatW1.set_value(perMat1)
			multiViewAE.permMatW2.set_value(perMat2)
			itr_cost, L1, L2, corre = train_MVAE(batch_index)
			c.append(itr_cost)
			reconError1.append(L1)
			reconError2.append(L2)
			corr.append(corre)
			#print "iteration cost%f"%itr_cost
			#print "iteration %d, cost %f, correlation "%(batch_index,itr_cost)
		
		multiViewAE.save_matrices(epoch)
		print ('Training epoch %d , cost %d')%(epoch, numpy.mean(c))
		epoch_wise_cost.append(mean(c))
		epoch_wise_L1.append(mean(reconError1))
		epoch_wise_L2.append(mean(reconError2))
		epoch_wise_corr.append(mean(corr))
	
	plt.plot(epoch_wise_cost, label="totalError")
	plt.plot(epoch_wise_L1, label="ReconstructionError1")
	plt.plot(epoch_wise_L2, label="ReconstructionError2")
	# corr=[a-(b+c) for a,b,c in zip(epoch_wise_cost,L1,L2)]
	plt.plot(epoch_wise_corr, label="Correlation")
	plt.ylabel('cost') 
	plt.xlabel('epoch')
	plt.legend(bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure)
	plt.show()
	
	end_time = time.clock()
	training_time = (end_time - start_time)

	print >> sys.stderr, ('The no training time for file ' +
						  os.path.split(__file__)[1] +
						  ' ran for %.2fm' % ((training_time) / 60.))
	image = Image.fromarray(
		tile_raster_images(X=multiViewAE.W1.get_value(borrow=True).T,
						   img_shape=(28, 28), 
						   tile_shape=(10, 10),
						   tile_spacing=(1, 1)))
	image.save('filters_view1.png')

	image = Image.fromarray(
		tile_raster_images(X=multiViewAE.W2.get_value(borrow=True).T,
						   img_shape=(28, 28), 
						   tile_shape=(10, 10),
						   tile_spacing=(1, 1)))
	image.save('filters_view2.png')

############################################################

def testMultiviewAutoEncoders(learning_rate=.1,
		batch_size=20,
		training_epochs=10,
		dataset='mnist.pkl.gz',
		output_folder='MVAE_plots'):
		
	dataset = load_data(dataset)
	train_set_x = theano.shared(numpy.asarray(numpy.zeros((100,728)),
		dtype=theano.config.floatX),
		borrow=True)

	train_set_x, train_set_y = dataset[0]

	n_train_batches = train_set_x.get_value().shape[0]/batch_size

	index = T.lscalar()
	perMat1 = T.matrix()
	perMat2 = T.matrix()

	x = T.matrix('x')

	if not os.path.isdir(output_folder):
		os.makedirs(output_folder)

	os.chdir(output_folder)
  
	multiViewAE = multiViewAutoEncoder(numpy_rng=None,
		theano_rng=None,
		input=x,
		n_visible=28*28,
		n_hidden=400)
	multiViewAE.save_matrices(0)
	print "Multiview auto encoder object initialized"
	cost, updates, L1, L2, corr = multiViewAE.get_cost_updates(learning_rate=0.1)
	print "Cost updates calculated"
	train_MVAE=theano.function([index],[cost, L1, L2, corr],
		updates=updates,
		givens={x:train_set_x[index*batch_size:(index+1)*batch_size]},
		on_unused_input='warn')
	print "Train function defined"
	start_time = time.clock()
	epoch_wise_cost = list()
	epoch_wise_L1 = list()
	epoch_wise_L2 = list()
	epoch_wise_corr = list()
	for epoch in range(training_epochs):
		c = list()
		reconError1 = list()
		reconError2 = list()
		corr = list()
		print 'Epoch %d started' % epoch
		for batch_index in range(n_train_batches):
			if( batch_index%500==0 and batch_index!=0):            
				print "Finished training %d batches, cost so far = %f" % (batch_index, mean(c))
				print "Total error:%f " % itr_cost
				print "Reconstruction error : %f" % L1
				print "Reconstruction error:%f" % L2
				print itr_cost-(L1+L2)
			perMat1=get_permat(multiViewAE.n_hidden,10*multiViewAE.n_hidden)
			perMat2=get_permat(multiViewAE.n_hidden,10*multiViewAE.n_hidden)
			multiViewAE.permMatW1.set_value(perMat1)
			multiViewAE.permMatW2.set_value(perMat2)
			itr_cost,L1,L2,corre=train_MVAE(batch_index)
			c.append(itr_cost)
			reconError1.append(L1)
			reconError2.append(L2)
			corr.append(corre)
			#print "iteration cost%f"%itr_cost
			#print "iteration %d, cost %f, correlation "%(batch_index,itr_cost)
		
		multiViewAE.save_matrices(epoch)
		
		print ('Training epoch %d , cost %d')%(epoch,numpy.mean(c))
		epoch_wise_cost.append(mean(c))
		epoch_wise_L1.append(mean(reconError1))
		epoch_wise_L2.append(mean(reconError2))
		epoch_wise_corr.append(mean(corr))

	plt.plot(epoch_wise_cost, label="totalError")
	plt.plot(epoch_wise_L1, label="ReconstructionError1")
	plt.plot(epoch_wise_L2, label="ReconstructionError2")
	# corr=[a-(b+c) for a,b,c in zip(epoch_wise_cost,L1,L2)]
	plt.plot(epoch_wise_corr, label="Correlation")
	plt.ylabel('cost') 
	plt.xlabel('epoch')
	plt.legend(bbox_to_anchor=(1, 1),bbox_transform=plt.gcf().transFigure)
	plt.show()

	end_time=time.clock()
	training_time=(end_time-start_time)

	print >> sys.stderr, ('The no training time for file ' +
						  os.path.split(__file__)[1] +
						  ' ran for %.2fm' % ((training_time) / 60.))
	image = Image.fromarray(tile_raster_images(X=multiViewAE.W1.get_value(borrow=True).T,
		img_shape=(28, 28), 
		tile_shape=(10, 10),
		tile_spacing=(1, 1)))
	
	image.save('filters_view1.png')

	image = Image.fromarray(tile_raster_images(X=multiViewAE.W2.get_value(borrow=True).T,
		img_shape=(28, 28), 
		tile_shape=(10, 10),
		tile_spacing=(1, 1)))
	
	image.save('filters_view2.png')

if __name__=='__main__':
	testMultiviewAutoEncodersWebkb()