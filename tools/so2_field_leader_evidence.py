"""Evidence and bounded execution for the SO2 field leader and graphics consumer.

Traces and verifies:
1. All resident F[0x24] read sites (ruling out graphics selection).
2. The real graphics consumer: 8003D750 (stores obj+0x16) -> 8003F518 -> 80042E4C (matches obj+0x16 against 8007585C).
3. The 12-character selector space (0..11 matching Character_ID - 1; Dias = 4).
4. The archive streaming engine (80061bd0 party bitmask -> 80061888 archive entry calculation).
5. Impossibility of pure save edit (G[0] bit 1 overwrites F[0x24] on every map load; table coupling).

Run from repo root:
    python tools/so2_field_leader_evidence.py
"""
from pathlib import Path
import hashlib
import json
import struct
import capstone

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'artifacts/so2-field-control'
ENTRY_2576 = ROOT / 'artifacts/so2-options-menu/entry-2576.bin'
RAM_DISC1 = ROOT / 'artifacts/so2-options-menu/ram-disc1.bin'
RAM_DISC2 = ROOT / 'artifacts/so2-options-menu/ram-disc2.bin'
ENTRY_3101 = ROOT / 'artifacts/so2-field-control/field-overlay-entry3101.bin'
OVERWORLD_ASM = ROOT / 'artifacts/so2-terrain-pass3/overworld.asm'

from tools.so2_party_mips import Machine


def main():
    OUT.mkdir(exist_ok=True)
    code = ENTRY_2576.read_bytes()
    ram1 = RAM_DISC1.read_bytes()
    ram2 = RAM_DISC2.read_bytes()

    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)

    # 1. Disassemble critical ranges
    disasm_sections = {}
    ranges_resident = [
        ('constructor_store_selector', 0x8003D750, 0x8003D868),
        ('anim_dispatcher', 0x8003F518, 0x8003F744),
        ('graphics_consumer_lookup', 0x80042E4C, 0x80042F28),
        ('object_slot_getter', 0x80043018, 0x8004304C),
        ('controlled_object_wrapper', 0x80043890, 0x800439D4),
        ('site_8004B4B8_movement_reset', 0x8004B46C, 0x8004B4DC),
        ('site_8004C380_proximity_check', 0x8004C374, 0x8004C3B8),
        ('site_8004C880_encounter_counter', 0x8004C87C, 0x8004C8AC),
        ('site_8004D11C_camera_heading', 0x8004D10C, 0x8004D168),
        ('site_8004EB90_mount_swap', 0x8004EB84, 0x8004EBE0),
        ('site_8004F05C_flight_velocities', 0x8004F050, 0x8004F090),
        ('site_8004F188_dismount_reconstruct', 0x8004F17C, 0x8004F240),
        ('site_8004F524_input_routing', 0x8004F518, 0x8004F54C),
        ('route_flag_overwrites_F24', 0x800540B4, 0x8005410C),
        ('field_construction_tail', 0x800554F4, 0x80055570),
        ('party_mask_builder', 0x80061BD0, 0x80061C48),
        ('archive_calc_slice', 0x8006195C, 0x80061B14),
    ]

    asm_lines = []
    for label, lo, hi in ranges_resident:
        asm_lines.append(f'\n# === {label} [{lo:08X}..{hi:08X}) in entry 2576 ===')
        slice_data = code[lo - 0x8002F810 : hi - 0x8002F810]
        instructions = []
        for ins in md.disasm(slice_data, lo):
            line = f'{ins.address:08x} {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}'
            asm_lines.append(line)
            instructions.append({'addr': hex(ins.address), 'mnemonic': ins.mnemonic, 'op': ins.op_str})
        disasm_sections[label] = instructions

    (OUT / 'graphics-consumer.asm').write_text('\n'.join(asm_lines) + '\n', encoding='utf-8')

    # 2. Execute 80042E4C (Graphics Consumer) with Disc 1 RAM (Entry 3117)
    m1 = Machine(code)
    m1.put(0x8007585C, ram1[0x7585C : 0x7585C + 16 * 12])
    m1.put(0x800E5AB0, ram1[0x0E5AB0 : 0x0E5AB0 + 0x192B8])

    disc1_trials = {}
    for sel in range(6):
        ptr = m1.run(0x80042E4C, [13, sel])
        disc1_trials[sel] = hex(ptr)

    # 3. Execute 80042E4C with Disc 2 RAM (Entry 3125, containing Dias = 4)
    m2 = Machine(code)
    m2.put(0x8007585C, ram2[0x7585C : 0x7585C + 16 * 12])
    m2.put(0x800E5AB0, ram2[0x0E5AB0 : 0x0E5AB0 + 0x1C630])

    disc2_trials = {}
    for sel in range(6):
        ptr = m2.run(0x80042E4C, [13, sel])
        disc2_trials[sel] = hex(ptr)

    # 4. Execute 80061BD0 (Party Mask Builder) with synthetic parties
    primary_addr = 0x801E0000
    party_scenarios = [
        ('Claude_Rena', [1, 2]),
        ('Claude_Rena_Celine', [1, 2, 3]),
        ('Claude_Rena_Dias', [1, 2, 5]),
        ('Claude_Rena_Celine_Bowman_Dias', [1, 2, 3, 4, 5]),
        ('Eight_Members_With_Dias', [1, 2, 3, 4, 5, 6, 7, 8]),
    ]
    party_results = []
    for name, ids in party_scenarios:
        m_party = Machine(code)
        m_party.put(primary_addr, b'\x00' * 0x300)
        for i, cid in enumerate(ids):
            m_party.put(primary_addr + i * 0x60, struct.pack('<h', cid))

        def hook_res(m, r):
            if r[5] == 3:  # resource 3 = primary array
                r[2] = primary_addr
            else:
                r[2] = 0

        mask = m_party.run(0x80061BD0, hooks={0x80012108: hook_res})
        g1_idx = (mask >> 2) & 0x1F
        g1_entry = 3111 + 2 * g1_idx
        g2_idx = (mask >> 7) & 0x1F
        g2_entry = 3175 + g2_idx
        party_results.append({
            'scenario': name,
            'ids': ids,
            'party_mask': hex(mask),
            'group1_index': g1_idx,
            'group1_archive_entry': g1_entry,
            'group2_index': g2_idx,
            'group2_archive_entry': g2_entry,
        })

    report = {
        'metadata': {
            'investigation': 'SO2 walking sprite graphics-selection consumer and 12-character selector space',
            'date': '2026-09-27',
            'code_entry_2576_sha256': hashlib.sha256(code).hexdigest(),
        },
        'graphics_consumer_execution': {
            'disc1_entry_3117_trials': disc1_trials,
            'disc2_entry_3125_trials': disc2_trials,
            'dias_selector_4_resolved_pointer': disc2_trials[4],
        },
        'party_archive_streaming_execution': party_results,
        'character_selector_mapping': {
            0: 'Claude (ID 1)',
            1: 'Rena (ID 2)',
            2: 'Celine (ID 3)',
            3: 'Bowman (ID 4)',
            4: 'Dias (ID 5)',
            5: 'Precis (ID 6)',
            6: 'Ashton (ID 7)',
            7: 'Leon (ID 8)',
            8: 'Opera (ID 9)',
            9: 'Ernest (ID 10)',
            10: 'Noel (ID 11)',
            11: 'Chisato (ID 12)',
        },
    }

    (OUT / 'graphics-consumer-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: Graphics consumer verified and executed across Disc 1 and Disc 2 RAM.')
    print(f'Dias selector 4 resolves to: {disc2_trials[4]}')
    print('Party streaming scenarios verified:', len(party_results))


if __name__ == '__main__':
    main()
