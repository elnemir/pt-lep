# Code Review Findings

Ниже перечислен актуальный статус findings после внесенных исправлений.

## Закрыто (2026-03-04)

### P1-1) Некорректный mapping каталогов пакетов для REDOS/RED
- Исправлено в [vars/main.yml](../vars/main.yml#L100):
  - `REDOS -> redos7`;
  - `RED -> redos7` с корректной структурой (`dist/ver/dir_name`).

### P1-2) Игнорирование ошибок в offline-инсталляции
- Исправлено:
  - [tasks/install/without_repos/audit.yml](../tasks/install/without_repos/audit.yml#L21)
  - [tasks/install/without_repos/audispd-plugins.yml](../tasks/install/without_repos/audispd-plugins.yml#L21)
  - [tasks/install/without_repos/rsyslog.yml](../tasks/install/without_repos/rsyslog.yml#L21)
  - [tasks/install/without_repos/misc.yml](../tasks/install/without_repos/misc.yml#L21)
- Что сделано:
  - удалены `ignore_errors: True`;
  - добавлены post-install проверки через `package_facts` + `assert`;
  - добавлены проверки бинарников (`auditctl -v`, `rsyslogd -v`, `tar --version`).

### P2-1) Определение syslog-демона зависело только от запущенного процесса
- Исправлено в [tasks/configure/syslog.yml](../tasks/configure/syslog.yml#L2):
  - удален `pgrep`-подход;
  - добавлен выбор по `service_facts` с детерминированными правилами;
  - fallback на установку `rsyslog` сохранен при отсутствии обнаруженных сервисов.

### P2-2) Строковые сравнения версий Auditd
- Исправлено:
  - [tasks/configure/audispd-plugins.yml](../tasks/configure/audispd-plugins.yml#L2)
  - [tasks/install/with_repos/auditd.yml](../tasks/install/with_repos/auditd.yml#L27)
- Что сделано:
  - переход на числовой `auditd_major_version` для audispd ветвления;
  - переход на `version` test после нормализации версии в install-with-repos ветке.

### P3-1) В inventory присутствовали внутренние IP/hostnames
- Исправлено в [inventory/hosts](../inventory/hosts#L1):
  - inventory заменен на sanitized template без внутренних адресов;
  - добавлен безопасный default `localhost` для локального запуска.
- Дополнительно санитизирован default SIEM endpoint в [vars/siem_agents.yml](../vars/siem_agents.yml#L18) (`mpxagent01.example.com`).

### P3-2) Мелкие проблемы качества в task-файлах
- Исправлено:
  - [tasks/configure/auditd.yml](../tasks/configure/auditd.yml#L96): исправлена опечатка в названии задачи;
  - [tasks/configure/rsyslogd.yml](../tasks/configure/rsyslogd.yml#L6): shell-конвейеры в grep-проверках заменены на `command` + `rc` (`failed_when: false`, `changed_when: false`).

## Открытые findings

Открытых findings в рамках текущего review-списка не осталось.

## Рекомендованный порядок исправления (оставшееся)

1. Добавить CI-контур (`ansible-lint`, syntax-check, smoke-run) и закрепить его как обязательный gate.
2. Вынести повторяющуюся install-логику в переиспользуемые блоки и сократить shell-heavy участки.
