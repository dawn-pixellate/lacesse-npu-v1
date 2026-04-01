import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # 1. Reset the chip
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # 2. Load Weight '1'
    dut._log.info("Loading Weight: 1")
    dut.ui_in.value = 0x11 # Shift 0x1 into data, ui[0]=1 (Enable)
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x06 # cmd_valid=1, func_id=1
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 2)

    # 3. Shift in Activation '50' (0x32)
    dut._log.info("Shifting Activation: 50")
    dut.ui_in.value = 0x21 # Shift nibble 0x2
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x31 # Shift nibble 0x3
    await ClockCycles(dut.clk, 1)
    
    # 4. TRIGGER & WAIT: Handle the 1-cycle pipeline delay
    dut._log.info("Triggering Compute...")
    dut.ui_in.value = 0x0A # cmd_valid=1, func_id=2
    await ClockCycles(dut.clk, 2) # Wait for NPU -> CFU propagation
    
    # Disable command to hold the result
    dut.ui_in.value = 0 
    await ClockCycles(dut.clk, 1)

    # 5. Final Assertion
    dut._log.info(f"NPU Output Captured: {dut.uo_out.value}")
    assert dut.uo_out.value == 50
