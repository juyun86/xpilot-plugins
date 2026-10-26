"""Independent ARS408 receiver. Motion/configuration encoders remain pure APIs.

No CAN transmissions are enabled by this package. Hardware motion provisioning
must be supplied by the installation; missing motion reports remain radar faults.
"""
from openpilot.tesla.plugin import Plugin


class ARS408(Plugin):
  SERVICES = ('deviceMotion', 'extrinsicsCalibration')

  def __init__(self, CP, params):
    super().__init__(CP, params)
    from openpilot.selfdrive.locationd.helpers import PoseCalibrator
    from .transmitter import ARS408Transmitter
    self._calibrator = PoseCalibrator()
    self._motion_cache = {}
    self.motion_transmitter = ARS408Transmitter(
      None, enabled=True, mount_inverted=params.get_bool('ExtARS408Inverted'))

  def card_context(self, context, now_ns):
    from .motion import radar_yaw_rate_context
    # Clear first: a malformed context must never preserve an older good sample.
    self.motion_transmitter.update_yaw_rate(None, 0)
    self.motion_transmitter.update_yaw_rate(
      *radar_yaw_rate_context(context, now_ns, self._calibrator, self._motion_cache))

  # control_sends stays the base no-op until the Panda motion contract exists.
  # Consuming real host context does not grant permission to transmit.

  @classmethod
  def radar_interface(cls, CP, CP_SP, params):
    if CP.brand != 'tesla':
      return None
    from .interface import ARS408RadarInterface
    radar = ARS408RadarInterface(CP, CP_SP, mount_inverted=params.get_bool('ExtARS408Inverted'))
    # Selecting this external receiver is independent of factory radar availability.
    # Do not mutate CP/CP_SP, their flags, car port code or the fallback receiver.
    radar.radar_off_can = False
    return radar
