import sys
from rfsee_client import ClientTCP

# host = '131.215.42.189' # Tokyo's IP
host = '131.215.42.218' # Tokyo's IP behind firewall
port =  10781

if len(sys.argv) > 1:
    host = sys.argv[1]


cp = ClientTCP(host, port)
cp.config('optics', 'ring_fov180_num180')
cp.config_compute_mu(True)
cp.config_stimulus_xml('/home/andrea/landing/20080626/4postsA.xml')

position = [0.5,0.5,0.5]
attitude = [[1,0,0],[0,1,0],[0,0,1]]
linear_velocity_body = [0,0,0]
angular_velocity_body = [0,0,0]

import time
ntrials = 1000
res = cp.render(position, attitude, linear_velocity_body, angular_velocity_body)


start = time.time()
for i in range(ntrials):
    res = cp.render(position, attitude, linear_velocity_body, angular_velocity_body)
end = time.time()

avg = (end-start)/ntrials

print "Average: %f s"  % avg


cp.close()