# How to run tests

VenueServer tests use `pytest`.

VenueServer tests requires live AMPCS sessions that need to be started manually.

The tests have different inputs for different missions. Currently they can be run on Europa or Psyche WSTS.

## Set up Python virtual environment. (One Time Set up)
```
cd tests
virtualenv -p python3 ve3
source ve3/bin/activate.csh
pip install -r requirements.txt
deactivate
```

## Activate virtual environment

```
cd tests
source ve3/bin/activate.csh
```

## Start WSTS

Start two WSTS sessions. Each WSTS session will have an AMPCS session.

Set the AMPCS sessions in `env.csh` and source it.

```
source env.csh
```

## Run tests

Run pytest
```
pytest
```

To see debug outputs, disable stdout capture.
```
pytest -s
```

You can run a individual test.

```
pytest test_mtak.py
pytest test_mtak.py::test_start_shutdown
```