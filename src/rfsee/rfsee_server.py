from __future__ import with_statement
from StringIO import StringIO
import sys, numpy

#if 1:
    # deal with old files, forcing to numpy
#    import tables.flavor
#    tables.flavor.restrict_flavors(keep=['numpy', 'python'])


from cjson import decode


import flydra.a2.xml_stimulus as xml_stimulus
import flydra_osg.xml_stimulus_osg as xml_stimulus_osg

import fsee
import fsee.Observer

import cgtypes
import cjson
import struct

        
from rfsee.communication import positive_answer, exit_with_error


def go_render(vision, json, compute_mu, write_binary):
    position = numpy.array(json['position'])
    attitude = numpy.array(json['attitude'])
    linear_velocity_body = numpy.array(json['linear_velocity_body'])
    angular_velocity_body = numpy.array(json['angular_velocity_body'])
    
    linear_velocity_body = cgtypes.vec3(linear_velocity_body)
    angular_velocity_body = cgtypes.vec3(angular_velocity_body)
    position = cgtypes.vec3(position)
    orientation = cgtypes.quat.fromMat(cgtypes.quat(), cgtypes.mat3(attitude))

    vision.step(position, orientation)

    R = vision.get_last_retinal_imageR()
    G = vision.get_last_retinal_imageG()
    B = vision.get_last_retinal_imageB()
    y = (R + G + B) / 3.0 / 255

    answer = {}
    answer['luminance'] = y.tolist()

      # Get Q_dot and mu from body velocities
        # WARNING: Getting Q_dot and mu can be very slow
    if compute_mu:
        lvel = json['linear_velocity_body']
        avel = json['angular_velocity_body']
        linear_velocity_body = cgtypes.vec3(numpy.array(lvel))
        angular_velocity_body = cgtypes.vec3(numpy.array(avel))

        qdot, mu = vision.get_last_retinal_velocities(linear_velocity_body, angular_velocity_body)

        answer['nearness'] = mu
        answer['retinal_velocities'] = qdot


    if write_binary:
        what = answer['luminance']
        n = len(what);
        s = struct.pack('>' + 'f' * n, *what);
        positive_answer({'binary_length': len(s), 'mean': numpy.mean(what) }, "Sending binary data (n * 4 bytes)")
        sys.stdout.write(s);
        sys.stdout.flush()
    else:
        positive_answer(answer)
        
    
def go_initialize_stimulus(stimulus_xml, optics, extra):
    """ returns fsee.Observer.Observer """
    try:        
        # stimulus_xml can be a filename
        if stimulus_xml[0] == '/':
            pass
        else:
            # otherwise it's a string
            # pass it like a string
            stimulus_xml = StringIO(stimulus_xml)
        
        stim_xml = xml_stimulus.xml_stimulus_from_filename(stimulus_xml)
        stim_xml_osg = xml_stimulus_osg.StimulusWithOSG(stim_xml.get_root())

        with  stim_xml_osg.OSG_model_path(extra=extra) as osg_model_path:
            # sys.stderr.write('osg_model_path = \n %s' % open(osg_model_path).read())
            hz = 60.0 # fps
            dt = 1.0 / hz

            vision = fsee.Observer.Observer(model_path=osg_model_path,
                                            # scale=1000.0, # from meters to mm
                                            hz=hz,
                                            skybox_basename=None,
                                            full_spectrum=True,
                                            optics=optics,
                                            do_luminance_adaptation=False,
                                            )
    
            positive_answer({}, ('Model loaded, path = %s' % osg_model_path))
            return vision
    
    except IOError, ex:
        exit_with_error("Could not load file %s: %s" % (stimulus_xml, ex))


def main():

    try:
        # XXX Add timestamp
        sys.stderr.write('rfsee_server.py started\n')
        
        # State 
        config = {'compute_mu': 0,
                  'write_binary': 1,
                  'optics': 'buchner71',
                  'osg_params': {'white_arena': False}}
        vision = None
    
        while True:
            line = sys.stdin.readline()
            if not line:
                break
        
            try: 
                json = decode(line)
    
                method = json['method']
                del(json['method'])
                
                if method == 'render':
                    
                    if vision is None:
                        exit_with_error('Before rendering, configure the vision.')
                    
                    go_render(vision, json, config['compute_mu'], config['write_binary'])
                    
                elif method == 'get':
                    key = json['key']
                    if not config.has_key(key):
                        exit_with_error('You asked for key "%s", but I only know %s' % (key, config.keys()))
                        
                    value = config[key]
                    positive_answer({"key":key, "value":value}, 'Here is the results you requested')
                    
                elif method == 'config':
                
                    for key in json.keys():
                        
                        if key == "stimulus_xml":
                            vision = go_initialize_stimulus(json[key], config['optics'],
                                                            config['osg_params'])
                            dirs = vision.cvs.precomputed_optics_module.receptor_dirs
                            dirs = map(lambda x: [x[0], x[1], x[2]], dirs)
                            dirs = []
                            #sys.stderr.write("Type of dirs : %s " % type(dirs[0]))
                            config['receptors_dirs'] = dirs
                            
                        else:
                            if not(config.has_key(key)):
                                exit_with_error('Trying to set config key "%s", but I only know %s' % 
                                    (key, config.keys()))
                            else:
                                old_value = config[key];
                                config[key] = json[key];
                                positive_answer({}, 'Changed %s from %s to %s' % (
                                    str(key), str(old_value), str(json[key])))
                elif method == 'bye':
                    positive_answer({}, 'Goodbye, good sir.')
                else:
                    exit_with_error("Uknown method '%s' \n" % method)
                        
                
            except KeyError:
                exit_with_error("Got incomplete values in request: '%s'\n" % str(line))
            except cjson.DecodeError, ex:
                exit_with_error("Cannot decode json: '%s' \n\t %s\n" % (line, str(ex)))
            except cjson.EncodeError, ex:
                exit_with_error("Cannot encode json. \n\t %s\n" % (str(ex)))
                
        
        sys.stderr.write('rfsee.py ended naturally \n')
        
    except SystemExit:
        pass
    except IOError:
        import traceback
        s = "\n".join(traceback.format_tb(sys.exc_info()[2]));
    #    sys.stderr.write(s)
        exit_with_error("Unexpected error: \n%s" % s)
            
if __name__ == '__main__':
    main()
