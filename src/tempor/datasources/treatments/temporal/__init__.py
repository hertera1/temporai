from tempor.core import plugins
from tempor.datasources import datasource

plugins.register_plugin_category(
    "treatments.temporal", datasource.TemporalTreatmentEffectsDataSource, plugin_type="datasource"
)

plugins.importing.import_plugins(__file__)

__all__ = [  # pyright: ignore
    *plugins.importing.gather_modules_names(__file__),
]
