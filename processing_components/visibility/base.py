"""
Base simple visibility operations, placed here to avoid circular dependencies
"""

import copy
import logging
from typing import Union

import numpy
from astropy import constants as constants
from astropy import units as u
from astropy.coordinates import SkyCoord

from data_models.memory_data_models import Visibility, BlockVisibility, Configuration
from data_models.polarisation import PolarisationFrame, ReceptorFrame, correlate_polarisation
from libs.util.coordinate_support import xyz_to_uvw, uvw_to_xyz, skycoord_to_lmn, simulate_point

log = logging.getLogger(__name__)


def vis_summary(vis: Union[Visibility, BlockVisibility]):
    """Return string summarizing the Visibility

    """
    return "%d rows, %.3f GB" % (vis.nvis, vis.size())


def copy_visibility(vis: Union[Visibility, BlockVisibility], zero=False) -> Union[Visibility, BlockVisibility]:
    """Copy a visibility

    Performs a deepcopy of the data array
    """
    assert isinstance(vis, Visibility) or isinstance(vis, BlockVisibility), vis
    
    newvis = copy.copy(vis)
    newvis.data = numpy.copy(vis.data)
    if isinstance(vis, Visibility):
        newvis.cindex = vis.cindex
        newvis.blockvis = vis.blockvis
    if zero:
        newvis.data['vis'][...] = 0.0
    return newvis


def create_visibility(config: Configuration, times: numpy.array, frequency: numpy.array,
                      channel_bandwidth, phasecentre: SkyCoord,
                      weight: float, polarisation_frame=PolarisationFrame('stokesI'),
                      integration_time=1.0,
                      zerow=False) -> Visibility:
    """ Create a Visibility from Configuration, hour angles, and direction of source

    Note that we keep track of the integration time for BDA purposes

    :param config: Configuration of antennas
    :param times: hour angles in radians
    :param frequency: frequencies (Hz] [nchan]
    :param weight: weight of a single sample
    :param phasecentre: phasecentre of observation
    :param channel_bandwidth: channel bandwidths: (Hz] [nchan]
    :param integration_time: Integration time ('auto' or value in s)
    :param polarisation_frame: PolarisationFrame('stokesI')
    :return: Visibility
    """
    assert phasecentre is not None, "Must specify phase centre"
    
    if polarisation_frame is None:
        polarisation_frame = correlate_polarisation(config.receptor_frame)
    
    nch = len(frequency)
    ants_xyz = config.data['xyz']
    nants = len(config.data['names'])
    nbaselines = int(nants * (nants - 1) / 2)
    ntimes = len(times)
    npol = polarisation_frame.npol
    nrows = nbaselines * ntimes * nch
    nrowsperintegration = nbaselines * nch
    row = 0
    rvis = numpy.zeros([nrows, npol], dtype='complex')
    rweight = weight * numpy.ones([nrows, npol])
    rtimes = numpy.zeros([nrows])
    rfrequency = numpy.zeros([nrows])
    rchannel_bandwidth = numpy.zeros([nrows])
    rantenna1 = numpy.zeros([nrows], dtype='int')
    rantenna2 = numpy.zeros([nrows], dtype='int')
    ruvw = numpy.zeros([nrows, 3])
    
    # Do each hour angle in turn
    for iha, ha in enumerate(times):
        
        # Calculate the positions of the antennas as seen for this hour angle
        # and declination
        ant_pos = xyz_to_uvw(ants_xyz, ha, phasecentre.dec.rad)
        rtimes[row:row + nrowsperintegration] = ha * 43200.0 / numpy.pi
        
        # Loop over all pairs of antennas. Note that a2>a1
        for a1 in range(nants):
            for a2 in range(a1 + 1, nants):
                rantenna1[row:row + nch] = a1
                rantenna2[row:row + nch] = a2
                
                # Loop over all frequencies and polarisations
                for ch in range(nch):
                    # noinspection PyUnresolvedReferences
                    k = frequency[ch] / constants.c.value
                    ruvw[row, :] = (ant_pos[a2, :] - ant_pos[a1, :]) * k
                    rfrequency[row] = frequency[ch]
                    rchannel_bandwidth[row] = channel_bandwidth[ch]
                    row += 1
    
    if zerow:
        ruvw[..., 2] = 0.0
    assert row == nrows
    rintegration_time = numpy.full_like(rtimes, integration_time)
    vis = Visibility(uvw=ruvw, time=rtimes, antenna1=rantenna1, antenna2=rantenna2,
                     frequency=rfrequency, vis=rvis,
                     weight=rweight, imaging_weight=rweight,
                     integration_time=rintegration_time, channel_bandwidth=rchannel_bandwidth,
                     polarisation_frame=polarisation_frame)
    vis.phasecentre = phasecentre
    vis.configuration = config
    log.info("create_visibility: %s" % (vis_summary(vis)))
    assert isinstance(vis, Visibility), "vis is not a Visibility: %r" % vis
    return vis


def create_blockvisibility(config: Configuration,
                           times: numpy.array,
                           frequency: numpy.array,
                           phasecentre: SkyCoord,
                           weight: float = 1.0,
                           polarisation_frame: PolarisationFrame = None,
                           integration_time=1.0,
                           channel_bandwidth=1e6,
                           zerow=False, **kwargs) -> BlockVisibility:
    """ Create a BlockVisibility from Configuration, hour angles, and direction of source

    Note that we keep track of the integration time for BDA purposes

    :param config: Configuration of antennas
    :param times: hour angles in radians
    :param frequency: frequencies (Hz] [nchan]
    :param weight: weight of a single sample
    :param phasecentre: phasecentre of observation
    :param channel_bandwidth: channel bandwidths: (Hz] [nchan]
    :param integration_time: Integration time ('auto' or value in s)
    :param polarisation_frame:
    :return: BlockVisibility
    """
    assert phasecentre is not None, "Must specify phase centre"
    
    if polarisation_frame is None:
        polarisation_frame = correlate_polarisation(config.receptor_frame)
    
    nch = len(frequency)
    ants_xyz = config.data['xyz']
    nants = len(config.data['names'])
    ntimes = len(times)
    npol = polarisation_frame.npol
    visshape = [ntimes, nants, nants, nch, npol]
    rvis = numpy.zeros(visshape, dtype='complex')
    rweight = weight * numpy.ones(visshape)
    rtimes = numpy.zeros([ntimes])
    ruvw = numpy.zeros([ntimes, nants, nants, 3])
    
    # Do each hour angle in turn
    for iha, ha in enumerate(times):
        
        # Calculate the positions of the antennas as seen for this hour angle
        # and declination
        ant_pos = xyz_to_uvw(ants_xyz, ha, phasecentre.dec.rad)
        rtimes[iha] = ha * 43200.0 / numpy.pi
        
        # Loop over all pairs of antennas. Note that a2>a1
        for a1 in range(nants):
            for a2 in range(a1 + 1, nants):
                ruvw[iha, a2, a1, :] = (ant_pos[a2, :] - ant_pos[a1, :])
                ruvw[iha, a1, a2, :] = (ant_pos[a1, :] - ant_pos[a2, :])
    
    rintegration_time = numpy.full_like(rtimes, integration_time)
    rchannel_bandwidth = numpy.full_like(frequency, channel_bandwidth)
    if zerow:
        ruvw[..., 2] = 0.0
    vis = BlockVisibility(uvw=ruvw, time=rtimes, frequency=frequency, vis=rvis, weight=rweight,
                          integration_time=rintegration_time, channel_bandwidth=rchannel_bandwidth,
                          polarisation_frame=polarisation_frame)
    vis.phasecentre = phasecentre
    vis.configuration = config
    log.info("create_blockvisibility: %s" % (vis_summary(vis)))
    assert isinstance(vis, BlockVisibility), "vis is not a BlockVisibility: %r" % vis
    
    return vis


def create_visibility_from_rows(vis: Union[Visibility, BlockVisibility], rows: numpy.ndarray, makecopy=True) \
        -> None:
    """ Create a Visibility from selected rows

    :param vis: Visibility
    :param rows: Boolean array of row selction
    :param makecopy: Make a deep copy (True)
    :return: Visibility
    """
    
    if rows is None or numpy.sum(rows) == 0:
        return None
    
    assert len(rows) == vis.nvis, "Length of rows does not agree with length of visibility"
    
    if isinstance(vis, Visibility):
        
        if makecopy:
            newvis = copy_visibility(vis)
            if vis.cindex is not None and len(rows) == len(vis.cindex):
                newvis.cindex = vis.cindex[rows]
            else:
                newvis.cindex = None
            if vis.blockvis is not None:
                newvis.blockvis = vis.blockvis
            newvis.data = copy.deepcopy(vis.data[rows])
            return newvis
        else:
            vis.data = copy.deepcopy(vis.data[rows])
            if vis.cindex is not None:
                vis.cindex = vis.cindex[rows]
            return vis
    else:
        
        if makecopy:
            newvis = copy_visibility(vis)
            newvis.data = copy.deepcopy(vis.data[rows])
            return newvis
        else:
            vis.data = copy.deepcopy(vis.data[rows])
            
            return vis


def phaserotate_visibility(vis: Visibility, newphasecentre: SkyCoord, tangent=True, inverse=False) -> Visibility:
    """
    Phase rotate from the current phase centre to a new phase centre

    If tangent is False the uvw are recomputed and the visibility phasecentre is updated.
    Otherwise only the visibility phases are adjusted

    :param vis: Visibility to be rotated
    :param newphasecentre:
    :param tangent: Stay on the same tangent plane? (True)
    :param inverse: Actually do the opposite
    :return: Visibility
    """
    assert isinstance(vis, Visibility), "vis is not a Visibility: %r" % vis
    
    l, m, n = skycoord_to_lmn(newphasecentre, vis.phasecentre)
    
    # No significant change?
    if numpy.abs(n) > 1e-15:
        
        # Make a new copy
        newvis = copy_visibility(vis)
        
        phasor = simulate_point(newvis.uvw, l, m)
        
        if len(newvis.vis.shape) > len(phasor.shape):
            phasor = phasor[:, numpy.newaxis]
        
        if inverse:
            newvis.data['vis'] *= phasor
        else:
            newvis.data['vis'] *= numpy.conj(phasor)
        
        # To rotate UVW, rotate into the global XYZ coordinate system and back. We have the option of
        # staying on the tangent plane or not. If we stay on the tangent then the raster will
        # join smoothly at the edges. If we change the tangent then we will have to reproject to get
        # the results on the same image, in which case overlaps or gaps are difficult to deal with.
        if not tangent:
            if inverse:
                xyz = uvw_to_xyz(vis.data['uvw'], ha=-newvis.phasecentre.ra.rad, dec=newvis.phasecentre.dec.rad)
                newvis.data['uvw'][...] = \
                    xyz_to_uvw(xyz, ha=-newphasecentre.ra.rad, dec=newphasecentre.dec.rad)[...]
            else:
                # This is the original (non-inverse) code
                xyz = uvw_to_xyz(newvis.data['uvw'], ha=-newvis.phasecentre.ra.rad, dec=newvis.phasecentre.dec.rad)
                newvis.data['uvw'][...] = xyz_to_uvw(xyz, ha=-newphasecentre.ra.rad, dec=newphasecentre.dec.rad)[
                    ...]
            newvis.phasecentre = newphasecentre
        return newvis
    else:
        return vis


def create_blockvisibility_from_ms(msname, channum=None, ack=False):
    """ Minimal MS to BlockVisibility converter

    The MS format is much more general than the ARL BlockVisibility so we cut many corners. This requires casacore to be
    installed. If not an exception ModuleNotFoundError is raised.

    Creates a list of BlockVisibility's, split by field and spectral window
    
    :param msname: File name of MS
    :param channum: range of channels e.g. range(17,32), default is None meaning all
    :return:
    """
    try:
        from casacore.tables import table  # pylint: disable=import-error
    except ModuleNotFoundError:
        raise ModuleNotFoundError("casacore is not installed")
    
    tab = table(msname, ack=ack)
    log.debug("create_blockvisibility_from_ms: %s" % str(tab.info()))

    fields = numpy.unique(tab.getcol('FIELD_ID'))
    dds = numpy.unique(tab.getcol('DATA_DESC_ID'))
    log.debug("create_blockvisibility_from_ms: Found unique fields %s, unique data descriptions %s" % (
        str(fields), str(dds)))
    vis_list = list()
    for dd in dds:
        dtab = table(msname, ack=ack).query('DATA_DESC_ID==%d' % dd, style='')
        for field in fields:
            ms = dtab.query('FIELD_ID==%d' % field, style='')
            assert ms.nrows() > 0, "Empty selection for FIELD_ID=%d and DATA_DESC_ID=%d" % (field, dd)
            log.debug("create_blockvisibility_from_ms: Found %d rows" % (ms.nrows()))
            time = ms.getcol('TIME')
            channels = ms.getcol('DATA').shape[-2]
            log.debug("create_visibility_from_ms: Found %d channels" % (channels))
            if channum is None:
                channum = range(channels)
            try:
                ms_vis = ms.getcol('DATA')[:, channum, :]
                ms_weight = ms.getcol('WEIGHT')[:, :]
            except IndexError:
                raise IndexError("channel number exceeds max. within ms")
            uvw = -1 * ms.getcol('UVW')
            antenna1 = ms.getcol('ANTENNA1')
            antenna2 = ms.getcol('ANTENNA2')
            integration_time = ms.getcol('INTERVAL')
            
            # Now get info from the subtables
            spwtab = table('%s/SPECTRAL_WINDOW' % msname, ack=False)
            cfrequency = spwtab.getcol('CHAN_FREQ')[dd][channum]
            cchannel_bandwidth = spwtab.getcol('CHAN_WIDTH')[dd][channum]
            nchan = cfrequency.shape[0]
            
            # Get polarisation info
            poltab = table('%s/POLARIZATION' % msname, ack=False)
            corr_type = poltab.getcol('CORR_TYPE')
            # These correspond to the CASA Stokes enumerations
            if numpy.array_equal(corr_type[0], [1, 2, 3, 4]):
                polarisation_frame = PolarisationFrame('stokesIQUV')
            elif numpy.array_equal(corr_type[0], [5, 6, 7, 8]):
                polarisation_frame = PolarisationFrame('circular')
            elif numpy.array_equal(corr_type[0], [9, 10, 11, 12]):
                polarisation_frame = PolarisationFrame('linear')
            else:
                raise KeyError("Polarisation not understood: %s" % str(corr_type))
            
            npol = 4
            
            # Get configuration
            anttab = table('%s/ANTENNA' % msname, ack=False)
            nants = anttab.nrows()
            mount = anttab.getcol('MOUNT')
            names = anttab.getcol('NAME')
            diameter = anttab.getcol('DISH_DIAMETER')
            xyz = anttab.getcol('POSITION')
            configuration = Configuration(name='', data=None, location=None,
                                          names=names, xyz=xyz, mount=mount, frame=None,
                                          receptor_frame=ReceptorFrame("linear"),
                                          diameter=diameter)
            
            # Get phasecentres
            fieldtab = table('%s/FIELD' % msname, ack=False)
            pc = fieldtab.getcol('PHASE_DIR')[field, 0, :]
            phasecentre = SkyCoord(ra=[pc[0]] * u.rad, dec=pc[1] * u.rad, frame='icrs', equinox='J2000')
            
            bv_times = numpy.unique(time)
            ntimes = len(bv_times)
            
            bv_vis = numpy.zeros([ntimes, nants, nants, nchan, npol]).astype('complex')
            bv_weight = numpy.zeros([ntimes, nants, nants, nchan, npol])
            bv_uvw = numpy.zeros([ntimes, nants, nants, 3])
            
            time_last = time[0]
            time_index = 0
            for row, _ in enumerate(ms_vis):
                # MS has shape [row, npol, nchan]
                # BV has shape [ntimes, nants, nants, nchan, npol]
                if time[row] != time_last:
                    assert time[row] > time_last, "MS is not time-sorted - cannot convert"
                    time_index += 1
                    time_last = time[row]
                bv_vis[time_index, antenna2[row], antenna1[row], ...] = ms_vis[row, ...]
                bv_weight[time_index, antenna2[row], antenna1[row], :, ...] = ms_weight[row, numpy.newaxis, ...]
                bv_uvw[time_index, antenna2[row], antenna1[row], :] = uvw[row, :]
    
            vis_list.append(BlockVisibility(uvw=bv_uvw,
                                            time=bv_times,
                                            frequency=cfrequency,
                                            channel_bandwidth=cchannel_bandwidth,
                                            vis=bv_vis,
                                            weight=bv_weight,
                                            configuration=configuration,
                                            phasecentre=phasecentre,
                                            polarisation_frame=polarisation_frame))
        tab.close()
    return vis_list


def create_visibility_from_ms(msname, channum=None, ack=False):
    """ Minimal MS to BlockVisibility converter

    The MS format is much more general than the ARL BlockVisibility so we cut many corners. This requires casacore to be
    installed. If not an exception ModuleNotFoundError is raised.

    Creates a list of BlockVisibility's, split by field and spectral window

    :param msname: File name of MS
    :param channum: range of channels e.g. range(17,32), default is None meaning all
    :return:
    """
    from processing_components.visibility.coalesce import convert_blockvisibility_to_visibility
    return [convert_blockvisibility_to_visibility(v)
            for v in create_blockvisibility_from_ms(msname=msname, channum=channum, ack=ack)]

