import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

async def reset(dut):
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

async def load_weights(dut, w00, w01, w10, w11):
    """
    Pack weights into 32-bit word:
      w00 in bits[1:0], w01 in bits[9:8], w10 in bits[17:16], w11 in bits[25:24]
    Shift 8 nibbles MSB-first so LSB lands at shift_reg[0].
    Fire func_id=1 (0x06).
    """
    word = ((w11 & 0xFF) << 24) | ((w10 & 0xFF) << 16) | ((w01 & 0xFF) << 8) | (w00 & 0xFF)
    for i in range(7, -1, -1):
        nibble = (word >> (i * 4)) & 0xF
        dut.ui_in.value = 0x01 | (nibble << 4)
        await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x06   # cmd_valid=1, func_id=01
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)

async def compute(dut, row0, row1):
    """
    Shift row1 then row0 so shift_reg[7:0]=row0, shift_reg[15:8]=row1.
    Fire func_id=2 (0x0A).
    Wait 3 cycles for acc + result_reg to settle.
    """
    nibbles = [
        (row1 >> 4) & 0xF, row1 & 0xF,
        (row0 >> 4) & 0xF, row0 & 0xF,
    ]
    for n in nibbles:
        dut.ui_in.value = 0x01 | (n << 4)
        await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x0A   # cmd_valid=1, func_id=10
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 3)

async def read_out(dut, sel):
    """Shift sel into shift_reg[1:0], fire func_id=3 (0x0E), return uo_out."""
    dut.ui_in.value = 0x01 | (sel << 4)
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0x0E   # cmd_valid=1, func_id=11
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value = 0x00
    await ClockCycles(dut.clk, 2)
    return int(dut.uo_out.value)


@cocotb.test()
async def test_weight_plus1(dut):
    """w00=+1, row0=50 → out00 == 50"""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())
    await reset(dut)
    await load_weights(dut, w00=1, w01=0, w10=0, w11=0)
    await compute(dut, row0=50, row1=0)
    result = int(dut.uo_out.value)
    assert result == 50, f"Expected 50, got {result}"
    dut._log.info(f"PASS: out00={result}")


@cocotb.test()
async def test_weight_minus1(dut):
    """w00=-1, row0=50 → out00 == lower 8 bits of -50"""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())
    await reset(dut)
    await load_weights(dut, w00=-1, w01=0, w10=0, w11=0)
    await compute(dut, row0=50, row1=0)
    result = int(dut.uo_out.value)
    expected = (-50) & 0xFF
    assert result == expected, f"Expected {expected} (-50 as byte), got {result}"
    dut._log.info(f"PASS: out00={result} == -50")


@cocotb.test()
async def test_weight_zero(dut):
    """w00=0, row0=99 → out00 == 0 (ternary zero, no accumulation)"""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())
    await reset(dut)
    await load_weights(dut, w00=0, w01=0, w10=0, w11=0)
    await compute(dut, row0=99, row1=0)
    result = int(dut.uo_out.value)
    assert result == 0, f"Expected 0, got {result}"
    dut._log.info(f"PASS: out00={result}")


@cocotb.test()
async def test_accumulation(dut):
    """w00=+1, row0=10, 3 compute cycles → out00 == 30"""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())
    await reset(dut)
    await load_weights(dut, w00=1, w01=0, w10=0, w11=0)
    await compute(dut, row0=10, row1=0)
    await compute(dut, row0=10, row1=0)
    await compute(dut, row0=10, row1=0)
    result = int(dut.uo_out.value)
    assert result == 30, f"Expected 30, got {result}"
    dut._log.info(f"PASS: out00={result}")


@cocotb.test()
async def test_row1_mac(dut):
    """w10=+1, row1=77 → read_out(sel=2) == 77"""
    cocotb.start_soon(Clock(dut.clk, 10, units="us").start())
    await reset(dut)
    await load_weights(dut, w00=0, w01=0, w10=1, w11=0)
    await compute(dut, row0=0, row1=77)
    result = await read_out(dut, sel=2)
    assert result == 77, f"Expected 77, got {result}"
    dut._log.info(f"PASS: out10={result}")
