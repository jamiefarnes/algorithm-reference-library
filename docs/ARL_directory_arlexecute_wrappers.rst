.. toctree::
   :maxdepth: 2

Workflows using arlexecute
**************************

Workflows created using the ARL processing components and the arlexecute interface. These are higher level and fewer
in number than processing components.

Calibration workflows
=====================

* Calibrate workflow: :py:mod:`wrappers.arlexecute.calibration.calibration_wrappers.calibrate_arlexecute`

Model Partition Calibration workflows
=====================================

* Define model partition: :py:mod:`wrappers.arlexecute.calibration.modelpartition_wrappers.create_modelpartition_arlexecute`
* Solve model partition: :py:mod:`wrappers.arlexecute.calibration.modelpartition_wrappers.solve_modelpartition_arlexecute`

Image workflows
===============

* Generic image workflow: :py:mod:`wrappers.arlexecute.image.image_wrappers.generic_image_arlexecute`
* Generic image iteration workflow: :py:mod:`wrappers.arlexecute.image.image_wrappers.generic_image_iterator_arlexecute`

Imaging workflows
=================

* Invert: :py:mod:`wrappers.arlexecute.imaging.imaging_wrappers.invert_arlexecute`
* Predict: :py:mod:`wrappers.arlexecute.imaging.imaging_wrappers.predict_arlexecute`
* Deconvolve: :py:mod:`wrappers.arlexecute.imaging.imaging_wrappers.deconvolve_arlexecute`

Pipeline workflows
==================

* ICAL: :py:mod:`wrappers.arlexecute.pipelines.pipeline_wrappers.ical_arlexecute`
* Continuum imaging: :py:mod:`wrappers.arlexecute.pipelines.pipeline_wrappers.continuum_imaging_arlexecute`
* Spectral line imaging: :py:mod:`wrappers.arlexecute.pipelines.pipeline_wrappers.spectral_line_imaging_arlexecute`

Simulation workflows
====================

* Testing and simulation support: :py:mod:`wrappers.arlexecute.simulation.simulation_wrappers.simulate_arlexecute`

Visibility workflows
====================

* Generic visibility function: :py:mod:`wrappers.arlexecute.visibility.visibility_wrappers.generic_blockvisibility_arlexecute`

Execution
=========

* Execution framework (an interface to Dask): :py:mod:`wrappers.arlexecute.execution_support.arlexecute`
