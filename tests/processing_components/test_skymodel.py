""" Unit tests for skymodel

"""

import logging
import unittest

import astropy.units as u
import numpy
from astropy.coordinates import SkyCoord

from data_models.memory_data_models import SkyModel
from data_models.polarisation import PolarisationFrame

from processing_components.skycomponent.operations import create_skycomponent
from processing_components.skymodel.operations import copy_skymodel
from processing_components.simulation.testing_support import create_test_image, create_named_configuration
from processing_components.visibility.base import create_blockvisibility

log = logging.getLogger(__name__)


class TestSkyModel(unittest.TestCase):
    def setUp(self):
        from data_models.parameters import arl_path
        self.lowcore = create_named_configuration('LOWBD2', rmax=300.0)
        self.dir = arl_path('test_results')
        self.times = (numpy.pi / 12.0) * numpy.linspace(-3.0, 3.0, 7)
        self.frequency = numpy.array([1e8])
        self.channel_bandwidth = numpy.array([1e6])
        self.phasecentre = SkyCoord(ra=+180.0 * u.deg, dec=-60.0 * u.deg, frame='icrs', equinox='J2000')
        self.vis = create_blockvisibility(self.lowcore, self.times, self.frequency,
                                          channel_bandwidth=self.channel_bandwidth,
                                          phasecentre=self.phasecentre, weight=1.0,
                                          polarisation_frame=PolarisationFrame('stokesI'))
        self.vis.data['vis'] *= 0.0
        
        # Create model
        self.model = create_test_image(cellsize=0.0015, phasecentre=self.vis.phasecentre,
                                       frequency=self.frequency)
        self.model.data[self.model.data > 1.0] = 1.0
    
    def test_create(self):
        fluxes = numpy.linspace(0, 1.0, 11)
        sc = [create_skycomponent(direction=self.phasecentre, flux=numpy.array([[f]]), frequency=self.frequency,
                                  polarisation_frame=PolarisationFrame('stokesI')) for f in fluxes]
        sm = SkyModel(images=[self.model], components=sc)
        assert len(sm.images) == 1
        assert len(sm.components) == 11
    
    def test_copy(self):
        fluxes = numpy.linspace(0, 1.0, 11)
        sc = [create_skycomponent(direction=self.phasecentre, flux=numpy.array([[f]]), frequency=self.frequency,
                                  polarisation_frame=PolarisationFrame('stokesI')) for f in fluxes]
        sm = SkyModel(images=[self.model], components=sc)
        sm_copy = copy_skymodel(sm)
        assert len(sm.components) == len(sm_copy.components)
        sm_fluxes = numpy.array([c.flux[0,0] for c in sm.components])
        sm_copy_fluxes = numpy.array([c.flux[0,0] for c in sm_copy.components])
        
        assert numpy.max(numpy.abs(sm_fluxes - sm_copy_fluxes)) < 1e-7
        
