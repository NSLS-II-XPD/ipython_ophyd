# Devices

## Gas Switcher

The gas switcher is represented by the ophyd Device instance ``gas``. Before
using, you must set the list of gasses like so:

```
gas.gas_list = ['N', 'Ar']
```

There may be up to six gasses, but you only need to specify the number that you
plan to use.

To change gasses interactively, use the ``set`` method. It expects the gas name,
not the numerical position.

```
gas.set("N")
```

When ``gas`` is included as a "detector" or scanned like a motor, four things
are recorded in the database: the current and requested numerical position and
the current and requested gas name.


For example, this "scans" the gas switcher, triggering the ``pe1`` at Nitrogen
and then at Argon.

```
list_scan([pe1], gas, ["N", "Ar"])
```

## Temperature Controllers (eurotherm and cs700)

The ophyd Devices representing the temp controllers are named ``eurotherm`` and
``cs700``.

They can be used like any motor in a scan. For example:

```
dscan([pe1], eurotherm, -10, 10)
```

They can also be used interatively:

```
mov(eurotherm, 50)
```

A special feature of the ``eurotherm``, not shared by the ``cs700``, is a
configurable ``tolerance`` attribute. The tolerance is set to 10 in the startup
file, but it can be changed interactively.

```
eurotherm.tolerance = 15
```

Given the instability of the Eurotherm, a tolerance of 10 or greater is
recommended.

## RGA

When an RGA is included as a detector in a bluesky plan, it will automatically
be started at the beginning of the scan and stopped at the end.

```
RE(count([rga], num=5, delay=1), LiveTable([rga]))
```
