from sensors.fan_controller import FanController

_fan_instance = None

def get_fan():
    global _fan_instance

    if _fan_instance is None:
        _fan_instance = FanController()

    return _fan_instance