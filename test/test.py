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

    # STEP 1: Load Weight '1' and Latch it
    dut._log.info("Latching Weight...")
    dut.ui_in.value = 0x11 # Shift 1 into data, ui[0]=1 (Enable)
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x06 # cmd_valid=1, func_id=1
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0    # Let go! Weight stays in silicon memory
    await ClockCycles(dut.clk, 2)

    # STEP 2: Shift Activation '50' (0x32)
    dut.ui_in.value = 0x21; await ClockCycles(dut.clk, 1) # Shift 0x2
    dut.ui_in.value = 0x31; await ClockCycles(dut.clk, 1) # Shift 0x3
    
    # STEP 3: Compute and Wait for Result
    dut.ui_in.value = 0x0A # cmd_valid=1, func_id=2
    await ClockCycles(dut.clk, 5) # Time for math to propagate
    
    dut._log.info(f"Final NPU Result: {dut.uo_out.value}")
    assert int(dut.uo_out.value) == 50
