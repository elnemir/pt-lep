# Changelog

Все значимые изменения проекта фиксируются в этом файле.

Формат основан на Keep a Changelog, версия проекта следует Semantic Versioning.

## [Unreleased]

### Added
- Полный комплект проектной документации:
  - [README.md](README.md)
  - [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
  - [docs/CONFIGURATION.md](docs/CONFIGURATION.md)
  - [docs/RUNBOOK.md](docs/RUNBOOK.md)
  - [docs/PROJECT_ANALYSIS.md](docs/PROJECT_ANALYSIS.md)
  - [docs/CODE_REVIEW.md](docs/CODE_REVIEW.md)
  - [docs/changelog.md](docs/changelog.md)
  - [docs/tasktracker.md](docs/tasktracker.md)

### Fixed
- Исправлен mapping офлайн-пакетов для `REDOS`/`RED` в [vars/main.yml](vars/main.yml).
- Устранено скрытие ошибок в offline-установках:
  - [tasks/install/without_repos/audit.yml](tasks/install/without_repos/audit.yml)
  - [tasks/install/without_repos/audispd-plugins.yml](tasks/install/without_repos/audispd-plugins.yml)
  - [tasks/install/without_repos/rsyslog.yml](tasks/install/without_repos/rsyslog.yml)
  - [tasks/install/without_repos/misc.yml](tasks/install/without_repos/misc.yml)
- Добавлены post-install проверки пакетов и проверка доступности бинарников в offline-ветках установки.
- Выбор syslog-демона переведен на детерминированную логику через `service_facts` в [tasks/configure/syslog.yml](tasks/configure/syslog.yml).
- Строковые сравнения версий auditd заменены на безопасные сравнения:
  - [tasks/configure/audispd-plugins.yml](tasks/configure/audispd-plugins.yml)
  - [tasks/install/with_repos/auditd.yml](tasks/install/with_repos/auditd.yml)
- Inventory в репозитории санитизирован до шаблона без внутренних адресов: [inventory/hosts](inventory/hosts).
- Default SIEM endpoint в репозитории заменен на placeholder: [vars/siem_agents.yml](vars/siem_agents.yml).
- Закрыты мелкие проблемы качества:
  - [tasks/configure/auditd.yml](tasks/configure/auditd.yml) (исправлена опечатка в task name)
  - [tasks/configure/rsyslogd.yml](tasks/configure/rsyslogd.yml) (упрощены grep-checks без shell-конвейеров)
- Расширена матрица поддерживаемых ОС:
  - RedHat/CentOS/OracleLinux `7..9`
  - Debian `6..12`
  - REDOS/RED `7..9`
  (см. [vars/main.yml](vars/main.yml))
- Для RHEL-like в `with_repos`-ветках установка переведена на `ansible.builtin.package` для совместимости с современными менеджерами пакетов.
- Для `without_repos`-веток добавлены явные проверки availability локальных пакетов и RPM-установка с авто-выбором `dnf/yum`.
