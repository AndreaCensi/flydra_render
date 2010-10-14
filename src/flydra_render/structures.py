
# fields that are added to Flydra's rows

additional_fields = [
                     
     ('time', 'float64'),
     
     ('position', ('float64', 3)),
     ('attitude', ('float64', (3, 3))),
     
     ('linear_velocity_body', ('float64', 3)),
     ('linear_velocity_world', ('float64', 3)),
     ('linear_velocity_modulus', 'float64'),
     
     ('linear_acceleration_body', ('float64', 3)),
     ('linear_acceleration_world', ('float64', 3)),
     ('linear_acceleration_modulus', 'float64'),
     
     ('angular_velocity_body', ('float64', 3)),
     ('angular_velocity_world', ('float64', 3)),
     
     ('reduced_angular_orientation', ('float64')),
     ('reduced_angular_velocity', ('float64')),
     ('reduced_angular_acceleration', ('float64')),
]
