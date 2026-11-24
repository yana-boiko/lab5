# Лабораторна робота 5. Потокобезпечна структура даних

Варіант 4: пріоритетна черга задач (С4), місткість 64, n = 12 потоків (6 пишуть, 6 читають).
Порівняння глобального замка і RWLock. Python 3.10, `threading`.

**Звіт:** [report/report.md](report/report.md)

## Запуск

mkdir results
python stand.py --sync global --rep 1
python stand.py --sync rw --rep 1

Режими: --mode x1 (швидкість одного потоку), --mode tcs (час утримання глобального замка).
Таблиці зі збережених результатів: table2.py, table3.py, table5.py, table6.py.

## Структура

- stand.py – черга, обидва замки, стенд
- table*.py – розрахунок таблиць
- results/ – сирі результати прогонів
- report/ – звіт із зображеннями