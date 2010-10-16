
from rfsee_client import ClientProcess

cp = ClientProcess('./rfsee_server.py')

cp.config_stimulus_xml('/home/andrea/landing/20080626/4postsA.xml')

position = [0.5,0.5,0.5]
attitude = [[1,0,0],[0,1,0],[0,0,1]]
linear_velocity_body = [0,0,0]
angular_velocity_body = [0,0,0]

res = cp.render(position, attitude, linear_velocity_body, angular_velocity_body)

print res['luminance']

cp.close()
