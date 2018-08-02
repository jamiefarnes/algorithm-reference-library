"""

"""

from ..execution_support.arlexecute import arlexecute

from processing_components.calibration.calibration_control import calibrate_function, create_calibration_controls
from processing_components.calibration.operations import apply_gaintable
from processing_components.visibility.gather_scatter import visibility_gather_channel
from processing_components.visibility.operations import divide_visibility, integrate_visibility_by_channel


def calibrate_arlexecute(vis_list, model_vislist, calibration_context='TG',
                         calibration_controls=None, global_solution=True, **kwargs):
    """ Create a set of components for (optionally global) calibration of a list of visibilities

    If global solution is true then visibilities are gathered to a single visibility data set which is then
    self-calibrated. The resulting gaintable is then effectively scattered out for application to each visibility
    set. If global solution is false then the solutions are performed locally.

    :param vis_list:
    :param model_vislist:
    :param calibration_context: String giving terms to be calibrated e.g. 'TGB'
    :param calibration_controls: dictionary giving calibration information
    :param global_solution: Solve for global gains
    :param kwargs: Parameters for functions in components
    :return:
    """
    
    if calibration_controls is None:
        calibration_controls =create_calibration_controls()
        
    def solve_and_apply(vis, modelvis=None):
        return calibrate_function(vis, modelvis, calibration_context=calibration_context,
                                  calibration_controls=calibration_controls, **kwargs)[0]
    
    if global_solution:
        point_vislist = [arlexecute.execute(divide_visibility, nout=len(vis_list))(vis_list[i],
                                                                                   model_vislist[i])
                         for i, _ in enumerate(vis_list)]
        global_point_vis_list = arlexecute.execute(visibility_gather_channel, nout=1)(point_vislist)
        global_point_vis_list = arlexecute.execute(integrate_visibility_by_channel, nout=1)(global_point_vis_list)
        # This is a global solution so we only compute one gain table
        _, gt_list = arlexecute.execute(solve_and_apply, pure=True, nout=2)(global_point_vis_list,
                                                                            calibration_controls=calibration_controls,
                                                                            **kwargs)
        return [arlexecute.execute(apply_gaintable, nout=len(vis_list))(v, gt_list, inverse=True)
                for v in vis_list]
    else:
        
        return [arlexecute.execute(solve_and_apply, nout=len(vis_list))(vis_list[i], model_vislist[i])
                for i, v in enumerate(vis_list)]
