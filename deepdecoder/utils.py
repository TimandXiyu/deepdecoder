# Copyright 2015 Leon Sixt

#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os

from beesgrid import MASK
import theano
import h5py
import numpy as np
import theano.tensor as T
from diktya.numpy.utils import tile

floatX = theano.config.floatX


def binary_mask(mask, black=0., ignore=0.5,  white=1.):
    bw = ignore * T.ones_like(mask, dtype=floatX)
    bw = T.set_subtensor(bw[(mask > MASK["IGNORE"]).nonzero()], white)
    bw = T.set_subtensor(bw[(mask < MASK["BACKGROUND_RING"]).nonzero()], black)
    return bw


def adaptive_mask(mask, black=0., ignore=0.5, white=1.):
    bw = ignore * T.ones_like(mask, dtype=floatX)
    t_black = black*T.ones_like(bw, dtype=floatX)
    t_white = white*T.ones_like(bw, dtype=floatX)
    white_idx = (mask > MASK["IGNORE"]).nonzero()
    black_idx = (mask < MASK["BACKGROUND_RING"]).nonzero()
    bw = T.set_subtensor(bw[white_idx], t_white[white_idx])
    bw = T.set_subtensor(bw[black_idx], t_black[black_idx])
    return bw


def tags_from_hdf5(fname):
    tags_list = []
    with open(fname) as pathfile:
        for hdf5_name in pathfile.readlines():
            hdf5_fname = os.path.dirname(fname) + "/" + hdf5_name.rstrip('\n')
            f = h5py.File(hdf5_fname)
            data = np.asarray(f["data"], dtype=np.float32)
            labels = np.asarray(f["labels"], dtype=np.float32)
            tags = data[labels == 1]
            tags /= 255.
            tags_list.append(tags)

    return np.concatenate(tags_list)


def loadRealData(fname):
    X = tags_from_hdf5(fname)
    X = X[:(len(X)//64)*64]
    return X


def visualise_tiles(images):
    import warnings
    import beras.visualise
    warnings.warn(
        "Call to deprecated function deepdecoder.utils.visualise_tiles."
        " Use beras.visualise.visualise_tiles", category=DeprecationWarning)
    return beras.visualise.visualise_tiles(images)


def rotate_by_multiple_of_90(img, rots):
    def idx(pos):
        return T.eq(rots, pos).nonzero()
    rots = rots.reshape((-1, ))
    img = T.set_subtensor(img[idx(0)], img[idx(0)][:, :, :, :])
    img = T.set_subtensor(img[idx(1)],
                          img[idx(1)].swapaxes(2, 3)[:, :, ::-1, :])
    img = T.set_subtensor(img[idx(2)], img[idx(2)][:, :, ::-1, ::-1])
    img = T.set_subtensor(img[idx(3)],
                          img[idx(3)].swapaxes(2, 3)[:, :, :, ::-1])
    return img


def zip_visualise_tiles(*arrs, show=True):
    import matplotlib.pyplot as plt
    assert len(arrs) >= 2
    length = len(arrs[0])
    for a in arrs:
        assert len(a) == length, "all input arrays must have the same size"
    tiles = []
    for i in range(length):
        for a in arrs:
            tiles.append(a[i])

    tiled = tile(tiles, columns_must_be_multiple_of=len(arrs))
    assert len(tiled) == 1, "currently only grayscale image are supported"
    plt.imshow(tiled[0], cmap='gray')
    if show:
        plt.show()
