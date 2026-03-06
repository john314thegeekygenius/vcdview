import math
try:
    import curses
except ImportError:
    print("Curses not supported on this platform.")
import sys
from colorama import just_fix_windows_console, Fore, Back, Style

scale_to_fs = {
        "fs": 1,
        "ps": 1_000,
        "ns": 1_000_000,
        "us": 1_000_000_000,
        "ms": 1_000_000_000_000,
        "s":  1_000_000_000_000_000,
}

g_timescales = [
    "fs",
    "ps",
    "ns",
    "us",
    "ms",
    " s",
]

timescale_cnvt = [
    # fs
    1_000_000_000_000_000,
    # ps
    1_000_000_000_000,
    # ns
    1_000_000_000,
    # us
    1_000_000,
    # ms
    1_000,
    # s
    1
]

timescale_scaler = [
    # fs
    1,
    # ps
    1_000,
    # ns
    1_000_000,
    # us
    1_000_000_000,
    # ms
    1_000_000_000_000,
    # s
    1_000_000_000_000_000,
]

render_variables = []

max_waveform_width = 160

def waveform_ui(stdscr, wf_data):
    curses.curs_set(0)
    stdscr.keypad(True)
    curses.noecho()
    curses.cbreak()
    curses.start_color()

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Waveform Viewer - Press q to exit")
        stdscr.refresh()

        key = stdscr.getch()
        if key == ord('q'):
            break


def render_wvf_curses(wf_data):
    sys.stdout.flush()
    curses.wrapper(waveform_ui, wf_data)
    print()


def magnitude(n):
    if n == 0:
        return 0
    return 10 ** math.floor(math.log10(abs(n)))

def get_wf_tdelta(wf_data):
    min_dt = None
    curtime = 0
    nexttime = 0
    eventidx = 0
    events = wf_data.events
    for time, changes in events:
        curtime = time 
        if eventidx < len(events)-1:
            nexttime = events[eventidx+1][0]
        else:
            nexttime = curtime+1_000_000_000_000_000
        eventidx += 1
        deltatime = nexttime - curtime
        if min_dt == None or min_dt > deltatime:
            min_dt = deltatime
    return min_dt 


def binstr2hexstr(val):
    hexstr = ""
    curhexval = 0

    paddbits = (len(val)%4)
    if paddbits:
        val = ("0"*(4-paddbits)) + val

    for i in range(len(val)+1):
        if (((i % 4) == 0) and (i > 0)) or (i == len(val)):
            if curhexval <= -1:
                hexstr += "X"
            else:
                hexstr += str(hex(curhexval)[2]).lower()
                curhexval = 0
        if i == len(val):
            break
        b = val[i]
        curhexval = curhexval*2
        if b == '1':
            curhexval += 1
        if b == 'u' or b == 'z' or b == 'x':
            curhexval = -1

    return hexstr 

def binstr2decstr(val):
    hstr = binstr2hexstr(val)
    dval = 0
    for c in hstr:
        dval *= 16
        if c == "X":
            return "XX"
        for i, l in enumerate("0123456789abcdef"):
            if c == l:
                dval += i 
                break 
    return str(dval)

def render_wvf(wf_data, stop_data=True,zoom=1,sub_zoom=1,tick_spacing=20,show_tticks=True):
    global render_variables
    variables = wf_data.variables
    events = wf_data.events

    # For Windows OS (I guess)
    just_fix_windows_console()

    # Build ordered list of signal names
    signal_names = sorted(
        var["name"] for var in variables.values()
    )

    # Track current state of each signal
    current_values = {name: " " for name in signal_names}
    prev_values = {name: " " for name in signal_names}

    # Build waveform storage
    wave_lines = {name: [] for name in signal_names}
    wave_lens = {name: 0 for name in signal_names}

    # Sort events by time (safety)
    events = sorted(events, key=lambda e: e[0])

    waveform_len = 0

    # Find the longest name
    longest_name_len = 0
    for name in signal_names:
        if not name in render_variables:
            continue
        nlen = len(name)
        if nlen > longest_name_len:
            longest_name_len = nlen 

    # Limit the name length
    if longest_name_len >= 35:
        longest_name_len = 34
    # Make sure its not too short 
    if longest_name_len < 14:
        longest_name_len = 14

    # Calculate how long a time step is in characters 
    
    next_tick = timescale_scaler[zoom-1]

    wf_time_step = sub_zoom
    time_scale_sfx = g_timescales[zoom-1]

    curtime = 0
    eventidx = 0

    bad_data = False
    for time, changes in events:
        if bad_data == True:
            break

        curtime = time 

        if eventidx < len(events)-1:
            nexttime = events[eventidx+1][0]
        else:
            nexttime = curtime
        eventidx += 1

        deltatime = nexttime - curtime
        #print(deltatime, next_tick, wf_time_step)
        time_step = int((deltatime*tick_spacing)/(next_tick*wf_time_step))
        if time_step > 500:
            time_step = 500

        # Its too small!
        if time_step <= 0:
            break

        # Apply changes
        for value, var_info in changes:
            name = var_info["name"]
            current_values[name] = value

        # Snapshot state for all signals at this time
        for name in signal_names:
            if not name in render_variables:
                continue

            wave_lens[name] += time_step

            # Stop the simulation output from being too long???
            if stop_data:
                maxw = (max_waveform_width-(longest_name_len+6))
                if wave_lens[name] >= maxw:
                    bad_data = True
                    waveform_len = maxw 
                    wave_lens[name] -= time_step
                    time_step = maxw - wave_lens[name]
                    wave_lens[name] += time_step

            val = current_values[name]
            pval = prev_values[name]
            # Simple visual mapping
            if val == "1":
                wave_lines[name].append(Fore.GREEN)
                if pval == "0":
                    wave_lines[name].append("/")
                    wave_lines[name].append("▔"*(time_step-1))
                else:
                    wave_lines[name].append("▔"*time_step)
            elif val == "0":
                wave_lines[name].append(Fore.RED)
                if pval == "1":
                    wave_lines[name].append("\\")
                    wave_lines[name].append("▁"*(time_step-1))
                else:
                    wave_lines[name].append("▁"*time_step)
            elif val in ("x", "X"):
                wave_lines[name].append(Fore.BLUE)
                wave_lines[name].append("×"*time_step)
            elif val == "U":
                wave_lines[name].append(Fore.YELLOW)
                wave_lines[name].append("U"*time_step)
            elif len(val) > 1:
                    # TODO:
                    # bits need to be independent because 
                    # 01uxz is a valid set of bits... 
                show_bin = False
                show_hex = False
                if show_bin:
                    wave_lines[name].append(Fore.MAGENTA)
                    for iii in range(time_step):
                        if iii >= len(val):
                            wave_lines[name].append(Style.RESET_ALL)
                            wave_lines[name].append("."*(time_step-iii))
                            break
                        wave_lines[name].append(val[iii])
                elif show_hex:
                    hexval = binstr2hexstr(val)
                    hsw = int(len(hexval)/2)
                    hsw2 = round(len(hexval)/2)
                    wave_lines[name].append(Style.RESET_ALL)
                    wave_lines[name].append("."*(int(time_step/2)-hsw+1))
                    wave_lines[name].append(Fore.MAGENTA)
                    wave_lines[name].append(hexval)
                    wave_lines[name].append(Style.RESET_ALL)
                    wave_lines[name].append("."*(int(time_step/2)-hsw2))
                else:
                    decval = binstr2decstr(val)
                    wave_lines[name].append(Fore.MAGENTA)
                    wave_lines[name].append(decval)
                    wave_lines[name].append(Style.RESET_ALL)
                    wave_lines[name].append("."*(time_step-len(decval)))
            else:
                wave_lines[name].append(Fore.YELLOW)
                wave_lines[name].append("?"*time_step)
            wave_lines[name].append(Style.RESET_ALL)


            if bad_data == False:
                if waveform_len < wave_lens[name]:
                    waveform_len = wave_lens[name]

        # Store state for edge detection 
        for value, var_info in changes:
            name = var_info["name"]
            prev_values[name] = value

        

    # Render
    print("\nWaveform:\n")

    ticks_per_wf = int(waveform_len/tick_spacing)

    name_hz_txt = ("─"*(longest_name_len+2))
    topstr = "┌"+name_hz_txt+"┬"+("─"*(((ticks_per_wf+1)*tick_spacing)+1))+"┐"
    win_width = len(topstr)
    print(topstr)
    print("├"+name_hz_txt+"┤"+(" "*(((ticks_per_wf+1)*tick_spacing)+1))+"│")

    # Pad the waveform 
    maxpadw = win_width-(longest_name_len+6)
    for name in signal_names:
        if not name in render_variables:
            continue
        padw = (maxpadw - wave_lens[name])+1
        wave_lines[name].append("."*padw)

    waveform_len = maxpadw+1

    tbch = "─"
    if show_tticks:
        tbch = "┼"

    htick_spacing = int(tick_spacing/2)
    if htick_spacing >= 2:
        waveform_brk = tbch+(("─"*(htick_spacing-1))+tbch+("─"*(htick_spacing-1))+tbch)*int(ticks_per_wf)
    else:
        waveform_brk = tbch+(("─"*(tick_spacing-1))+tbch)*int(ticks_per_wf)
    waveform_brk += "─"*(tick_spacing)
    break_line = "├"+name_hz_txt+"┼"+waveform_brk+"┤"

    for name in signal_names:
        if not name in render_variables:
            continue
        waveform = "".join(wave_lines[name])
        name_len_ctdn = 3
        while (len(name) >= 35):
            name = ".".join(name.split(".")[-name_len_ctdn:])
            name_len_ctdn -= 1
            if name_len_ctdn == 0:
                break
        # Pad the name out 
        name = name + " "*(longest_name_len-len(name))
        print(f"│ {name} │{waveform}│")
        if not show_tticks == None:
            print(break_line)

    timeline = f"│ TimeScale: {time_scale_sfx}  "+(" "*(longest_name_len-14))+"│"
    for t in range(int(ticks_per_wf)+1):
        value = (t*wf_time_step)
        timeline += f"{value:<{tick_spacing}.2f}"
    timeline += (" "*(win_width-(len(timeline)+1)))+"│"
    print(timeline)
    print("└"+name_hz_txt+"┴"+("─"*waveform_len)+"┘")

    # Spacing between changes could be 7 characters for this formating:
    # |      |      | 
    # 00e-15 00e-15 00e-15

