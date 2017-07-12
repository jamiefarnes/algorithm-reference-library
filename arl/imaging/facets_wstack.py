
""" The wide field imaging equation can be approximated by partitioning the image plane into small regions, treating each separately and then glueing the resulting partitions into one image. We call this image plane partitioning image plane faceting.

.. math::
    V(u,v,w) = \\sum_{i,j} \\frac{1}{\\sqrt{1- l_{i,j}^2- m_{i,j}^2}} e^{-2 \\pi j (ul_{i,j}+um_{i,j} + w(\\sqrt{
    1-l_{i,j}^2-m_{i,j}^2}-1))} \\int  I(\\Delta l, \\Delta m) e^{-2 \\pi j (u\\Delta l_{i,j}+u \\Delta m_{i,j})} dl dm

"""


from arl.imaging.wstack import predict_wstack, invert_wstack

from arl.image.iterators import raster_iter
from arl.imaging.iterated import *

log = logging.getLogger(__name__)

def predict_facets_wstack(vis: Visibility, model: Image, predict_function=predict_wstack, **kwargs)  -> Visibility:
    """ Predict using image facets, calling specified predict function

    :param vis: Visibility to be predicted
    :param model: model image
    :param predict_function: Function to be used for prediction (allows nesting) (default predict_2d)
    :returns: resulting visibility (in place works)
    """
    log.info("predict_facets_wstack: Predicting by image facets and w stacking")
    return predict_with_image_iterator(vis, model, image_iterator=raster_iter, predict_function=predict_function,
                                **kwargs)

def invert_facets_wstack(vis: Visibility, im: Image, dopsf=False, normalize=True, invert_function=invert_wstack,
                         **kwargs)  -> (Image, numpy.ndarray):
    """ Invert using image partitions, calling specified Invert function

    :param vis: Visibility to be inverted
    :param im: image template (not changed)
    :param dopsf: Make the psf instead of the dirty image
    :param normalize: Normalize by the sum of weights (True)
    :param invert_function: Function to be used for inverting (allows nesting) (default invert_2d)
    :returns: resulting image[nchan, npol, ny, nx], sum of weights[nchan, npol]
    """
    
    log.info("invert_facets_wstack: Inverting by image facets and w stacking")
    return invert_with_image_iterator(vis, im, normalize=normalize, image_iterator=raster_iter, dopsf=dopsf,
                                      invert_function=invert_function, **kwargs)