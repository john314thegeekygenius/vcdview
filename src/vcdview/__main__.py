import sys 
from .parser import parse_vcd 
from .render import render_wvf
from .cli import cli_run

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 -m vcdview <file.vcd>")
        sys.exit(1)

    wavedata = parse_vcd(sys.argv[1])
    if wavedata == None:
        sys.exit(1)
    
    cli_run(wavedata)
    print("Thank you for using vcdview!")

if __name__ == "__main__":
    main()

