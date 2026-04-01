import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 10 us (100 KHz)
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # 1. Reset the chip
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # 2. Shift in a value (Let's load '50' into the NPU)
    # 50 in hex is 0x32. We'll shift it into the 4-bit data pins (ui_in[4:7])
    dut._log.info("Shifting in data: 50")
    
    # Send lower nibble (0x2)
    dut.ui_in.value = 0x21 # ui[4:7]=2, ui[0]=1 (Shift Enable)
    await ClockCycles(dut.clk, 1)
    
    # Send upper nibble (0x3)
    dut.ui_in.value = 0x31 # ui[4:7]=3, ui[0]=1 (Shift Enable)
    await ClockCycles(dut.clk, 1)
    
    dut.ui_in.value = 0  # Stop shifting
    await ClockCycles(dut.clk, 1)

    # 3. Trigger NPU Command (Func ID 2: Push Activations/Output)
    dut._log.info("Triggering NPU output command")
    dut.ui_in.value = 0x0A # ui[1]=1 (Cmd Valid), ui[2:3]=2 (Func ID 2)
    await ClockCycles(dut.clk, 1)
    
    # 4. Check the result
    dut._log.info(f"Checking output: {dut.uo_out.value}")
    assert dut.uo_out.value == 50
