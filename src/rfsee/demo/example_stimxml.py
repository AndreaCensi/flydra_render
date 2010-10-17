
example_stim_xml = '''
<stimxml version="1">
  <cylindrical_arena>
    <diameter>2</diameter>
    <height>0.8</height>
    <axis>0 0 1</axis>
    <origin>0.15 0.48 0.0</origin>
  </cylindrical_arena>

  <cylindrical_post>
    <vert>0.2159869 ,  0.23529284,  0.39472771</vert>
    <vert>0.18479352,  0.24706014,  0.00616013</vert>
    <diameter>0.0508</diameter>
  </cylindrical_post>

  <cylindrical_post>
    <vert>0.26938038,  0.73651523,  0.38791465</vert>
    <vert>0.2329588 ,  0.71118121, -0.00281394</vert>
    <diameter>0.0508</diameter>
  </cylindrical_post>

  <cylindrical_post>
    <vert>-0.22548925,  0.8553097 ,  0.4100357</vert>
    <vert>-0.21959056,  0.8369173 ,  0.02571872</vert>
    <diameter>0.0508</diameter>
  </cylindrical_post>

  <cylindrical_post>
    <vert>-0.30463551,  0.32364712,  0.41044896</vert>
    <vert>-0.30685028,  0.33559432,  0.03426788</vert>
    <diameter>0.0508</diameter>
  </cylindrical_post>

  <multi_camera_reconstructor>
    <single_camera_calibration>
      <cam_id>mama01_0</cam_id>
      <calibration_matrix>-4.904264e+02 -1.107516e+02 -2.443060e+02  4.741160e+05; -2.861491e+02  4.361509e+02  1.315223e+02  2.387648e+05; -3.429405e-01  5.421856e-01 -7.670897e-01  9.909943e+02</calibration_matrix>
      <resolution>656 491</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>1000.0</fc2>
        <cc1>324.46078785677207</cc1>
        <cc2>245.8989649198021</cc2>
        <k1>-1.6453238086116195</k1>
        <k2>2.3596787188910184</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama02_0</cam_id>
      <calibration_matrix>2.771731e+02 -4.629598e+02 -2.659999e+02  6.371806e+05; -2.839966e+02 -4.612485e+02  1.435894e+02  6.903227e+05; -3.768601e-01 -5.547680e-01 -7.417607e-01  1.550881e+03</calibration_matrix>
      <resolution>656 491</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>1000.0</fc2>
        <cc1>317.64022687190129</cc1>
        <cc2>253.60089300842131</cc2>
        <k1>-1.5773930368340232</k1>
        <k2>1.9308294843687406</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama03_0</cam_id>
      <calibration_matrix>4.971680e+02  8.274244e+01 -2.589535e+02  3.403682e+05;  3.453504e+02 -4.195060e+02  1.049272e+02  5.986545e+05;  4.229416e-01 -5.401825e-01 -7.275460e-01  1.432702e+03</calibration_matrix>
      <resolution>656 491</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>1000.0</fc2>
        <cc1>324.71598020460021</cc1>
        <cc2>251.94156882441408</cc2>
        <k1>-1.5980186754551708</k1>
        <k2>2.0785278852038735</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama04_0</cam_id>
      <calibration_matrix>-2.011650e+02  4.487405e+02 -2.021755e+02  1.766921e+05;  3.791132e+02  3.954719e+02  8.671726e+01  2.162830e+05;  4.210977e-01  5.125944e-01 -7.482805e-01  9.173965e+02</calibration_matrix>
      <resolution>656 491</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>1000.0</fc2>
        <cc1>321.16469753503111</cc1>
        <cc2>254.99035329705143</cc2>
        <k1>-1.5578225603537565</k1>
        <k2>1.8607646349066083</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama05_0</cam_id>
      <calibration_matrix>4.408130e+02  2.300243e+01 -3.488840e+02  2.251922e+05;  2.173232e+01 -4.377104e+02 -2.615853e+02  4.140880e+05;  4.631188e-03  1.034849e-02 -9.999357e-01  7.623284e+02</calibration_matrix>
      <resolution>656 491</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>1000.0</fc2>
        <cc1>331.94942036735256</cc1>
        <cc2>255.53456192844098</cc2>
        <k1>-1.6957859852283426</k1>
        <k2>2.4257906320858535</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama06_0</cam_id>
      <calibration_matrix>6.720309e+02 -3.456779e+02 -1.235945e+02  5.686230e+05;  2.733984e+01 -2.237973e+02  2.645175e+02  1.148915e+05;  1.138439e-01 -9.611069e-01 -2.516209e-01  1.590748e+03</calibration_matrix>
      <resolution>752 240</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>500.0</fc2>
        <cc1>374.98554235533243</cc1>
        <cc2>114.39103018661532</cc2>
        <k1>-1.0429320520976231</k1>
        <k2>1.0944382762766243</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama06_1</cam_id>
      <calibration_matrix>-6.055246e+02  3.597921e+02 -1.020963e+02  2.860117e+05;  1.304119e+01  2.311795e+02  2.632059e+02 -9.889233e+04;  9.278682e-02  9.509125e-01 -2.952220e-01  6.862650e+02</calibration_matrix>
      <resolution>752 240</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>500.0</fc2>
        <cc1>376.40974850827808</cc1>
        <cc2>110.92632158979187</cc2>
        <k1>-1.0590189242480634</k1>
        <k2>1.1693675791273346</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama07_0</cam_id>
      <calibration_matrix>6.059584e+02  3.549294e+02 -9.409000e+01  1.834414e+05;  2.003505e+02 -1.084735e+02  2.392856e+02  5.605704e+04;  8.670934e-01 -4.255885e-01 -2.588890e-01  1.210432e+03</calibration_matrix>
      <resolution>752 240</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>500.0</fc2>
        <cc1>376.07856010472216</cc1>
        <cc2>120.56481375979682</cc2>
        <k1>-1.1039397812639224</k1>
        <k2>1.2767452559678902</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama07_1</cam_id>
      <calibration_matrix>-4.777411e+01  6.770563e+02 -9.847555e+01  6.974870e+04;  1.845566e+02  1.277381e+02  2.436675e+02 -6.223179e+04;  8.113262e-01  5.221587e-01 -2.628689e-01  7.652623e+02</calibration_matrix>
      <resolution>752 240</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>500.0</fc2>
        <cc1>375.90532263364349</cc1>
        <cc2>118.17825957762014</cc2>
        <k1>-1.0529590681868382</k1>
        <k2>1.0475960377322129</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama08_0</cam_id>
      <calibration_matrix>1.263225e+02 -7.863315e+02 -1.414303e+02  8.611537e+05; -1.676897e+02 -1.553994e+02  2.971723e+02  9.157796e+04; -7.550834e-01 -6.052025e-01 -2.521488e-01  1.543896e+03</calibration_matrix>
      <resolution>752 240</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>500.0</fc2>
        <cc1>377.19874603622384</cc1>
        <cc2>114.1308192392591</cc2>
        <k1>-1.0714816357344443</k1>
        <k2>1.1887872738210006</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
    <single_camera_calibration>
      <cam_id>mama08_1</cam_id>
      <calibration_matrix>-6.369316e+02 -4.350792e+02 -5.937384e+01  6.792130e+05; -1.890457e+02  1.087584e+02  3.071636e+02 -5.171885e+04; -8.536019e-01  4.820929e-01 -1.973584e-01  1.001991e+03</calibration_matrix>
      <resolution>752 240</resolution>
      <scale_factor>0.001</scale_factor>
      <non_linear_parameters>
        <fc1>1000.0</fc1>
        <fc2>500.0</fc2>
        <cc1>376.33474164499603</cc1>
        <cc2>117.16999307874083</cc2>
        <k1>-1.0949966756204308</k1>
        <k2>1.2785517624198808</k2>
        <p1>0.0</p1>
        <p2>0.0</p2>
        <alpha_c>0.0</alpha_c>
      </non_linear_parameters>
    </single_camera_calibration>
  </multi_camera_reconstructor>
</stimxml>'''


