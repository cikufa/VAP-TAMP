"""Process-local instrumentation of native Kit startup; no installed-source edits."""
import functools
import os


def install(event):
    from omni.isaac.kit import SimulationApp

    def wrap(owner, name):
        original = getattr(owner, name)
        @functools.wraps(original)
        def traced(*args, **kwargs):
            event(name + '_enter')
            result = original(*args, **kwargs)
            event(name + '_exit')
            return result
        setattr(owner, name, traced)

    original_init = SimulationApp.__init__
    def init(self, launch_config=None, *args, **kwargs):
        config = dict(launch_config or {})
        if os.getenv('VAPTAMP_NATIVE_SYNC_LOADS') is not None:
            config['sync_loads'] = os.environ['VAPTAMP_NATIVE_SYNC_LOADS'] == '1'
        event('SimulationApp_constructor', config=config)
        return original_init(self, config, *args, **kwargs)
    SimulationApp.__init__ = init
    original_start = SimulationApp._start_app
    def start(self):
        event('kit_start_enter')
        result = original_start(self)
        event('kit_start_exit')
        import omni.usd
        import omni.isaac.kit.utils
        wrap(omni.usd, 'add_hydra_engine')
        wrap(omni.isaac.kit.utils, 'create_new_stage')
        return result
    SimulationApp._start_app = start
    original_reset = SimulationApp.reset_render_settings
    def reset(self):
        event('reset_render_settings_enter')
        result = original_reset(self)
        import carb.settings
        settings = carb.settings.get_settings()
        event('reset_render_settings_exit', settings={p: settings.get(p) for p in (
            '/rtx/materialDb/syncLoads', '/rtx/hydra/materialSyncLoads',
            '/omni.kit.plugin/syncUsdLoads', '/app/asyncRendering',
            '/plugins/carb.tasking.plugin/threadCount')})
        return result
    SimulationApp.reset_render_settings = reset
    wrap(SimulationApp, '_prepare_ui')
