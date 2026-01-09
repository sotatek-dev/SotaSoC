OUTPUT_ARCH( "riscv" )
ENTRY(rvtest_entry_point)

MEMORY
{
  FLASH (rx) : ORIGIN = 0x00000000, LENGTH = 0x01000000
  RAM (rw)   : ORIGIN = 0x01000000, LENGTH = 0x01000000
}

SECTIONS
{
  /* Code sections in FLASH */
  . = 0x00000000;
  .text.init : { *(.text.init) } > FLASH
  . = ALIGN(0x1000);
  .text : { *(.text) } > FLASH
  . = ALIGN(0x1000);
  
  /* Data sections in RAM */
  . = 0x01000000;
  .tohost : { *(.tohost) } > RAM
  . = ALIGN(0x1000);
  .data : { *(.data) } > RAM
  .data.string : { *(.data.string) } > RAM
  .bss : { *(.bss) } > RAM
  _end = .;
}

