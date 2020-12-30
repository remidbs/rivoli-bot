from rivoli.config import CounterName, get_settings


def test_missing_counter_ids():
    for counter in list(CounterName):
        get_settings(counter)
