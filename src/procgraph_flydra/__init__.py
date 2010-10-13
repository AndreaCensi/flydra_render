''' ProcGraph blocks to visualize flydra data. '''

import flydra_db_source
import flydra_db_image
import values2retina
import arena_display

# FIXME, make this importing code easier
import os
from procgraph.core.registrar import default_library
from procgraph.core.model_loader import pg_look_for_models
dir = os.path.join(os.path.dirname(__file__), 'models')

pg_look_for_models(default_library, additional_paths=[dir], ignore_env=True,
                   assign_to_module='procgraph_flydra')


