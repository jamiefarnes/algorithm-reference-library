""" Wrappers around ARL processing components, using JSON for configuration.

These can be executed using processing_arlexecute_interface.py.

"""

import numpy

from data_models.buffer_data_models import BufferBlockVisibility
from workflows.processing_component_interface.arl_json.json_helpers import json_to_linspace, json_to_skycoord
from wrappers.arlexecute.execution_support.arlexecute import arlexecute
from wrappers.arlexecute.simulation.simulation_arlexecute import simulate_arlexecute


def create_vislist_serial_wrapper(conf):
    """ Create an empty vislist
    
    :param conf: Configuration from JSON file
    :return:
    """
    configuration = conf['create_vislist']['configuration']
    rmax = conf['create_vislist']['rmax']
    phasecentre = json_to_skycoord(conf['create_vislist']['phasecentre'])
    frequency = json_to_linspace(conf['create_vislist']['frequency'])
    if conf['create_vislist']['frequency']['steps'] > 1:
        channel_bandwidth = numpy.array(conf['create_vislist']['frequency']['steps'] * [frequency[1] - frequency[0]])
    else:
        channel_bandwidth = numpy.array(conf['create_vislist']['frequency']['start'])
    
    times = json_to_linspace(conf['create_vislist']['times'])
    
    vis_list = simulate_arlexecute(configuration,
                                   rmax=rmax,
                                   frequency=frequency,
                                   channel_bandwidth=channel_bandwidth,
                                   times=times,
                                   phasecentre=phasecentre,
                                   order='frequency')
    
    def output_vislist(v):
        bdm = BufferBlockVisibility(conf["buffer"], conf["outputs"]["vis_list"], v)
        bdm.sync()
    
    return arlexecute.execute(output_vislist)(vis_list)
