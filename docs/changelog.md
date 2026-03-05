# Журнал изменений документации

## 2026-03-05

### Изменено
- Запущен цикл подготовки fully-offline контуров для актуальных Debian и всех целевых CentOS/REDOS:
  - Debian `13` (`trixie`);
  - CentOS `7..10`;
  - REDOS/RED `7..9`.
- Реализовано расширение offline-поддержки:
  - в [vars/main.yml](../vars/main.yml) добавлены mapping записи:
    - `trixie -> debian13`,
    - `CentOS 9 -> centos9`,
    - `CentOS 10 -> centos10`,
    - `REDOS/RED 8 -> redos8`,
    - `REDOS/RED 9 -> redos9`;
  - обновлен скрипт [scripts/fetch_debian_legacy_offline.py](../scripts/fetch_debian_legacy_offline.py):
    - теперь поддерживает `debian6..debian13`;
    - добавлен параметр `--releases`;
  - добавлен [scripts/fetch_rpm_offline.py](../scripts/fetch_rpm_offline.py):
    - автоматический резолв RPM-зависимостей по metadata;
    - выгрузка для `centos7..10`;
    - формирование `redos7..9` как совместимых alias-наборов.
- Актуализирована эксплуатационная документация:
  - [README.md](../README.md),
  - [docs/CONFIGURATION.md](./CONFIGURATION.md),
  - [docs/RUNBOOK.md](./RUNBOOK.md),
  - [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md),
  - [CHANGELOG.md](../CHANGELOG.md).
- Добавлен [.gitignore](../.gitignore):
  - исключены `.DS_Store` и `__pycache__` для предотвращения повторного попадания служебных файлов в git-статус.
- Расширена поддержка AstraLinux:
  - в [vars/main.yml](../vars/main.yml) `linux_supported` обновлен до `Astra Linux 1..2`;
  - добавлен оффлайн mapping для релизов `1.5/1.6/1.7/1.8/2.12` с compatibility-привязкой к существующим bundles (`astra17`, `debian9`, `debian12`).

## 2026-03-04

### Изменено
- Запущен цикл добавления офлайн-пакетов для устаревших Debian-релизов:
  - `debian6 (squeeze)`,
  - `debian7 (wheezy)`,
  - `debian8 (jessie)`.
- Реализовано добавление офлайн-пакетов для устаревших Debian:
  - добавлен скрипт [scripts/fetch_debian_legacy_offline.py](../scripts/fetch_debian_legacy_offline.py) для автоматической выгрузки;
  - добавлены наборы `.deb` (с зависимостями) для `debian6`, `debian7`, `debian8` по компонентам `auditd`, `audispd-plugins`, `rsyslog`, `misc`;
  - в [vars/main.yml](../vars/main.yml) добавлены mapping записи:
    - `squeeze -> debian6`,
    - `wheezy -> debian7`,
    - `jessie -> debian8`.
- Запущен цикл точечного расширения поддержки ОС:
  - Debian до версии 13;
  - CentOS до версии 10.
- Реализовано точечное расширение поддержки ОС:
  - в [vars/main.yml](../vars/main.yml) обновлен `linux_supported`:
    - Debian `6..13`;
    - CentOS `7..10`.
  - обновлены диапазоны в [README.md](../README.md) и [docs/CONFIGURATION.md](./CONFIGURATION.md).
- Запущен цикл расширения поддержки ОС:
  - поддержка Debian начиная с 6.x;
  - поддержка REDOS/RED до 9.x;
  - повышение переносимости install-логики для современных RHEL-like систем и явная обработка отсутствующих офлайн-пакетов.
- Реализовано расширение поддержки ОС:
  - в [vars/main.yml](../vars/main.yml) расширен `linux_supported` до:
    - RedHat/CentOS/OracleLinux `7..9`;
    - Debian `6..12`;
    - REDOS/RED `7..9`;
  - в `with_repos`-ветках RHEL-like установка переведена на package-agnostic модуль `ansible.builtin.package`;
  - в `without_repos`-ветках добавлены:
    - проверка mapping локальных пакетов для текущей версии ОС;
    - проверка наличия загруженных `.rpm/.deb`;
    - RPM-установка через `dnf/yum` с авто-выбором по `ansible_pkg_mgr`.
- Запущен цикл P3 hardening и cleanup:
  - удаление чувствительных данных из inventory;
  - закрытие мелких quality-замечаний в task-файлах.
- Реализованы P3-фиксы:
  - [inventory/hosts](../inventory/hosts) заменен на sanitized template (без внутренних адресов);
  - [vars/siem_agents.yml](../vars/siem_agents.yml) переведен на placeholder endpoint;
  - [tasks/configure/auditd.yml](../tasks/configure/auditd.yml) исправлена опечатка в имени задачи;
  - [tasks/configure/rsyslogd.yml](../tasks/configure/rsyslogd.yml) проверки `grep` переведены с shell-конвейеров на `command` + анализ `rc`.
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
