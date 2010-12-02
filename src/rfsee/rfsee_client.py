from .communication import exit_with_error

class SimulationException(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, string):
        Exception.__init__(self, string)

from cjson import encode, decode, EncodeError, DecodeError

class Client:
    stdin = None
    stout = None
    
    def __init__(self, stdin, stdout):
        self.stdin = stdin
        self.stdout = stdout
        
        self.config_use_binary(False)
    
    def get(self, key):
        self.write_json({'method': 'get', "key": key})
        packet = self.expect_ok_status()
        return packet["value"]
        
    def config(self, key, value):
        self.write_json({'method': 'config', key: value})
        self.expect_ok_status()
        
    def render(self, position, attitude, linear_velocity_body, angular_velocity_body):
        
        # write the data as simple lists of floats
        def simple(x):
            return [x[0], x[1], x[2]]
        
        def simple_matrix(x):
            return [ [ x[0, 0], x[0, 1], x[0, 2]],
                     [ x[1, 0], x[1, 1], x[1, 2]],
                     [ x[2, 0], x[2, 1], x[2, 2]]  ]
        

        self.write_json({
            'method': 'render',
            'position': simple(position),
            'attitude': simple_matrix(attitude),
            'linear_velocity_body': simple(linear_velocity_body),
            'angular_velocity_body': simple(angular_velocity_body),
        });
        # FIXME ADD: BINARY MODE
        return self.expect_ok_status()
    
    def close(self):
        self.write_json({'method': 'bye'})
        return self.expect_ok_status()

    def expect_ok_status(self):
        packet = self.read_json()
        try:
            if not packet['ok']:
                raise SimulationException("Error sent: %s " % packet['status'])
        except KeyError:
            exit_with_error("Got incomplete values in answer: '%s'\n" % packet)
        return packet
        
    def write_json(self, dic):
        try:
            self.stdout.write(encode(dic))
            self.stdout.write("\n")
            self.stdout.flush();
        except IOError, ex:
            raise SimulationException("IOError while writing: %s" % ex)
        except EncodeError, ex:
            raise SimulationException("Cannot encode json. \n\t %s '''%s'''\n" % 
                                       (str(ex), dic))
    
    def read_json(self):
        try:
            line = self.stdin.readline()
            if not line:
                raise SimulationException("Broken communication") 
            return decode(line)
        except IOError, ex:
            raise SimulationException("IOError while reading: %s" % ex)
        except DecodeError, ex:
            raise SimulationException("Cannot decode json: '%s' \n\t %s\n" % (line, str(ex)))
        
    # some pre-set config settings
    def config_stimulus_xml(self, path):
        self.config('stimulus_xml', path)
    
    def config_compute_mu(self, do):
        if do:
            self.config('compute_mu', 1)
        else:
            self.config('compute_mu', 0)
    
    # binary sending
    def config_use_binary(self, use):
        if use:
            self.config('write_binary', 1)
            print "Warning: did not implement binary communication for python"
        else:
            self.config('write_binary', 0)
    
    def config_use_white_arena(self):
        ''' Tweak the OSG model such that the arena is displayed in white. 
            (the posts are the only distinguishable entities. 
            Call this before config_stimulus_xml().
        '''
        self.config('osg_params', {'white_arena': True})
    
import socket

class ClientTCP(Client):

    def __init__(self, host, port):
        #create an INET, STREAMing socket
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        f = self.s.makefile()
        Client.__init__(self, f, f)
 

    def close(self):
        Client.close(self)
        self.s.close()
        

import sys
import subprocess 
        
class ClientProcess(Client):
    process = None;

    def __init__(self, script_path='rfsee_server'):
        self.process = subprocess.Popen(script_path,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=sys.stderr,
            stdin=subprocess.PIPE)
        Client.__init__(self, self.process.stdout, self.process.stdin)

    def close(self):
        Client.close(self)
        # ready anything left, and wait for termination
        self.process.communicate(input=None)




         
