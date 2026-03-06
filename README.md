# VCDVIEW 
## A terminal based VCD viewer 

#### Installation (From Wheel File)
Download the latest whl file from the releases tab. <br>
Install with the command:
```
pip install <vcdview-x.x.x.whl> 
```
Replacing `vcdview-x.x.x.whl` with the correct wheel name.

#### Installation (From Project Directory)
Open a terminal in the same directory as the README.md <br>
Run the following command:
```
pip install .
```

#### How it works
1. Create a vcd waveform (somehow)
2. Run this program with the waveform as the argument:
```
vcdview my_waveform.vcd
```

Use the command interface to interact with the waveform:
```
] vcdview (ver 0.1.0)
] type `h` for help

> (this is where commands go)
```

Some useful commands include:
```
h -- help 
q -- exit the application
c -- clear terminal 
p -- print waveform 
l -- list available signals 
z -- set the zoom
```

