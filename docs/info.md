# Lacesse Fikra NPU

## How it works
This project is a 2x2 Systolic Array designed for ternary weight AI inference. It utilizes a serial shift register to load 32-bit data through an 8-bit physical interface. Once loaded, the NPU performs multiply-accumulate operations using ternary weights (-1, 0, 1), which significantly reduces silicon area by eliminating traditional multipliers.

## How to test
1. Reset the chip using the `rst_n` pin.
2. Set `Shift Enable` (ui[0]) to high.
3. Pulse 8-bit data chunks through `Data` (ui[4:7]) to fill the 32-bit internal register.
4. Set `Cmd Valid` (ui[1]) to high and select a `Func ID` (ui[2:3]) to load weights or trigger a calculation.
5. Observe the 8-bit result on the output pins (uo[0:7]).

## External hardware
No external hardware is required other than standard input switches and output LEDs.
