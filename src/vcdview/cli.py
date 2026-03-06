from .__init__ import __version__
from .parser import parse_vcd 
from .render import *

app_running = True

g_wf_data = None

def print_help():
    entries = []
    
    # Sort the entries alphabetically 

    for command in cli_commands:
        cmds = command[0]
        args = command[1]
        info = command[2]

        help_line = ", ".join(cmds)
        if args:
            help_line += " " + " ".join(args)

        entries.append((help_line, info))

    # Compute maximum command width
    max_width = max(len(entry[0]) for entry in entries)

    for help_line, info in entries:
        print(f"\t{help_line.ljust(max_width)}  -- {info}")

def clear_terminal():
    print("\033[2J\033[H", end="")

def quit_app():
    global app_running
    app_running = False


l_zoom_tframe = 1
l_zoom_width = 10
l_show_tticks = True

def enable_time_ticks():
    global l_show_tticks
    l_show_tticks = True 
def disable_time_ticks():
    global l_show_tticks
    l_show_tticks = False
def compact_mode():
    global l_show_tticks
    l_show_tticks = None

def print_wave():
    if l_zoom_tframe >= 1:
        zval = int(math.log(l_zoom_tframe,1000))
        szval = 1#(1000+abs(l_zoom_tframe-(math.pow(1000,zval))))/1000
        zval += 1
    else:
        zval = 1
        szval = l_zoom_tframe
    print(zval, szval, l_zoom_tframe)
    render_wvf(g_wf_data,
               stop_data=True,
               zoom=zval,
               sub_zoom=szval,
               tick_spacing=l_zoom_width,
               show_tticks=l_show_tticks)

def cprint_wave():
    render_wvf_curses(g_wf_data)

def load_waveform(fname):
    global g_wf_data
    wf = parse_vcd(fname)
    if wf == None:
        print(f"Error loading {fname}")
        return 
    render_variables.clear()
    g_wf_data = wf

def reload_waveform():
    cur_fname = g_wf_data.get_filename()
    load_waveform(cur_fname)

def list_variables():
    global g_wf_data 
    print(f"0] all")
    for i, v in enumerate(g_wf_data.variables, start=1):
        var = g_wf_data.variables[v]
        vname = var["name"]
        for k in render_variables:
            if k == vname:
                vname += " ✓"
        print(f"{i}] {vname}")

def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def add_variable1(var):
    global render_variables
    if var == "all" or var == "0":
        render_variables.clear()
        for v in g_wf_data.variables:
            vr = g_wf_data.variables[v]
            render_variables.append(vr["name"])
        return
    # Allow number identification
    if is_int(var):
        for i, v in enumerate(g_wf_data.variables, start=1):
            if i != int(var):
                continue
            vr = g_wf_data.variables[v]
            render_variables.append(vr["name"])
            return
        print("Invalid variable index!")
        return 
    # Make sure its a valid name
    if not var in render_variables:
        print("Invalid variable name!")
        return
    render_variables.append(var)

def add_variable(var):
    vars = var.split(",")
    for v in vars:
        add_variable1(v)


def rm_variable1(var):
    global render_variables
    if var == "all" or var == "0":
        render_variables.clear()
        return
    # Allow number identification
    if is_int(var):
        for i, v in enumerate(g_wf_data.variables, start=1):
            if i != int(var):
                continue
            var = g_wf_data.variables[v]["name"]
            if var in render_variables:
                render_variables.remove(var)
            return
        print("Invalid variable index!")
        return 
    # Make sure its a valid name
    if not var in render_variables:
        print("Invalid variable name!")
        return
    if var in render_variables:
        render_variables.remove(var)

def rm_variable(var):
    vars = var.split(",")
    for v in vars:
        rm_variable1(v)

def set_zoom(zvalue):
    global g_timescales, l_zoom_tframe
    if zvalue == "+":
        l_zoom_tframe += 1000
        return 
    if zvalue == "-":
        l_zoom_tframe -= 1000
        if l_zoom_tframe < 0:
            l_zoom_tframe = 0.1
        return 
    if zvalue[0] == '+':
        val = zvalue[1:]
        if is_int(val):
            l_zoom_tframe += int(val)
        return 
    if zvalue[0] == '-':
        val = zvalue[1:]
        if is_int(val):
            l_zoom_tframe -= int(val)
        if l_zoom_tframe < 0:
            l_zoom_tframe = 0.1
        return 
    if zvalue == "fit":
        dt = get_wf_tdelta(g_wf_data)
        l_zoom_tframe = dt*2
        return
    #if len(events) > 1:
    #    next_tick = magnitude(events[1][0])
    #    return
    if zvalue in scale_to_fs:
        l_zoom_tframe = scale_to_fs[zvalue]
        print(f"Set zoom to: {l_zoom_tframe}")
        return
    if (zvalue+"s") in scale_to_fs:
        l_zoom_tframe = scale_to_fs[zvalue+"s"]
        print(f"Set zoom to: {l_zoom_tframe}")
        return
    print("Invalid zoom command!")

def set_time_tick(val):
    global l_zoom_width
    if not is_int(val):
        print("Requires an integer value!")
        return
    val = int(val)
    if val < 10:
        print("Invalid integer value! Must be > 10")
        return
    if not (val%5)==0:
        print("Invalid integer value! Must be divisable by 5")
        return
    l_zoom_width = val


cli_commands = [
    [["h","help"],[], "Gives commands that can be used.", print_help],
    [["q","quit","exit"],[], "Quits the application.", quit_app],
    [["p","print"],[], "Prints the waveform to the console.", print_wave],
    [["c","clear"],[], "Clears the console.", clear_terminal],
    [["fr"],[], "Reloads the waveform from file.", reload_waveform],
    [["fl","f"],["<waveform.vcd>"], "Loads a waveform from a file.", load_waveform],
    [["l", "ls"],[], "Lists all variables available to view.", list_variables],
    [["wa", "add", "a"],["<variable.name>"], "Adds a variable to the waveform.", add_variable],
    [["wr", "rm", "r"],["<variable.name>"], "Removes a variable from the waveform.", rm_variable],
    [["wv", "view"],[], "Opens a interactive waveform viewer.", cprint_wave],
    [["z", "wz", "zoom"],["<time_scale>"], "Sets the waveform zoom. (Use: -<value>,+<value>,fit,fs,ps,ns,us,ms,s)", set_zoom],
    [["zf", "wzf"],[], "Same as `zoom fit`.", set_zoom],
    [["zw", "tspace"],["<tick_spacing>"], "Sets how far apart each time tick is.", set_time_tick],
    [["t","ticks"],[], "Enables time ticks on waveform.", enable_time_ticks],
    [["n","noticks", "nticks"],[], "Disables time ticks on waveform.", disable_time_ticks],
    [["comp"],[], "Compacts the waveform.", compact_mode],
    #[["wg", "group", "g"],["<group_name>","<variable.name1,variable.name2,variable.name3>"], "Adds a variable to the waveform.", group_variables],
]

def cli_run(wf_data):
    global app_running, g_wf_data
    
    if wf_data == None:
        print("No valid waveform data!")
    g_wf_data = wf_data 

    print(f"] vcdview (ver {__version__})")
    print("] type `h` for help")

    cli_commands.sort()

    while app_running:
        print("")
        try:
            usr_in = input(">")
        except:
            print("")
            app_running = False
            return 
        if len(usr_in) == 0:
            continue
        usr_list = usr_in.strip().split()

        cmd_valid = False

        for command in cli_commands:
            cmds = command[0]
            args = command[1]
            fun = command[3]
            for c in cmds:
                if usr_list[0] == c:
                    if len(usr_list) < len(args)+1:
                        print("Use: " + cmds[0] + " " + " ".join(args))
                        break
                    if len(args) == 0:
                        fun()
                        cmd_valid = True
                        break
                    if len(args) == 1:
                        fun(usr_list[1])
                        cmd_valid = True
                        break
                if cmd_valid == True:
                    break
            if cmd_valid == True:
                break



