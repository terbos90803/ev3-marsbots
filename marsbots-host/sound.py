import simpleaudio as sa

_alert_obj = sa.WaveObject.from_wave_file("klaxon.wav")


def alert():
    _alert_obj.play()
