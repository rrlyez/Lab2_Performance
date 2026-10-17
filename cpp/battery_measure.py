"""Measure laptop battery energy during repeated C++ benchmark runs.

Run from Lab2_Performance/cpp: python battery_measure.py
Keep AC disconnected, screen on, and brightness unchanged throughout.
Battery readings and idle subtraction are approximate, not per-process counters.
"""
from pathlib import Path
import subprocess
import time

BATTERY = Path('/sys/class/power_supply/BAT1')
SECONDS = 60
RESULTS = Path.cwd().parent / 'results'


def read(name):
    return (BATTERY / name).read_text().strip()


def require_battery():
    if read('status') != 'Discharging':
        raise RuntimeError('Disconnect AC: battery must be Discharging.')


def measure(action):
    require_battery()
    before = int(read('energy_now'))
    start = time.perf_counter()
    count = action()
    duration = time.perf_counter() - start
    after = int(read('energy_now'))
    require_battery()
    if after >= before:
        raise RuntimeError('Battery energy did not decrease; measurement unusable.')
    return duration, (before - after) * 0.0036, count, before, after


def main():
    executables = {v: Path.cwd() / ('tree_benchmark_' + v) for v in ('O0', 'O3')}
    for executable in executables.values():
        if not executable.is_file():
            raise RuntimeError('Run this script from the cpp folder: missing ' + str(executable))
    RESULTS.mkdir(exist_ok=True)
    print('Idle baseline: wait 60 seconds...', flush=True)
    idle_t, idle_e, _, before, after = measure(lambda: time.sleep(SECONDS))
    idle_power = idle_e / idle_t
    baseline = (f'Power source: battery\nDuration: {idle_t:.4f} s\n'
                f'Energy before: {before} uWh\nEnergy after: {after} uWh\n'
                f'Idle energy: {idle_e:.4f} J\nIdle average power: {idle_power:.4f} W\n')
    (RESULTS / 'battery_idle.txt').write_text(baseline)
    print(baseline, flush=True)
    for version, executable in executables.items():
        print(f'{version}: running for at least 60 seconds...', flush=True)

        def workload():
            count = 0
            start = time.perf_counter()
            while time.perf_counter() - start < SECONDS:
                require_battery()
                subprocess.run([str(executable)], stdout=subprocess.DEVNULL, check=True)
                count += 1
            return count

        duration, energy, count, before, after = measure(workload)
        report = (f'Version: {version}\nPower source: battery\nRuns: {count}\n'
                  f'Energy before: {before} uWh\nEnergy after: {after} uWh\n'
                  f'Batch duration: {duration:.4f} s\nSystem batch energy: {energy:.4f} J\n'
                  f'System average power: {energy / duration:.4f} W\n'
                  f'Mean duration per run: {duration / count:.4f} s\n'
                  f'Mean system energy per run: {energy / count:.4f} J\n'
                  f'Estimated energy above idle per run: {(energy - idle_power * duration) / count:.4f} J\n'
                  'Method: battery energy drop; idle subtraction is an estimate.\n')
        destination = RESULTS / ('cpp_' + version)
        destination.mkdir(exist_ok=True)
        (destination / 'battery_energy.txt').write_text(report)
        print(report, flush=True)
    print('Done. You may reconnect AC.', flush=True)


if __name__ == '__main__':
    main()
