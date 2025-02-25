import tensorflow as tf
from tensorflow.keras.layers import  *


def conv_bn_relu(inputs, filters, kernel_size=3, strides=1, activate=True):
    conv = tf.keras.layers.Conv2D(filters, kernel_size, strides, padding='same')(inputs)
    conv = tf.keras.layers.BatchNormalization()(conv)
    if activate:
        conv = tf.keras.layers.Activation('relu')(conv)
    return conv


def conv_block(inputs, filters, strides=1):
    conv = conv_bn_relu(inputs, filters // 4, kernel_size=1, strides=strides)
    conv = conv_bn_relu(conv, filters // 4, kernel_size=3, strides=1)
    conv = conv_bn_relu(conv, filters, kernel_size=1, strides=1, activate=False)

    short = conv_bn_relu(inputs, filters, kernel_size=1, strides=strides, activate=False)

    add = tf.add(conv, short)
    add = tf.keras.layers.Activation('relu')(add)

    return add


def identity_block(inputs, filters):
    conv = conv_bn_relu(inputs, filters // 4, kernel_size=1, strides=1)
    conv = conv_bn_relu(conv, filters // 4, kernel_size=3, strides=1)
    conv = conv_bn_relu(conv, filters, kernel_size=1, strides=1, activate=False)

    add = tf.add(conv, inputs)
    add = tf.keras.layers.Activation('relu')(add)

    return add


def basic_block(inputs, filters):
    conv = conv_bn_relu(inputs, filters, kernel_size=3, strides=1)
    conv = conv_bn_relu(conv, filters, kernel_size=3, strides=1, activate=False)

    add = tf.add(conv, inputs)
    add = tf.keras.layers.Activation('relu')(add)

    return add


def layer1(inputs):
    conv = conv_block(inputs, 256)
    conv = identity_block(conv, 256)
    conv = identity_block(conv, 256)
    conv = identity_block(conv, 256)
    return conv


def transition_layer1(x, out_channels=[32, 64]):
    x0 = conv_bn_relu(x, out_channels[0])
    x1 = conv_bn_relu(x, out_channels[1], strides=2)
    return [x0, x1]


def transition_layer2(x, out_channels=[32, 64, 128]):
    x0 = conv_bn_relu(x[0], out_channels[0])
    x1 = conv_bn_relu(x[1], out_channels[1])
    x2 = conv_bn_relu(x[1], out_channels[2], strides=2)
    return [x0, x1, x2]


def transition_layer3(x, out_channels=[32, 64, 128, 256]):
    x0 = conv_bn_relu(x[0], out_channels[0])
    x1 = conv_bn_relu(x[1], out_channels[1])
    x2 = conv_bn_relu(x[2], out_channels[2])
    x3 = conv_bn_relu(x[2], out_channels[3], strides=2)
    return [x0, x1, x2, x3]


def branch(inputs, channels):
    conv = basic_block(inputs, channels)
    conv = basic_block(conv, channels)
    conv = basic_block(conv, channels)
    conv = basic_block(conv, channels)
    return conv


def fuse_block_1(x):
    '''
    x[0]:down2  32
    x[1]:down4  64
    '''
    x1 = conv_bn_relu(x[1], 32, 1, activate=False)
    x1 = tf.keras.layers.UpSampling2D()(x1)
    x0 = tf.add(x[0], x1)

    x1 = conv_bn_relu(x[0], 64, strides=2, activate=False)
    x1 = tf.add(x1, x[1])

    return [x0, x1]


def fuse_block_2(x):
    '''
    x[0]:down2  32
    x[1]:down4  64
    x[2]:down8  128
    '''
    x11 = x[0]
    x12 = conv_bn_relu(x[1], 32, kernel_size=1, activate=False)
    x12 = tf.keras.layers.UpSampling2D(size=2)(x12)
    x13 = conv_bn_relu(x[2], 32, kernel_size=1, activate=False)
    x13 = tf.keras.layers.UpSampling2D(size=4)(x13)
    x0 = tf.keras.layers.add([x11, x12, x13])

    x21 = conv_bn_relu(x[0], 64, 3, 2, activate=False)
    x22 = x[1]
    x23 = conv_bn_relu(x[2], 64, 1, activate=False)
    x23 = tf.keras.layers.UpSampling2D(size=2)(x23)
    x1 = tf.keras.layers.add([x21, x22, x23])

    x31 = conv_bn_relu(x[0], 32, 3, 2)
    x31 = conv_bn_relu(x31, 128, 3, 2, activate=False)
    x32 = conv_bn_relu(x[1], 128, 3, 2, activate=False)
    x33 = x[2]
    x2 = tf.keras.layers.add([x31, x32, x33])

    return [x0, x1, x2]


def fuse_block_3(x):
    '''
    x[0]:down2  32
    x[1]:down4  64
    x[2]:down8  128
    x[3]:down16 256
    '''
    x0 = x[0]

    x1 = conv_bn_relu(x[1], 32, 1, activate=False)
    x1 = tf.keras.layers.UpSampling2D(size=2)(x1)

    x2 = conv_bn_relu(x[2], 32, 1, activate=False)
    x2 = tf.keras.layers.UpSampling2D(size=4)(x2)

    x3 = conv_bn_relu(x[3], 32, 1, activate=False)
    x3 = tf.keras.layers.UpSampling2D(size=8)(x3)

    out = tf.concat([x0, x1, x2, x3], axis=-1)

    return out


def HRNET(shape=(512 * 2, 512 * 2, 3 * 2), num_classes=2):
    Input = tf.keras.layers.Input(shape=shape)

    conv = conv_bn_relu(Input, 64, strides=2)
    conv = layer1(conv)

    t1 = transition_layer1(conv)

    #     x1
    b10 = branch(t1[0], 32)  # down2
    b11 = branch(t1[1], 64)  # down4
    f1 = fuse_block_1([b10, b11])
    #     x1

    t2 = transition_layer2(f1)

    #     x4
    b20 = branch(t2[0], 32)
    b21 = branch(t2[1], 64)
    b22 = branch(t2[2], 128)
    f2 = fuse_block_2([b20, b21, b22])
    #     x4  仅融合一次，此处的模块可以重复4次

    t3 = transition_layer3(f2)

    #     x3
    b30 = branch(t3[0], 32)
    b31 = branch(t3[1], 64)
    b32 = branch(t3[2], 128)
    b33 = branch(t3[3], 256)
    f3 = fuse_block_3([b30, b31, b32, b33])
    #     x3  仅融合一次，此处的模块可以重复3次

    output = tf.keras.layers.UpSampling2D(size=2)(f3)
    output = conv_bn_relu(output, 64)
    output = tf.keras.layers.Conv2D(num_classes, 1, padding='same', activation='softmax')(output)

    model = tf.keras.Model(inputs=Input, outputs=output)
    # model.summary()
    return model

