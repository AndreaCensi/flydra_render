import sys
from rfsee.rfsee_client import ClientTCP

def main():
    # host = '131.215.42.189' # Tokyo's IP
    host = '131.215.42.218' # Tokyo's IP behind firewall
    port = 10781
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    
    cp = ClientTCP(host, port)
    cp.config('optics', 'ring_fov180_num180')
    cp.config_compute_mu(True)
    cp.config_stimulus_xml('/home/andrea/landing/20080626/4postsA.xml')
    
    position = [0.5, 0.5, 0.5]
    attitude = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    linear_velocity_body = [0, 0, 0]
    angular_velocity_body = [0, 0, 0]
    
    import time
    ntrials = 1000
    cp.render(position, attitude, linear_velocity_body, angular_velocity_body)
    
    
    start = time.time()
    for i in range(ntrials): #@UnusedVariable
        cp.render(position, attitude, linear_velocity_body, angular_velocity_body)
    end = time.time()
    
    avg = (end - start) / ntrials
    
    print "Average: %f s" % avg
    
    
    cp.close()
    
if __name__ == '__main__':
    main()
