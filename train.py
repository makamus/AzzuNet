from model import AzzuNet
import tensorflow as tf
import numpy as np
import _pickle as pkl
import gzip
import os

def get_batch(limit, size):
    idx = np.random.random_integers(limit - 1, size=(size))
    return idx

pkl_file = gzip.open('./data.pkl', 'rb')
data = pkl.load(pkl_file)

train = data["train"]
test = data["test"]

train_limit = 6500
val_limit = 7950
test_limit= 2704

train_length = train_limit
val_length = val_limit - train_limit
test_length = test_limit

p = np.random.permutation(val_limit)
words_train = np.array(train[0])
deps_train = np.array(train[1])
labels_c_train = np.array(train[2])
labels_f_train = np.array(train[3])
labels_b_train = np.array(train[4])

words_train = words_train[p]
deps_train = deps_train[p]
labels_c_train = labels_c_train[p]
labels_f_train = labels_f_train[p]
labels_b_train = labels_b_train[p]

words_val = words_train[train_limit:val_limit]
deps_val = deps_train[train_limit:val_limit]
labels_c_val = labels_c_train[train_limit:val_limit]
labels_f_val = labels_f_train[train_limit:val_limit]
labels_b_val = labels_b_train[train_limit:val_limit]

words_train = words_train[0:train_limit]
deps_train = deps_train[0:train_limit]
labels_c_train = labels_c_train[0:train_limit]
labels_f_train = labels_f_train[0:train_limit]
labels_b_train = labels_b_train[0:train_limit]

words_test = np.array(test[0])
deps_test = np.array(test[1])
labels_c_test = np.array(test[2])
labels_f_test = np.array(test[3])
labels_b_test = np.array(test[4])

#HYPERPARAMETERS:
batch_size = 32
learning_rates = [1e-1,5e-2,1e-2]
reg_rates = [1e-4,1e-5,1e-6]

max_sentence_length = 13
word_vec_length = 300
deps_vec_length = 50
steps_per_epoch = int(train_length/batch_size)+1
epochs = 50
min_loss = 666

#with tf.device('/gpu:0'):
config = tf.ConfigProto(allow_soft_placement = True)
sess = tf.Session(config = config)

saver = tf.train.Saver()

for learning_rate in learning_rates:
    for reg_rate in reg_rates: 
        print("Learning rate:",learning_rate)
        print("Reg rate:", reg_rate)
        sess = tf.Session(config = config)
        model = AzzuNet(max_sentence_length, word_vec_length, deps_vec_length)
        sess.run(tf.global_variables_initializer())
        train_writer = tf.summary.FileWriter('./logs_lr:%f,reg%f'%(learning_rate,reg_rate), sess.graph)
        val_writer = tf.summary.FileWriter('./logs_val_lr:%f,reg:%f'%(learning_rate, reg_rate), sess.graph)
        saver = tf.train.Saver()
        for i in range(epochs):
            print("Epoch",i)
            m_loss = 0 
            m_acc = 0
            for j in range(steps_per_epoch):
                idx = get_batch(train_length, batch_size)
                words = words_train[idx]
                deps = deps_train[idx]
                labels_combined = labels_c_train[idx]
                labels_forward = labels_f_train[idx]
                labels_backward = labels_b_train[idx]
                feed_dict = {model.words: words, 
                             model.deps: deps, 
                             model.lr: learning_rate, 
                             model.reg: reg_rate,
                             model.prob: 0.5,
                             model.l_c: labels_combined,
                             model.l_f: labels_forward,
                             model.l_b: labels_backward}
                
                ops = [model.acc_c, model.total_loss, model.summary, model.train_step]
                train_acc, train_loss, summary, _ = sess.run(ops, feed_dict)
                #print("Step:", j, "\tAccuracy:", train_acc, "\tLoss:", train_loss)
                m_loss += train_loss
                m_acc += train_acc
                train_writer.add_summary(summary, (i*steps_per_epoch + j))

            m_loss /= steps_per_epoch
            m_acc /= steps_per_epoch
            
            idx = get_batch(val_length, val_length)
            words = words_val[idx]
            deps = deps_val[idx]
            labels_combined = labels_c_val[idx]
            labels_forward = labels_f_val[idx]
            labels_backward = labels_b_val[idx]
            feed_dict = {model.words: words,
                         model.deps: deps,
                         model.lr: learning_rate,
                         model.reg: reg_rate,
                         model.prob: 1.0,
                         model.l_c: labels_combined,
                         model.l_f: labels_forward,
                         model.l_b: labels_backward}

            ops = [model.acc_c, model.total_loss, model.summary]
            val_acc, val_loss, summary = sess.run(ops, feed_dict)
            val_writer.add_summary(summary, i)
            print("Training accuracy:", m_acc, "\nTraining loss:", m_loss)
            print("Validation accuracy:", val_acc, "\nValidation loss:", val_loss)
  #          if val_loss < min_loss:
  #              min_loss = val_loss
  #              print("Saving model...")
  #              saver.save(sess, "./models/AzzuNet-%f" % min_loss)

 #           if i%20 == 0:
 #               print("Checkpoint...")
 #               saver.save(sess, "./models/AzzuNetCheckout-%d"%i)

        feed_dict = {model.words: words_test,
                         model.deps: deps_test,
                         model.lr: learning_rate,
                         model.reg: reg_rate,
                         model.prob: 1.0,
                         model.l_c: labels_c_test,
                         model.l_f: labels_f_test,
                         model.l_b: labels_b_test}

        ops = [model.acc_c, model.total_loss]
        test_acc, test_loss = sess.run(ops, feed_dict)
        print("Test accuracy:", val_acc, "\nTest loss:", val_loss,"\n")

#        saver.save(sess, "./models/final")