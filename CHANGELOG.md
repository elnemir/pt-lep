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
