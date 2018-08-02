""" Radio interferometric calibration using an expectation maximisation algorithm

See the SDP document "Model Partition Calibration View Packet"

In this code:

- A single model parition is taken to be a list composed of (skymodel, gaintable) tuples.

- The E step for a specific model partition is the sum of the partition data model and the discrepancy between the
    observed data and the summed (over all partitions) data models.


- The M step for a specific partition is the optimisation of the model partition given the model partition. This
    involves fitting a skycomponent and fitting for the gain phases.

"""

import logging

from data_models.memory_data_models import BlockVisibility
from processing_components.calibration.operations import copy_gaintable, create_gaintable_from_blockvisibility
from processing_components.skymodel.operations import copy_skymodel

log = logging.getLogger(__name__)


def create_modelpartition(vis: BlockVisibility, skymodels, **kwargs):
    """Create a set of associations between skymodel and gaintable

    :param vis: BlockVisibility to process
    :param skymodels: List of skyModels
    :param kwargs:
    :return:
    """
    gt = create_gaintable_from_blockvisibility(vis, **kwargs)
    return [(copy_skymodel(sm), copy_gaintable(gt)) for sm in skymodels]

