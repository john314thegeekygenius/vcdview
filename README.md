# VCDVIEW -- A console based VCD viewer (because this apparently doesn't exist already...)

How it works:
1. Create a vcd waveform (somehow)
2. Run this fun program with the waveform as the argument:
```
vcdview my_waveform.vcd
```

Use the command interface to interact with the waveform:
```
-- vcdview (ver. 0.1.0) 
-- type h for help 
> (this is where commands go)
```

Useful commands include:
```
h -- help 
p -- print waveform 
set dt <time> -- sets the window time delta (time per character)
set st <time> -- sets where the window should start in the simulation 
pd <filename> -- print the full waveform to a file

```

