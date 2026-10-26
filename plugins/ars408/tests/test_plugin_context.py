"""API wiring failures: no declared subscriptions, cold/stale samples emitting
motion, invalidation retaining an old yaw, wrong mount sign, or unauthorized TX.
Uses real capnp readers, PoseCalibrator, host CardContext and radar DBC. No sockets.
"""
from types import SimpleNamespace

import pytest
from opendbc.car import structs
from openpilot.cereal import log
from openpilot.tesla.card_context import CardContext, METADATA

from ..plugin import ARS408
from .test_transmitter import decode

NOW = 3_000_000_000


def fixture(inverted=True):
  params = SimpleNamespace(get_bool=lambda key: inverted if key == 'ExtARS408Inverted' else False)
  plugin = ARS408(SimpleNamespace(brand='tesla'), params)
  motion = log.DeviceMotion.new_message()
  motion.inputsOK = motion.sensorsOK = motion.posenetOK = True
  motion.timestamp = NOW
  motion.angularVelocityDevice = {'x': 0.1, 'y': 0.2, 'z': 0.3, 'valid': True}
  calibration = log.ExtrinsicsCalibration.new_message()
  calibration.rpyCalib = [0., 0., 0.]
  calibration.calStatus = 'calibrated'
  class Snapshot(dict):
    pass
  sm = Snapshot(deviceMotion=motion.as_reader(), extrinsicsCalibration=calibration.as_reader())
  for key in METADATA:
    setattr(sm, key, dict.fromkeys(sm, NOW if key == 'logMonoTime' else True))
  cs = structs.CarState()
  cs.canValid = True
  cs.vEgoRaw = 10.
  cs.gearShifter = 'drive'
  return plugin, sm, cs


@pytest.mark.parametrize('inverted,sign', [(True, 1), (False, -1)])
def test_host_snapshot_reaches_calibrated_encoder_without_can_authority(inverted, sign):
  plugin, sm, cs = fixture(inverted)
  assert set(plugin.SERVICES) == set(sm)
  assert plugin.motion_transmitter.update(0, cs, NOW) == []
  plugin.card_context(CardContext(sm, plugin.SERVICES), NOW)
  frames = plugin.motion_transmitter.update(0, cs, NOW)
  assert len(frames) == 2
  assert decode(frames[0], 'SpeedInformation')['RadarDevice_Speed'] == pytest.approx(10.)
  assert decode(frames[1], 'YawRateInformation')['RadarDevice_YawRate'] == pytest.approx(sign * 17.19, abs=.01)
  # No Panda rule exists yet: production hook must not leak prepared frames.
  assert plugin.control_sends(cs, None, NOW) == []
  assert plugin.motion_transmitter.update(5, cs, NOW + 150_000_001) == []


@pytest.mark.parametrize('failure', ['invalid', 'unseen', 'stale', 'uncalibrated'])
def test_api_invalidates_previous_sample(failure):
  plugin, sm, cs = fixture()
  plugin.card_context(CardContext(sm, plugin.SERVICES), NOW)
  assert plugin.motion_transmitter.yaw_rate_valid(NOW)
  if failure == 'invalid':
    sm.valid['deviceMotion'] = False
  elif failure == 'unseen':
    sm.seen['deviceMotion'] = False
  elif failure == 'stale':
    sm.logMonoTime['deviceMotion'] = NOW - 150_000_001
  else:
    calibration = log.ExtrinsicsCalibration.new_message()
    calibration.rpyCalib = [0., 0., 0.]
    calibration.calStatus = 'uncalibrated'
    sm['extrinsicsCalibration'] = calibration.as_reader()
  plugin.card_context(CardContext(sm, plugin.SERVICES), NOW + 1)
  assert plugin.motion_transmitter.update(5, cs, NOW + 1) == []
