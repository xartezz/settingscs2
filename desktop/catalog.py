"""Offline snapshot. Sources checked on 2026-11-12; presets are partial."""
PLAYERS = [
    dict(id='donk',name='donk',real='Danil Kryshkovets',team='Team Spirit',role='Rifler',dpi=800,sens=1.25,res='1280 × 960',hz=1000,mouse='ZOWIE x donk (unreleased)',accent='#92b69a'),
    dict(id='monesy',name='m0NESY',real='Ilya Osipov',team='Falcons Esports',role='AWPer',dpi=400,sens=2.3,res='1280 × 960',hz=2000,mouse='Logitech G Pro X Superlight 2 Cyan',accent='#94b3a5'),
    dict(id='zywoo',name='ZywOo',real='Mathieu Herbaut',team='Team Vitality',role='AWPer',dpi=400,sens=1.9,res='1024 × 768',hz=1000,mouse='Pulsar ZywOo The Chosen Mouse Gen.2',accent='#c7ad6a'),
]

def preset(player):
    return (f'// SETTINGSCS2 — {player["name"]}: preset partial, nu config original\n'
            f'// Sursa: https://prosettings.net/players/{"m0nesy" if player["id"]=="monesy" else player["id"]}/\n'
            f'// Snapshot 2026-11-12. DPI {player["dpi"]} si rezolutia se seteaza manual.\n'
            f'sensitivity "{player["sens"]}"\nzoom_sensitivity_ratio "1"\n'
            'viewmodel_fov "68"\nviewmodel_offset_x "2.5"\nviewmodel_offset_y "0"\nviewmodel_offset_z "-1.5"\n')
