"""Gleam pipeline using JSON interface

"""
import os

from workflows.processing_component_interface.processing_component_interface import component_wrapper

if __name__ == '__main__':

    files = ["test_results/test_pipeline.log",
             "test_results/test_skymodel.hdf",
             "test_results/test_empty_vislist.hdf",
             "test_results/test_perfect_vislist.hdf",
             "test_results/test_perfect_restored.fits",
             "test_results/test_perfect_deconvolved.fits",
             "test_results/test_perfect_residual.fits"
             ]
    try:
        for f in files:
            os.remove(f)
    except FileNotFoundError:
        pass
    
    processinging_steps = ["tests/workflows/test_create_vislist.json",
                           "tests/workflows/test_create_skymodel.json",
                           "tests/workflows/test_predict_vislist.json",
                           "tests/workflows/test_continuum_imaging.json"]
    
    for processing_step in processinging_steps:
        component_wrapper(processing_step)
    
    for f in files:
        assert os.path.isfile(f), "Output file %s does not exist" % f
