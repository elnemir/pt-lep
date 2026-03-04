# Журнал изменений документации

## 2026-03-04

### Изменено
- Запущен цикл исправления P2-замечаний из [docs/CODE_REVIEW.md](./CODE_REVIEW.md):
  - перевод выбора syslog-демона на детерминированную логику;
  - устранение строкового сравнения версий auditd.
- Реализованы P2-фиксы:
  - обновлен [tasks/configure/syslog.yml](../tasks/configure/syslog.yml): выбор syslog-демона через `service_facts` и детерминированные правила;
  - обновлен [tasks/configure/audispd-plugins.yml](../tasks/configure/audispd-plugins.yml): ветвление по числовому `auditd_major_version`;
  - обновлен [tasks/install/with_repos/auditd.yml](../tasks/install/with_repos/auditd.yml): нормализация версии и сравнение через `version` test.
- Запущен цикл исправления P1-замечаний из [docs/CODE_REVIEW.md](./CODE_REVIEW.md):
  - корректировка mapping офлайн-пакетов для REDOS/RED;
  - повышение надежности `without_repos` установки с явной валидацией результатов.
- Исправлен `packages_dirs.rpm` в [vars/main.yml](../vars/main.yml):
  - `REDOS` переведен на каталог `redos7`;
  - `RED` переведен на каталог `redos7` с корректной структурой (`dist/ver/dir_name`).
- В offline-установках убраны "тихие" ошибки и добавлены post-check:
  - [tasks/install/without_repos/audit.yml](../tasks/install/without_repos/audit.yml)
  - [tasks/install/without_repos/audispd-plugins.yml](../tasks/install/without_repos/audispd-plugins.yml)
  - [tasks/install/without_repos/rsyslog.yml](../tasks/install/without_repos/rsyslog.yml)
  - [tasks/install/without_repos/misc.yml](../tasks/install/without_repos/misc.yml)
- Добавлены валидации бинарников после установки (`auditctl -v`, `rsyslogd -v`, `tar --version`).

### Добавлено
- Создан [README.md](../README.md) с:
  - назначением роли;
  - быстрым стартом;
  - ключевыми переменными;
  - supported matrix;
  - ссылками на полный пакет документации.
- Создан [CHANGELOG.md](../CHANGELOG.md) в формате релизного журнала.
- Создан [docs/ARCHITECTURE.md](./ARCHITECTURE.md) с описанием компонентов и Mermaid-диаграммой потока.
- Создан [docs/CONFIGURATION.md](./CONFIGURATION.md) с переменными, facility-группами и шаблонами.
- Создан [docs/RUNBOOK.md](./RUNBOOK.md) с процедурами запуска, валидации и отката.
- Создан [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md) с анализом реализации и техдолга.
- Создан [docs/CODE_REVIEW.md](./CODE_REVIEW.md) с приоритизированными findings.
- Создан [docs/tasktracker.md](./tasktracker.md) с трекингом выполненной задачи.

### Результат
- Документация приведена к состоянию, достаточному для:
  - первичного онбординга;
  - безопасного запуска роли;
  - контроля текущих ограничений и рисков.
