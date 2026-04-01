import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

@cocotb.test()
async def test_project(dut):
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())
    dut.ena.value = 1; dut.ui_in.value = 0; dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    # 1. Load Weight '1'
    dut._log.info("Latching Weight...")
    dut.ui_in.value = 0x11 # Shift 1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x06 # Command: Load
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0    # Memory test: weight should stay latched!
    await ClockCycles(dut.clk, 2)

    # 2. Shift Activation '50'
    dut.ui_in.value = 0x21; await ClockCycles(dut.clk, 1) # Shift 2
    dut.ui_in.value = 0x31; await ClockCycles(dut.clk, 1) # Shift 3
    
    # 3. Compute (Wait for Pipeline)
    dut.ui_in.value = 0x0A # Command: Compute
    await ClockCycles(dut.clk, 4) # Give the silicon extra time to "breathe"
    
    dut._log.info(f"NPU Result: {dut.uo_out.value}")
    assert int(dut.uo_out.value) == 50
