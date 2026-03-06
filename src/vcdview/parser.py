
class waveform:
    def __init__(self, fn):
        self.variables = {}
        self.events = []
        self.info = ""
        self.timescale = 0 # in fs
        self.filename = fn

    def get_filename(self):
        return self.filename

    def set_info(self, data):
        self.info = data 

    def parse_timescalestr(self, s):
        if len(s) == 0:
            raise ValueError(f"Invalid time string \"{s}\"")
        parts = s.strip().split()
        number = int(parts[0])
        unit = parts[1]
    
        scale_to_fs = {
            "fs": 1,
            "ps": 1_000,
            "ns": 1_000_000,
            "us": 1_000_000_000,
            "ms": 1_000_000_000_000,
            "s":  1_000_000_000_000_000,
        }
    
        if unit not in scale_to_fs:
            raise ValueError(f"Invalid timescale unit: {unit}")
    
        return number * scale_to_fs[unit]

    def set_timescale(self, tss):
        ts = self.parse_timescalestr(tss)
        self.timescale = ts 

    def add_signal(self, stype, name, identifier, bit_width):
        self.variables[identifier] = {
                "name": name,
                "width": bit_width,
                "type": stype
                }

    def add_event(self, tick, signals):
        # Fix the signals 
        for sig in signals:
            real_name = self.variables.get(sig[1])
            if real_name == None:
                raise RuntimeError(f"ERROR! Invalid variable symbol {sig[1]}")
            sig[1] = real_name
        # Fix the tick 
        tick *= self.timescale
        self.events.append([tick, signals])


def parse_vcd(waveform_name):
    print(f"Loading {waveform_name}...")
    wf = waveform(waveform_name)

    file_date = ""
    file_mker = ""
    timescale = ""

    scope_stack = []
    variables = []

    try:
        with open(waveform_name) as f:
            print(f"] Wavefile: {waveform_name}")
            # Parse header 
            for rawline in f:
                line = rawline.strip()
                #print(line)
                if len(line) == 0:
                    continue
                tokens = line.split(' ')
                #print(tokens)
                # Check for info 
                if line[0] == '$':
                    if tokens[0] == "$date":
                        file_date = ""
                        for l in f:
                            il = l.strip()
                            if il == "$end":
                                break;
                            file_date += il + "\n"
                        print(f"  -- {file_date}", end="")
                    if tokens[0] == "$version":
                        file_mker = ""
                        for l in f:
                            il = l.strip()
                            if il == "$end":
                                break;
                            file_mker += il + "\n"
                        print(f"  -- {file_mker}", end="")
                    if tokens[0] == "$timescale":
                        timescale = f.readline().strip()
                        print(f"] TS: {timescale}")
                        for l in f:
                            il = l.strip()
                            if il == "$end":
                                break;
                    if tokens[0] == "$enddefinitions":
                        break
                    if tokens[0] == "$scope":
                        scope_stack.append(tokens[2])
                    if tokens[0] == "$upscope":
                        scope_stack.pop()
                    if tokens[0] == "$var":
                        variables.append([".".join(scope_stack+[tokens[4]]), tokens[1], tokens[2], tokens[3]])
            # Add signals 
            for var in variables:
                wf.add_signal(var[1], var[0], var[3], var[2])
            # Set the timescale 
            wf.set_timescale(timescale)
            # Set the information 
            wf.set_info(f"Created on {file_date} with {file_mker}")
            
            min_event_time = 1_000_000_000_000_000
            pevent_time = 0
            event_time = 0
            event_signals = []

            # Parse events now 
            for rawline in f:
                line = rawline.strip().lower()
                if len(line) == 0:
                    continue

                tokens = line.split(' ')
                # Parse the event time 
                if tokens[0][0] == '#':
                    # Push any available events 
                    if len(event_signals) > 0:
                        wf.add_event(event_time, event_signals)
                    event_signals = []
                    pevent_time = event_time
                    event_time = int(tokens[0][1:])
                    det = event_time - pevent_time
                    if det < min_event_time and det > 0:
                        min_event_time = det 
                # Check for scalar values 
                if tokens[0][0] == '0' or \
                   tokens[0][0] == '1' or \
                   tokens[0][0] == 'x' or \
                   tokens[0][0] == 'z' or \
                   tokens[0][0] == 'u':
                    value = tokens[0][0]
                    id = tokens[0][1:]
                    event_signals.append([value,id])
                # Check for vector values
                if tokens[0][0] == 'b':
                    bitstream = tokens[0][1:]
                    # TODO:
                    # bits need to be independent because 
                    # 01uxz is a valid set of bits... 
                    value = bitstream
                    id = tokens[1]
                    event_signals.append([value,id])
                # Check for real values
                if tokens[0][0] == 'r':
                    value = float(tokens[0][1:])
                    id = tokens[1]
                    event_signals.append([value,id])

        # Add an end event 
        wf.add_event(event_time+min_event_time, [])

        print("] Done reading wave file...")
    except FileNotFoundError:
        print(f"{waveform_name} not found.")
        return None
    except PermissionError:
        print(f"Permission denied opening {waveform_name}")
        return None
    except OSError as e:
        print(f"Failed to open file: {e}")
        return None

    return wf
