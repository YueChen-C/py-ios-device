from unicorn import *
from unicorn.x86_const import *
import re
from tools.kperfdata.kpmsg import messages
import struct

instruction_table = {
}

function_table = {
}

with open('kperfdata.s') as fp:
    kperfdata_list = fp.read().split('\n\n')


def load_assembly(txt):
    ptn = re.compile(r'\s+(?P<addr>[0-9a-f]+):\s*(?P<code>(?: [0-9a-f][0-9a-f])+)  \s*(?P<inst>.*)')
    lines = list(map(lambda x: x.rstrip(), filter(None, txt.split('\n'))))
    name = lines[0].strip(':')
    data = []
    for line in lines[1:]:
        matched = ptn.match(line)
        if matched:
            addr = int(matched.groupdict()['addr'], 16)
            if name not in function_table:
                function_table[name] = addr
            instruction_table[addr] = matched.groupdict()['inst']
            data.append((addr, bytes(bytearray.fromhex(matched.groupdict()['code']))))
        else:
            print(f'line: {line} not matched')
    return name, data


functions = [load_assembly(i) for i in kperfdata_list]


def hook_unmapped(uc, typ, address, size, value, user_data):
    print("oops~~", uc, typ, address, size, value, user_data, hex(uc.reg_read(UC_X86_REG_RIP)))
    return True


g_verbose = False


def hook_block(uc, addr, size, user_data):
    if addr in external_functions:
        external_functions[addr](uc)


def hook_interupt(uc, num, user_data):
    print("interupt!", num)
    if num == 3:
        # uc.reg_write(UC_X86_REG_RIP, 0x0)
        # return_rax(uc, 999)
        # return False
        pass


try:
    mu = Uc(UC_ARCH_X86, UC_MODE_64)
    # map 2MB memory for this emulation
    mu.mem_map(0x1000, 2 * 1024 * 1024)
    mu.mem_write(0x1000, b'\xcc' * (2 * 1024 * 1024 - 0x1000))
    for name, data in functions:
        for addr, code in data:
            # print(f'{addr:x} {code}')
            mu.mem_write(addr, code)
    STACK_BASE = 2 * 1024 * 1024
    mu.hook_add(UC_HOOK_CODE, hook_block)
except UcError as e:
    print("ERROR: %s" % e)

print("---", function_table)


def return_rax(uc, rax):
    uc.reg_write(UC_X86_REG_RAX, rax)
    uc.reg_write(UC_X86_REG_RIP, 0x8888)


def return_none(uc):
    uc.reg_write(UC_X86_REG_RIP, 0x8888)


class MM:

    def __init__(self, mu):
        self.mu = mu
        self.min_addr = 4 * 1024 * 1024
        self.allocs = []

    def _get_available_addr(self):
        if self.allocs:
            mx = max(self.allocs)
            return mx[0] + mx[1]
        return self.min_addr

    def alloc(self, n):
        a = self._get_available_addr()
        n = (n + 4095) // 4096 * 4096
        # print(a, n)
        self.mu.mem_map(a, n)
        self.allocs.append((a, n))
        # print(f"calloc({a}, {n})")
        return a

    def free(self, ptr):
        found = None
        for i in range(len(self.allocs)):
            if self.allocs[i][0] == ptr:
                found = i
                break
        if found is not None:
            # print(f"free{self.allocs[i]}")
            self.mu.mem_unmap(self.allocs[i][0], self.allocs[i][1])
            self.allocs.pop(i)


mm = MM(mu)


def my_calloc(uc):
    size = uc.reg_read(UC_X86_REG_RDI)
    count = uc.reg_read(UC_X86_REG_RSI)
    return_rax(uc, mm.alloc(size * count))


def my_free(uc):
    ptr = uc.reg_read(UC_X86_REG_RDI)
    mm.free(ptr)
    return_none(uc)


def my_malloc(uc):
    size = uc.reg_read(UC_X86_REG_RDI)
    return_rax(uc, mm.alloc(size))


external_functions = {
    0x77b2: my_calloc,
    0x77ca: my_free,
    0x77ee: my_malloc
}


def invoke(name, *arg):
    # setup stack
    mu.reg_write(UC_X86_REG_RSP, STACK_BASE - 8)
    mu.mem_write(STACK_BASE - 8, b'\x99\x99' + b'\x00' * 6)
    # mu.reg_write(UC_X86_REG_RIP, function_table['_kpdecode_cursor_create'])
    # mu.hook_add(UC_HOOK_INTR, hook_interupt)
    # mu.hook_add(UC_HOOK_MEM_UNMAPPED, hook_unmapped);
    if len(arg) > 0:
        mu.reg_write(UC_X86_REG_RDI, arg[0])
    if len(arg) > 1:
        mu.reg_write(UC_X86_REG_RSI, arg[1])
    if len(arg) > 2:
        mu.reg_write(UC_X86_REG_RDX, arg[2])
    if len(arg) > 3:
        mu.reg_write(UC_X86_REG_RCX, arg[3])
    if len(arg) > 4:
        mu.reg_write(UC_X86_REG_R8, arg[4])
    if len(arg) > 5:
        mu.reg_write(UC_X86_REG_R9, arg[5])
    if len(arg) > 4:
        raise NotImplementedError()

    try:
        # emulate machine code in infinite time
        mu.emu_start(function_table[name], 0x9999)
    except UcError as e:
        print("ERROR: %s" % e)
        print(f"rip = {mu.reg_read(UC_X86_REG_RIP):08x}")
    return mu.reg_read(UC_X86_REG_RAX)


def kpdecode_cursor_create():
    return invoke('_kpdecode_cursor_create')


def kpdecode_cursor_setchunk(cursor, buf, length):
    return invoke('_kpdecode_cursor_setchunk', cursor, buf, length)


def kpdecode_cursor_next_record(cursor, p_record):
    return invoke('_kpdecode_cursor_next_record', cursor, p_record)


def kpdecode_record_free(record):
    return invoke('_kpdecode_record_free', record)


def kpdecode_cursor_clearchunk(cursor):
    return invoke('_kpdecode_cursor_clearchunk', cursor)


def kpdecode_cursor_free(cursor):
    invoke('_kpdecode_cursor_free', cursor)


def kpdecode_cursor_set_option(cursor, o1, o2):
    return invoke('_kpdecode_cursor_set_option', cursor, o1, o2)


if __name__ == '__main__':
    p = kpdecode_cursor_create()
    kpdecode_cursor_set_option(p, 0, 1)
    code_num = 0
    for msg in messages[:]:
        _list = []
        buf = mm.alloc(len(msg))
        mu.mem_write(buf, msg)
        p_record = mm.alloc(8)
        kpdecode_cursor_setchunk(p, buf, len(msg))
        while not kpdecode_cursor_next_record(p, p_record):
            v, = struct.unpack('<Q', mu.mem_read(p_record, 8))
            time, = struct.unpack('Q', mu.mem_read(v + 0x8, 8))
            code, = struct.unpack('<Q', mu.mem_read(v + 0x30, 8))
            args = struct.unpack('<QQQ', mu.mem_read(v + 0x40, 24))
            if f'{code:08x}' == '31800318':
                print(mu.mem_read(v + 0x8, 8), mu.mem_read(v + 0x30, 8),args)
                code_num += 1
            kpdecode_record_free(v)
        g_verbose = False
        kpdecode_cursor_clearchunk(p)
    kpdecode_cursor_free(p)
    print('code_num', code_num)
