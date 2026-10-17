# Lab 2 — Performance Measurement and Analysis

Лабораторна робота з аналізу продуктивності та енерговитрат програми, профілювання CPU й дослідження асемблерного коду після оптимізації.

## Мета та програма

Основна програма — `cpp/tree_benchmark.cpp` (C++17). Вона створює масив із 20 000 000 чисел `float` та 20 разів підраховує елементи, які не перевищують `0.5`. Для порівняння зібрані версії без оптимізації (`-O0`) та з оптимізацією (`-O3 -march=native`). Для обох версій отримано однаковий результат: `Total count: 199934980`.

Вимірювання виконано у Fedora KDE Plasma Live USB на Intel Core i5-12450H. Використано GCC, `/usr/bin/time`, Linux `perf`, FlameGraph, Intel RAPL та показники батареї.

## Основні результати

| Показник | `-O0` | `-O3 -march=native` |
|---|---:|---:|
| Час обчислювального циклу (`std::chrono`) | 3,27601 с | 0,0773883 с |
| Повний час (`/usr/bin/time`) | 3,71 с | 0,15 с |
| Середній час (`perf stat -r 3`) | 3,793994 с | 0,152680 с |
| Кількість інструкцій (`cpu_core`) | 34 053 848 255 | 1 287 550 358 |
| Кількість тактів (`cpu_core`) | 15 809 310 087 | 586 745 291 |
| Енергія CPU package за RAPL, на запуск | 73,3363 Дж | 2,9254 Дж |

Час обчислювального циклу зменшився приблизно у **42,3 раза**, а повний час за середніми даними `perf stat` — приблизно у **24,85 раза**. Після оптимізації компілятор використовує векторні AVX/AVX2-інструкції, а окремі виклики методів `std::vector` в основному циклі усуваються.

> Енергетичні показники батареї та RAPL охоплюють різні компоненти й умови вимірювання. Енергія понад фонове споживання — це **оцінка** внеску програми, а не пряме вимірювання окремого процесу.

## Структура проєкту

- `cpp/` — вихідний код C++, виконувані файли, асемблерні лістинги та скрипти вимірювання енергії.
- `results/cpp_O0/`, `results/cpp_O3/` — результати `/usr/bin/time`, `perf stat`, `perf report`, FlameGraph, дизасемблювання та енерговимірювань.
- `screenshots/` — скріншоти виконаних команд і графіків.
- `FlameGraph/` — інструменти побудови FlameGraph (Brendan Gregg).
- `benchmark/`, `results/before/` — додатковий експеримент із Python (Decision Tree, Random Forest, XGBoost). Це окрема задача, **не** порівняння швидкодії Python та C++.

## Компіляція та запуск

Команди виконуються з кореня проєкту у Linux:

```bash
cd cpp
g++ -std=c++17 -O0 -g -fno-omit-frame-pointer tree_benchmark.cpp -o tree_benchmark_O0
g++ -std=c++17 -O3 -march=native -g -fno-omit-frame-pointer tree_benchmark.cpp -o tree_benchmark_O3
./tree_benchmark_O0
./tree_benchmark_O3
```

Збірка з `-march=native` орієнтована на процесор, на якому її компілюють.

## Вимірювання продуктивності

З каталогу `cpp/`:

```bash
/usr/bin/time -v ./tree_benchmark_O0
/usr/bin/time -v ./tree_benchmark_O3
perf stat -r 3 -d ./tree_benchmark_O0
perf stat -r 3 -d ./tree_benchmark_O3
```

Профіль і FlameGraph для `-O0`:

```bash
perf record -F 999 -g -o ../results/cpp_O0/perf.data -- bash -c 'for i in {1..5}; do ./tree_benchmark_O0; done'
perf report -i ../results/cpp_O0/perf.data
perf script -i ../results/cpp_O0/perf.data | ../FlameGraph/stackcollapse-perf.pl --event-filter=cpu_core/cycles/Pu > ../results/cpp_O0/perf.folded
../FlameGraph/flamegraph.pl --minwidth '1%' ../results/cpp_O0/perf.folded > ../results/cpp_O0/flame.svg
```

Аналогічно для `-O3`: замінити `cpp_O0` на `cpp_O3` та `tree_benchmark_O0` на `tree_benchmark_O3`. На іншій системі назви подій `perf` можуть відрізнятися.

## Енерговитрати

Із кореня проєкту:

```bash
python3 cpp/battery_measure.py
sudo python3 cpp/rapl_measure.py
```

`battery_measure.py` використовує датчик батареї ноутбука; вимірювання слід виконувати під час розряду. `rapl_measure.py` зчитує `intel-rapl:0/energy_uj` та зберігає **нові** результати в `results/cpp_O0/energy_repeat.txt` і `results/cpp_O3/energy_repeat.txt`. Для RAPL необхідні відповідний процесор, підтримка інтерфейсу в ОС та права читання. Повторні результати можуть відрізнятися від первинних.

## Додатковий експеримент (Python)

```bash
python3 -m pip install -r benchmark/requirements.txt
python3 benchmark/benchmark.py
```

Збережені результати Python-профілювання розміщені в `results/before/`.
