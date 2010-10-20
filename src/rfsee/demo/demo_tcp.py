import sys
from rfsee.rfsee_client import ClientTCP

def main():
    host = '131.215.42.189' # Tokyo's IP
    #host = '131.215.42.208' # Tokyo's IP behind firewall
    port = 10782
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    
    cp = ClientTCP(host, port)
    
    cp.config_stimulus_xml('/home/andrea/landing/20080626/4postsA.xml')
    
    position = [0.5, 0.5, 0.5]
    attitude = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    linear_velocity_body = [0, 0, 0]
    angular_velocity_body = [0, 0, 0]
    
    res = cp.render(position, attitude, linear_velocity_body, angular_velocity_body)
    
    print res.keys()
    print res['luminance']
    
    cp.close()


if __name__ == '__main__':
    main()
