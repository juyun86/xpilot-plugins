"""Optional internet connectivity, independent of driving roles."""
from openpilot.tesla.plugin import Plugin
from openpilot.tesla.plugin_params import ParamsView


def should_run(started, params, CP):
  return (not started and params.get_bool('IsOffroad') and not params.get_bool('IsEngaged')
          and ParamsView(params).get_bool('ExtStarlinkConnect'))


class Starlink(Plugin):
  @classmethod
  def ui_glyphs(cls):
    from .client import call
    try:
      labels = call('labels', timeout=3).get('labels', [])
      return ''.join(c for text in labels for c in text if ord(c) < 65536 and c.isprintable())[:16384]
    except Exception:
      return ''

  @classmethod
  def processes(cls):
    from .process import RestartingProcess
    return [RestartingProcess('starlinkd', f'{__package__}.service', should_run)]
