#!/usr/bin/env python3
"""Repeatable Intel RAPL package energy measurement for Lab 2.

Run on Fedora, from any directory: sudo python3 cpp/rapl_measure.py
Requires built cpp/tree_benchmark_O0 and cpp/tree_benchmark_O3.
Measures CPU package energy, NOT isolated energy of one process.
"""
from pathlib import Path
import argparse
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RAPL = Path('/sys/class/powercap/intel-rapl:0')


def read_integer(filename):
    return int((RAPL / filename).read_text().strip())


def measure_idle(seconds, modulus):
    before = read_integer('energy_uj')
    start = time.monotonic()
    time.sleep(seconds)
    duration = time.monotonic() - start
    after = read_integer('energy_uj')
    return ((after - before) % modulus) / 1e6, duration


def measure_runs(exe, runs, modulus):
    before = read_integer('energy_uj')
    start = time.monotonic()
    for _ in range(runs):
        subprocess.run([str(exe)], check=True, stdout=subprocess.DEVNULL)
    duration = time.monotonic() - start
    after = read_integer('energy_uj')
    return ((after - before) % modulus) / 1e6, duration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=int, default=10)
    parser.add_argument('--idle-seconds', type=float, default=15)
    args = parser.parse_args()
    if args.runs < 1 or args.idle_seconds <= 0:
        parser.error('runs must be >=1 and idle-seconds must be >0')
    if not (RAPL / 'energy_uj').exists():
        parser.error('Intel RAPL package-0 energy_uj not found on this system')
    try:
        modulus = read_integer('max_energy_range_uj')
        zone = (RAPL / 'name').read_text().strip()
    except PermissionError:
        parser.error('Cannot read Intel RAPL; use sudo if appropriate')
    if zone != 'package-0':
        print(f'Warning: zone is {zone!r}, not package-0')
    for label in ('O0', 'O3'):
        exe = HERE / f'tree_benchmark_{label}'
        if not exe.is_file():
            parser.error(f'Executable missing: {exe}; build the C++ programs first')
        try:
            idle_energy, idle_duration = measure_idle(args.idle_seconds, modulus)
            idle_power = idle_energy / idle_duration
            energy, duration = measure_runs(exe, args.runs, modulus)
        except PermissionError:
            parser.error('Permission denied reading RAPL; use sudo if appropriate')
        data = (
            f'Version: {label}\nZone: {zone}\nRuns: {args.runs}\n'
            f'Idle average power: {idle_power:.4f} W\n'
            f'Batch duration: {duration:.4f} s\n'
            f'Batch energy: {energy:.4f} J\n'
            f'Average power during batch: {energy / duration:.4f} W\n'
            f'Mean duration per run: {duration / args.runs:.4f} s\n'
            f'Mean package energy per run: {energy / args.runs:.4f} J\n'
            f'Estimated energy above idle per run: '
            f'{(energy - idle_power * duration) / args.runs:.4f} J\n'
        )
        dest = ROOT / 'results' / f'cpp_{label}' / 'energy_repeat.txt'
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(data, encoding='utf-8')
        print(data)
        print(f'Saved to: {dest}\n')
    print('Note: package energy above idle is an estimate, not per-process energy.')
    print('Measurement assumes fewer than one RAPL counter wrap per interval.')

if __name__ == '__main__':
    main()
