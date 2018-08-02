""" SDP pipelines as processing components.
"""

from data_models.parameters import get_parameter
from ..calibration.calibration_arlexecute import calibrate_arlexecute
from ..execution_support.arlexecute import arlexecute
from wrappers.arlexecute.imaging.imaging_arlexecute import invert_arlexecute, residual_arlexecute, \
    predict_arlexecute, zero_vislist_arlexecute, subtract_vislist_arlexecute, restore_arlexecute, \
    deconvolve_arlexecute


def ical_arlexecute(vis_list, model_imagelist, context='2d', calibration_context='TG', calibration_controls=None,
                    do_selfcal=True, **kwargs):
    """Create graph for ICAL pipeline

    :param calibration_controls:
    :param vis_list:
    :param model_imagelist:
    :param context: imaging context e.g. '2d'
    :param calibration_context: Sequence of calibration steps e.g. TGB
    :param do_selfcal: Do the selfcalibration?
    :param kwargs: Parameters for functions in components
    :return:
    """
    psf_imagelist = invert_arlexecute(vis_list, model_imagelist, dopsf=True, context=context, **kwargs)
    
    model_vislist = zero_vislist_arlexecute(vis_list)
    model_vislist = predict_arlexecute(model_vislist, model_imagelist, context=context, **kwargs)
    if do_selfcal:
        # Make the predicted visibilities, selfcalibrate against it correcting the gains, then
        # form the residual visibility, then make the residual image
        vis_list = calibrate_arlexecute(vis_list, model_vislist,
                                        calibration_context=calibration_context,
                                        calibration_controls=calibration_controls, **kwargs)
        residual_vislist = subtract_vislist_arlexecute(vis_list, model_vislist)
        residual_imagelist = invert_arlexecute(residual_vislist, model_imagelist, dopsf=True, context=context,
                                               iteration=0, **kwargs)
    else:
        # If we are not selfcalibrating it's much easier and we can avoid an unnecessary round of gather/scatter
        # for visibility partitioning such as timeslices and wstack.
        residual_imagelist = residual_arlexecute(vis_list, model_imagelist, context=context, **kwargs)
    
    deconvolve_model_imagelist, _ = deconvolve_arlexecute(residual_imagelist, psf_imagelist, model_imagelist,
                                                          prefix='cycle 0', **kwargs)
    
    nmajor = get_parameter(kwargs, "nmajor", 5)
    if nmajor > 1:
        for cycle in range(nmajor):
            if do_selfcal:
                model_vislist = zero_vislist_arlexecute(vis_list)
                model_vislist = predict_arlexecute(model_vislist, deconvolve_model_imagelist,
                                                   context=context, **kwargs)
                vis_list = calibrate_arlexecute(vis_list, model_vislist,
                                                calibration_context=calibration_context,
                                                calibration_controls=calibration_controls,
                                                iteration=cycle, **kwargs)
                residual_vislist = subtract_vislist_arlexecute(vis_list, model_vislist)
                residual_imagelist = invert_arlexecute(residual_vislist, model_imagelist, dopsf=False,
                                                       context=context, **kwargs)
            else:
                residual_imagelist = residual_arlexecute(vis_list, deconvolve_model_imagelist,
                                                         context=context, **kwargs)
            
            prefix = "cycle %d" % (cycle+1)
            deconvolve_model_imagelist, _ = deconvolve_arlexecute(residual_imagelist, psf_imagelist,
                                                                  deconvolve_model_imagelist,
                                                                  prefix=prefix,
                                                                  **kwargs)
    residual_imagelist = residual_arlexecute(vis_list, deconvolve_model_imagelist, context=context, **kwargs)
    restore_imagelist = restore_arlexecute(deconvolve_model_imagelist, psf_imagelist, residual_imagelist)
    
    return arlexecute.execute((deconvolve_model_imagelist, residual_imagelist, restore_imagelist))


def continuum_imaging_arlexecute(vis_list, model_imagelist, context='2d', **kwargs):
    """ Create graph for the continuum imaging pipeline.
    
    Same as ICAL but with no selfcal.
    
    :param vis_list:
    :param model_imagelist:
    :param context: Imaging context
    :param kwargs: Parameters for functions in components
    :return:
    """
    psf_imagelist = invert_arlexecute(vis_list, model_imagelist, dopsf=True, context=context, **kwargs)
    
    residual_imagelist = residual_arlexecute(vis_list, model_imagelist, context=context, **kwargs)
    deconvolve_model_imagelist, _ = deconvolve_arlexecute(residual_imagelist, psf_imagelist, model_imagelist,
                                                          prefix='cycle 0',
                                                          **kwargs)
    
    nmajor = get_parameter(kwargs, "nmajor", 5)
    if nmajor > 1:
        for cycle in range(nmajor):
            prefix = "cycle %d" % (cycle+1)
            residual_imagelist = residual_arlexecute(vis_list, deconvolve_model_imagelist, context=context, **kwargs)
            deconvolve_model_imagelist, _ = deconvolve_arlexecute(residual_imagelist, psf_imagelist,
                                                                  deconvolve_model_imagelist,
                                                                  prefix=prefix,
                                                                  **kwargs)
    
    residual_imagelist = residual_arlexecute(vis_list, deconvolve_model_imagelist, context=context, **kwargs)
    restore_imagelist = restore_arlexecute(deconvolve_model_imagelist, psf_imagelist, residual_imagelist)
    return arlexecute.execute((deconvolve_model_imagelist, residual_imagelist, restore_imagelist))


def spectral_line_imaging_arlexecute(vis_list, model_imagelist, continuum_model_imagelist=None, context='2d', **kwargs):
    """Create graph for spectral line imaging pipeline

    Uses the continuum imaging arlexecute pipeline after subtraction of a continuum model
    
    :param vis_list: List of visibility components
    :param model_imagelist: Spectral line model graph
    :param continuum_model_imagelist: Continuum model list
    :param context: Imaging context
    :param kwargs: Parameters for functions in components
    :return: (deconvolved model, residual, restored)
    """
    if continuum_model_imagelist is not None:
        vis_list = predict_arlexecute(vis_list, continuum_model_imagelist, context=context, **kwargs)
    
    return continuum_imaging_arlexecute(vis_list, model_imagelist, context=context, **kwargs)
