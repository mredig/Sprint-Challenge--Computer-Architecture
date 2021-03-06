"""CPU functionality."""

from ls8Instructions import *
import sys
import time
from KBHit import KBHit

IM = 5
IS = 6
SP = 7
KEY_PRESSED = 0xF4
class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = [0] * 256
        self.register = [0] * 8
        self.register[7] = 0xF4

        self.pc = 0
        self.fl = 0
        self.setupBranchtable()
        self.setupALUBranchtable()
        self.lastFire = time.time()
        self.interruptsEnabled = True

        self.keyboardMonitor = KBHit()

    def setupBranchtable(self):
        self.branchtable = {}

        self.branchtable[MUL] = self.handleMUL
        self.branchtable[CMP] = self.handleCMP
        self.branchtable[ADD] = self.handleADD
        self.branchtable[AND] = self.handleAND
        self.branchtable[OR] = self.handleOR
        self.branchtable[XOR] = self.handleXOR
        self.branchtable[NOT] = self.handleNOT
        self.branchtable[SHL] = self.handleSHL
        self.branchtable[SHR] = self.handleSHR
        self.branchtable[MOD] = self.handleMOD
        self.branchtable[INC] = self.handleINC
        self.branchtable[DEC] = self.handleDEC

        self.branchtable[LDI] = self.handleLDI
        self.branchtable[PRN] = self.handlePRN
        self.branchtable[HLT] = self.handleHLT
        self.branchtable[PUSH] = self.handlePUSH
        self.branchtable[POP] = self.handlePOP
        self.branchtable[CALL] = self.handleCALL
        self.branchtable[RET] = self.handleRET
        self.branchtable[ST] = self.handleST
        self.branchtable[JMP] = self.handleJMP
        self.branchtable[PRA] = self.handlePRA
        self.branchtable[IRET] = self.handleIRET
        self.branchtable[LD] = self.handleLD
        self.branchtable[JEQ] = self.handleJEQ
        self.branchtable[JNE] = self.handleJNE

    def setupALUBranchtable(self):
        self.aluTable = {}

        self.aluTable[MUL] = self.handleAluMUL
        self.aluTable[ADD] = self.handleAluADD
        self.aluTable[CMP] = self.handleAluCMP
        self.aluTable[AND] = self.handleAluAND
        self.aluTable[OR] = self.handleAluOR
        self.aluTable[XOR] = self.handleAluXOR
        self.aluTable[NOT] = self.handleAluNOT
        self.aluTable[SHL] = self.handleAluSHL
        self.aluTable[SHR] = self.handleAluSHR
        self.aluTable[MOD] = self.handleAluMOD
        self.aluTable[INC] = self.handleAluINC
        self.aluTable[DEC] = self.handleAluDEC

    def load(self, program):
        """Load a program into memory."""

        address = 0

        for instruction in program:
            self.ram[address] = instruction
            address += 1

    def getStackIndex(self):
        return self.register[7]

    def setStackIndex(self, index):
        self.register[7] = index

    def ramRead(self, mar):
        return self.ram[mar]

    def ramWrite(self, mdr, mar):
        """
        mar is the address
        mdr is the data to store at that address
        """
        self.ram[mar] = mdr

    def alu(self, op, operandA, operandB):
        """ALU operations."""

        opMethod = self.aluTable.get(op, None)
        if opMethod is not None:
            # every opMethod needs to take two parameters, even if it only USES one
            opMethod(operandA, operandB)
        else:
            raise Exception("Unsupported ALU operation")

    def handleAluADD(self, operandA, operandB):
        self.register[operandA] += self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluMUL(self, operandA, operandB):
        self.register[operandA] *= self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluCMP(self, operandA, operandB):
        if self.register[operandA] < self.register[operandB]:
            # L flag 0b0100
            self.fl |= 0b0100
        else:
            self.fl &= 0b11111011
        if self.register[operandA] > self.register[operandB]:
            # G flag 0b0010
            self.fl |= 0b0010
        else:
            self.fl &= 0b11111101
        if self.register[operandA] == self.register[operandB]:
            # equal flag 0b0001
            self.fl |= 0b0001
        else:
            self.fl &= 0b11111110

    def handleAluAND(self, operandA, operandB):
        self.register[operandA] &= self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluOR(self, operandA, operandB):
        self.register[operandA] |= self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluXOR(self, operandA, operandB):
        self.register[operandA] ^= self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluNOT(self, operandA, operandB):
        self.register[operandA] = ~self.register[operandA]
        self.register[operandA] &= 0xFF

    def handleAluSHL(self, operandA, operandB):
        self.register[operandA] = self.register[operandA] << self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluSHR(self, operandA, operandB):
        self.register[operandA] = self.register[operandA] >> self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluMOD(self, operandA, operandB):
        if self.register[operandB] == 0:
            print("Cannot divide (or MOD) by 0!")
            sys.exit(1)
        self.register[operandA] = self.register[operandA] % self.register[operandB]
        self.register[operandA] &= 0xFF

    def handleAluINC(self, operandA, operandB):
        self.register[operandA] += 1
        self.register[operandA] &= 0xFF

    def handleAluDEC(self, operandA, operandB):
        self.register[operandA] -= 1
        self.register[operandA] &= 0xFF

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE (pc): %02X | (values at pc, pc+1, pc+2) %02X %02X %02X | REGISTERS: " % (
            self.pc,
            #self.fl,
            #self.ie,
            self.ramRead(self.pc),
            self.ramRead(self.pc + 1),
            self.ramRead(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.register[i], end='')

        print()

    def handleLDI(self):
        operandIndex = self.ramRead(self.pc + 1)
        operand = self.ramRead(self.pc + 2)
        self.register[operandIndex] = operand

    def handlePRN(self):
        operandIndex = self.ramRead(self.pc + 1)
        operand = self.register[operandIndex]
        print(operand)

    def handleHLT(self):
        sys.exit(0)

    def handleMUL(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(MUL, operandAIndex, operandBIndex)

    def handleADD(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(ADD, operandAIndex, operandBIndex)

    def handleAND(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(AND, operandAIndex, operandBIndex)

    def handleOR(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(OR, operandAIndex, operandBIndex)

    def handleXOR(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(XOR, operandAIndex, operandBIndex)

    def handleNOT(self):
        operand = self.ram[self.pc + 1]
        self.alu(NOT, operand, 0)

    def handleSHL(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(SHL, operandAIndex, operandBIndex)

    def handleSHR(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(SHR, operandAIndex, operandBIndex)

    def handleMOD(self):
        operandAIndex = self.ram[self.pc + 1]
        operandBIndex = self.ram[self.pc + 2]
        self.alu(MOD, operandAIndex, operandBIndex)

    def handlePUSH(self):
        operandIndex = self.ramRead(self.pc + 1)
        operand = self.register[operandIndex]
        self.pushValueOnStack(operand)

    def pushValueOnStack(self, operand):
        stackPointer = self.getStackIndex() - 1
        self.setStackIndex(stackPointer)
        self.ramWrite(operand, stackPointer)

    def handlePOP(self):
        operand = self.popValueFromStack()
        operandIndex = self.ramRead(self.pc + 1)
        self.register[operandIndex] = operand

    def popValueFromStack(self):
        stackPointer = self.getStackIndex()
        self.setStackIndex(stackPointer + 1)
        return self.ramRead(stackPointer)

    def handleCALL(self):
        operandIndex = self.ramRead(self.pc + 1)
        operand = self.register[operandIndex]
        # save address of next *INSTRUCTION* in stack
        self.pushValueOnStack(self.pc + 2)
        self.pc = operand

    def handleRET(self):
        operand = self.popValueFromStack()
        self.pc = operand

    def handleST(self):
        operandA = self.ramRead(self.pc + 1)
        operandB = self.ramRead(self.pc + 2)
        self.ramWrite(self.register[operandB], self.register[operandA])

    def handleJMP(self):
        operand = self.ramRead(self.pc + 1)
        self.pc = self.register[operand]

    def handlePRA(self):
        operand = self.ramRead(self.pc + 1)
        value = self.register[operand]
        print(chr(value), end="")

    def handleIRET(self):
        self.register[6] = self.popValueFromStack()
        self.register[5] = self.popValueFromStack()
        self.register[4] = self.popValueFromStack()
        self.register[3] = self.popValueFromStack()
        self.register[2] = self.popValueFromStack()
        self.register[1] = self.popValueFromStack()
        self.register[0] = self.popValueFromStack()
        self.fl = self.popValueFromStack()
        self.pc = self.popValueFromStack()
        self.interruptsEnabled = True

    def handleLD(self):
        operandA = self.ramRead(self.pc + 1)
        operandB = self.ramRead(self.pc + 2)
        self.register[operandA] = self.ramRead(self.register[operandB])

    def handleCMP(self):
        operandA = self.ramRead(self.pc + 1)
        operandB = self.ramRead(self.pc + 2)
        self.alu(CMP, operandA, operandB)

    def handleINC(self):
        operand = self.ramRead(self.pc + 1)
        self.alu(INC, operand, 0)

    def handleDEC(self):
        operand = self.ramRead(self.pc + 1)
        self.alu(DEC, operand, 0)

    def handleJEQ(self):
        operand = self.ramRead(self.pc + 1)
        if (self.fl >> 0) & 0b1 == 1:
            self.pc = self.register[operand]
        else:
            self.pc += 2

    def handleJNE(self):
        operand = self.ramRead(self.pc + 1)
        if (self.fl >> 0) & 0b1 == 0:
            self.pc = self.register[operand]
        else:
            self.pc += 2

    def __interuptTimer(self):
        currentTime = time.time()
        if currentTime > self.lastFire + 1:
            self.lastFire = currentTime
            self.register[IS] |= 0b1

    def __checkKeyboardInterrupts(self):
        if self.keyboardMonitor.kbhit():
            keyPress = self.keyboardMonitor.getch()
            value = ord(keyPress)
            self.ramWrite(value, KEY_PRESSED)
            self.register[IS] |= 0b10

    def run(self):
        """Run the CPU."""

        while True:
            # poll interrupts
            self.__interuptTimer()
            self.__checkKeyboardInterrupts()

            # check for interrupts
            if self.interruptsEnabled:
                maskedInterrupts = self.register[IM] & self.register[IS]
                for i in range(8):
                    interrupt = ((maskedInterrupts >> i) & 1) == 1
                    if interrupt:
                        self.interruptsEnabled = False
                        # clear only the bit of the current interrupt
                        self.register[IS] &= 0xFF ^ (1 << i)
                        self.pushValueOnStack(self.pc)
                        self.pushValueOnStack(self.fl)
                        self.pushValueOnStack(self.register[0])
                        self.pushValueOnStack(self.register[1])
                        self.pushValueOnStack(self.register[2])
                        self.pushValueOnStack(self.register[3])
                        self.pushValueOnStack(self.register[4])
                        self.pushValueOnStack(self.register[5])
                        self.pushValueOnStack(self.register[6])
                        newAddress = self.ramRead(0xF8 + i)
                        self.pc = newAddress
                        break

            instructionRegister = self.ram[self.pc]
            instructionMethod = self.branchtable.get(instructionRegister, None)
            # self.trace()
            if instructionMethod is not None:
                instructionMethod()
            else:
                print(f"Instruction not recognized: {instructionRegister}")
                exit(1)

            # check to see if the PC is explicitly set by the instruction. if not, increment the PC by the number of arguments + 1
            if ((instructionRegister >> 4) & 0b1) != 1:
                self.pc += ((instructionRegister & 0xC0) >> 6) + 1
            # print(f"about to execute {self.pc}")
