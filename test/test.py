import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # 1. Reset
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # 2. STEP ONE: Load Weight '1' into the NPU
    dut._log.info("Loading Weight: 1")
    dut.ui_in.value = 0x11 # Shift 0x1 into data pins, ui[0]=1 (Enable)
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x06 # Set Cmd Valid (ui[1]) & Func ID 1 (ui[2])
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0    # Clear pins
    await ClockCycles(dut.clk, 2)

    # 3. STEP TWO: Shift in Activation '50' (0x32)
    dut._log.info("Shifting Activation: 50")
    dut.ui_in.value = 0x21 # Shift lower nibble 0x2
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x31 # Shift upper nibble 0x3
    await ClockCycles(dut.clk, 1)
    
    # 4. STEP THREE: Trigger Compute (Func ID 2)
    dut.ui_in.value = 0x0A # Set Cmd Valid (ui[1]) & Func ID 2 (ui[3])
    await ClockCycles(dut.clk, 2)

    # 5. Final Assertion: Result should be 50 * 1 = 50
    dut._log.info(f"NPU Output: {dut.uo_out.value}")
    assert dut.uo_out.value == 50
