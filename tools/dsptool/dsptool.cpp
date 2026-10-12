// dsptool: assemble DSP56300 lines and run code snippets on the dsp56kEmu interpreter.
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include <map>
#include <iostream>
#include <fstream>
#include <sstream>
#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif
#include "dsp56kEmu/dsp.h"
#include "dsp56kEmu/memory.h"
#include "dsp56kEmu/peripherals.h"
#include "dsp56kEmu/assembler.h"
#include "dsp56kEmu/disasm.h"
#include "dsp56kEmu/opcodes.h"
using namespace dsp56k;

static int cmdAsm() {
    Assembler a; std::string line;
    while (std::getline(std::cin, line)) {
        if (line.empty()) { std::cout << "\n"; continue; }
        auto r = a.assemble(line.c_str());
        if (!r.success()) { std::cout << "ERR " << (int)r.error << "\n"; continue; }
        std::cout << r.wordCount;
        for (uint32_t i = 0; i < r.wordCount; ++i) { char b[16]; snprintf(b, 16, " %06x", r.word[i]); std::cout << b; }
        std::cout << "\n";
    }
    return 0;
}

static TWord g_curPC = 0; static FILE* g_watchOut = nullptr; static uint64_t g_watchMax = 200000;
static void watchCb(EMemArea a, TWord addr, bool w, TWord v) {
    if (!g_watchOut || !g_watchMax) return; --g_watchMax;
    fprintf(g_watchOut, "%06x %c:%06x %c %06x\n", g_curPC, a == MemArea_X ? 'X' : a == MemArea_Y ? 'Y' : 'P', addr, w ? 'W' : 'R', v);
}

// run <script>: commands
//  P addr hexwords...   X addr ...   Y addr ...  (set memory)
//  PC addr  STOP addr  MAX n  REG name val
//  RUN   DUMPX addr n   DUMPY addr n  WATCHX lo hi (report writes)  -- watch via compare snapshots
static int cmdRun(const char* script) {
    PeripheralsNop px, py;
    static DefaultMemoryValidator mv; Memory mem(mv, 0x80000);
    DSP dsp(mem, &px, &py);
    std::ifstream f(script); std::string line; TWord stop = 0xffffff; uint64_t maxi = 10000000;
    std::string histFile; std::map<TWord, uint64_t> hist;   // HIST file: per-PC execution counts of all RUNs
    std::string traceFile; std::vector<uint8_t> trX(0x80000), trY(0x80000);   // TRACE file: X/Y access bits of all RUNs
    std::vector<uint8_t> wX(0x80000), wY(0x80000); bool watching = false;
    bool spTrack = false; TWord spMax = 0, spMaxPC = 0;                         // SPMAX: deepest system stack in RUNs     // WATCHFILE f ; WATCH X|Y addr [n]: log PC of accesses
    while (std::getline(f, line)) {
        std::istringstream s(line); std::string c; s >> c;
        if (c.empty() || c[0] == '#') continue;
        auto area = [&](char a) { return a == 'P' ? MemArea_P : a == 'X' ? MemArea_X : MemArea_Y; };
        if (c == "P" || c == "X" || c == "Y") {
            std::string as; s >> as; TWord addr = strtoul(as.c_str(), nullptr, 16); std::string w;
            while (s >> w) mem.set(area(c[0]), addr++, strtoul(w.c_str(), nullptr, 16));
        } else if (c == "LOADP") {    // LOADP file addr  (raw 3-byte BE words)
            std::string fn, as; s >> fn >> as; TWord addr = strtoul(as.c_str(), nullptr, 16);
            std::ifstream b(fn, std::ios::binary); std::vector<unsigned char> d((std::istreambuf_iterator<char>(b)), {});
            for (size_t i = 0; i + 2 < d.size(); i += 3) mem.set(MemArea_P, addr++, (d[i] << 16) | (d[i+1] << 8) | d[i+2]);
        } else if (c == "PC") { std::string as; s >> as; dsp.setPC(strtoul(as.c_str(), nullptr, 16)); }
        else if (c == "STOP") { std::string as; s >> as; stop = strtoul(as.c_str(), nullptr, 16); }
        else if (c == "MAX") { s >> maxi; }
        else if (c == "HIST") { s >> histFile; }
        else if (c == "TRACE") { s >> traceFile; }
        else if (c == "SPMAX") { spTrack = true; }
        else if (c == "WATCHFILE") { std::string fn; s >> fn; g_watchOut = fopen(fn.c_str(), "w"); }
        else if (c == "WATCH") {
            std::string sp, as; TWord n = 1; s >> sp >> as; s >> n; if (!n) n = 1;
            TWord addr = strtoul(as.c_str(), nullptr, 16); auto& v = sp == "X" ? wX : wY;
            for (TWord i = 0; i < n; ++i) v[addr + i] = 1; watching = true;
        }
        else if (c == "RUN") {
            uint64_t n = 0; const uint64_t i0 = dsp.getInstructionCounter(), c0 = dsp.getCycles();
            if (!traceFile.empty()) { g_memTrace[MemArea_X] = trX.data(); g_memTrace[MemArea_Y] = trY.data(); }
            if (watching) { g_memWatch[MemArea_X] = wX.data(); g_memWatch[MemArea_Y] = wY.data(); g_memWatchCb = watchCb; }
            while (dsp.getPC().toWord() != stop && n < maxi) { g_curPC = dsp.getPC().toWord(); if (!histFile.empty()) ++hist[g_curPC]; dsp.execInterpreter(); ++n;
                if (spTrack && dsp.ssIndex() > spMax) { spMax = dsp.ssIndex(); spMaxPC = g_curPC; } }
            g_memWatch[MemArea_X] = g_memWatch[MemArea_Y] = nullptr;
            g_memTrace[MemArea_X] = g_memTrace[MemArea_Y] = nullptr;
            printf("RAN %llu pc=%06x ins=%llu cyc=%llu\n", (unsigned long long)n, dsp.getPC().toWord(),
                   (unsigned long long)(dsp.getInstructionCounter() - i0), (unsigned long long)(dsp.getCycles() - c0));
        } else if (c == "DUMPX" || c == "DUMPY" || c == "DUMPP") {
            std::string as; TWord n; s >> as >> n; TWord addr = strtoul(as.c_str(), nullptr, 16);
            printf("%s %06x:", c.c_str() + 4, addr);
            for (TWord i = 0; i < n; ++i) printf(" %06x", mem.get(area(c[4]), addr + i));
            printf("\n");
        }
    }
    if (g_watchOut) fclose(g_watchOut);
    if (spTrack) printf("SPMAX %u pc=%06x\n", spMax, spMaxPC);
    if (!traceFile.empty()) { FILE* t = fopen(traceFile.c_str(), "wb"); fwrite(trX.data(), 1, trX.size(), t); fwrite(trY.data(), 1, trY.size(), t); fclose(t); }
    if (!histFile.empty()) { FILE* h = fopen(histFile.c_str(), "w"); for (auto& kv : hist) fprintf(h, "%06x %llu\n", kv.first, (unsigned long long)kv.second); fclose(h); }
    return 0;
}

// dis <file> [base]: raw 3-byte BE words -> "addr: words  text" per instruction
static int cmdDis(const char* fn, TWord base) {
    std::vector<unsigned char> d;
    if (!strcmp(fn, "/dev/stdin")) d.assign(std::istreambuf_iterator<char>(std::cin), {});   // also on Windows (no /dev/stdin there)
    else { std::ifstream b(fn, std::ios::binary); d.assign(std::istreambuf_iterator<char>(b), {}); }
    std::vector<TWord> w; for (size_t i = 0; i + 2 < d.size(); i += 3) w.push_back((d[i] << 16) | (d[i+1] << 8) | d[i+2]);
    Opcodes ops; Disassembler dis(ops);
    for (size_t i = 0; i < w.size();) {
        std::string t; TWord opB = i + 1 < w.size() ? w[i+1] : 0;
        uint32_t n = dis.disassemble(t, w[i], opB, 0, 0, base + (TWord)i); if (n == 0) n = 1;
        printf("%06x: %06x", base + (unsigned)i, w[i]); printf(n > 1 ? " %06x " : "        ", opB); printf(" %s\n", t.c_str());
        i += n;
    }
    return 0;
}

// stdin mode (build_sc13.py): each line "op opB" -> "<words> <text>"
static int cmdDisLines() {
    Opcodes ops; Disassembler dis(ops); std::string line;
    while (std::getline(std::cin, line)) {
        unsigned op = 0, opB = 0; sscanf(line.c_str(), "%x %x", &op, &opB);
        std::string t; uint32_t n = dis.disassemble(t, op, opB, 0, 0, 0); if (n == 0) n = 1;
        printf("%u %s\n", n, t.c_str());
    }
    return 0;
}

int main(int argc, char** argv) {
#ifdef _WIN32
    _setmode(_fileno(stdin), _O_BINARY); _setmode(_fileno(stdout), _O_BINARY);   // same bytes as on Linux
#endif
    if (argc >= 2 && !strcmp(argv[1], "asm")) return cmdAsm();
    if (argc >= 3 && !strcmp(argv[1], "run")) return cmdRun(argv[2]);
    if (argc >= 3 && !strcmp(argv[1], "dis")) return cmdDis(argv[2], argc >= 4 ? strtoul(argv[3], nullptr, 16) : 0);
    if (argc == 2 && !strcmp(argv[1], "dis")) return cmdDisLines();
    fprintf(stderr, "usage: dsptool asm < lines | dsptool run script | dsptool dis file.bin [base] | dsptool dis < \"op opB\" lines\n"); return 1;
}
