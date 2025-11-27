#!/usr/bin/env python3
import os, time, subprocess

# MAIN CARTS (1–41)
main_carts = [
    f"cart{str(i).zfill(3)}" + ext
    for i, ext in zip(range(1, 42), [
        "A_infinity_runcommands.py",
        "002_engineering.py",
        "003_computers.py",
        "004_nuances.py",
        "005_code.py",
        "006_python.py",
        "007_tokens.py",
        "008_government.py",
        "009_power.py",
        "010_components.py",
        "011_speakeasy.py",
        "012_solutes.py",
        "013_mercury_aluminum_growth.py",
        "014_mercury_vapor_power.py",
        "015_compression_hydrogen_engine.py",
        "016_hot_cold_TEG.py",
        "017_spiderweb_engine.py",
        "018_zip_hashing.py",
        "019_token_generation.py",
        "020_unzip_install_strategy.py",
        "021_token_tiers.py",
        "022_bank_grade_tokens.py",
        "023_idea_merger.py",
        "024_quantum_transport.py",
        "025_ai_watcher_login.py",
        "026_aluminum_oxide_devices.py",
        "027_robotics.py",
        "028_machines.py",
        "029_crystal_truths.py",
        "030_superchemistry_fireproof.py",
        "031_exoskeleton.py",
        "032_ecosystem.py",
        "033_nature.py",
        "034_drones.py",
        "035_signal_trace.py",
        "036_rf_generation.py",
        "037_mice_brainmapping.py",
        "038_genetics.py",
        "039_dna_engine.py",
        "040_gas_shell_code.py",
        "041_hydrogen_expansion.py",
    ])
]

# CALCULATOR CARTS (1–41)
calc_carts = [f"cart{str(i).zfill(3)}_calc.py" for i in range(1, 42)]

def run_background(script):
    try:
        subprocess.Popen(["python", script])
        print(f"Started: {script}")
    except:
        print(f"FAILED TO START: {script}")

def main():
    print("∞ STARTING ALL 82 CARTS ∞\n")

    print("→ Starting MAIN MODULE CARTS...")
    for script in main_carts:
        run_background(script)
        time.sleep(0.20)

    print("\n→ Starting CALCULATOR CARTS...")
    for script in calc_carts:
        run_background(script)
        time.sleep(0.15)

    print("\n∞ ALL CARTS LAUNCHED ∞")

if __name__ == "__main__":
    main()
