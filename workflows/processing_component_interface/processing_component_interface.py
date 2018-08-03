""" This is the processing wrapper interface into the ARL, allowing accessing to wrapped components.

"""

import logging

from wrappers.arlexecute.execution_support.arlexecute import arlexecute
from workflows.processing_component_interface.execution_helper import initialise_config_wrapper
from wrappers.arlexecute.processing_component_wrappers import setup_execution_wrapper_arlexecute, \
    teardown_execution_wrapper_arlexecute
from wrappers.serial.processing_component_wrappers import setup_execution_wrapper_serial, \
    teardown_execution_wrapper_serial



# Add new wrapped components here. These are accessed using globals()

from wrappers.arlexecute.processing_component_wrappers import create_vislist_arlexecute_wrapper, \
    create_skymodel_arlexecute_wrapper, predict_vislist_arlexecute_wrapper, continuum_imaging_arlexecute_wrapper, \
    corrupt_vislist_arlexecute_wrapper
from wrappers.serial.processing_component_wrappers import create_vislist_serial_wrapper


def component_wrapper(config):
    """Run an ARL component as described in a JSON dict or file
    
    :param config: JSON dict or file
    :return:
    """
    if isinstance(config, str):
        print('component_wrapper: read configuration from %s' % config)
        config = initialise_config_wrapper(config)

    elif isinstance(config, dict):
        print('component_wrapper: read configuration from dictionary')
    else:
        raise ValueError("config must be either a string of a JSON file or a dictionary")
    
    
    log = logging.getLogger()
    
    ef = config["component"]["execution_framework"]
    
    arl_component = config["component"]["name"]
    
    wrapper = arl_component + "_" + ef + "_wrapper"
    assert wrapper in globals().keys(), 'ARL component %s is not wrapped' % arl_component
    
    log.info('component_wrapper: executing %s component %s' % (ef, arl_component))
    print('component_wrapper: executing %s component %s' % (ef, arl_component))
    
    if ef == "arlexecute":
        # Initialise execution framework and set up the logging
        setup_execution_wrapper_arlexecute(config)
        result = globals()[wrapper](config)
        arlexecute.compute(result, sync=True)
        arlexecute.close()
        teardown_execution_wrapper_arlexecute(config)
    elif ef == "serial":
        setup_execution_wrapper_serial(config)
        globals()[wrapper](config)
        teardown_execution_wrapper_serial(config)
    else:
        raise NotImplemented("Execution framework %s is not supported" % ef)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Execute ARL componentst')
    parser.add_argument('--config', type=str, help='JSON configuration file')

    # Get the configuration definition, checking for validity
    config_file = parser.parse_args().config
    
    component_wrapper(config_file)
    
    
