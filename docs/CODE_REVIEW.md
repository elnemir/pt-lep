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

## Открытые findings

## P2

### 1) В inventory присутствуют внутренние IP/hostnames
- Файл: [inventory/hosts](../inventory/hosts#L31)
- Детали:
  - в репозитории хранится production-подобный список хостов.
- Риск:
  - повышенный риск утечки инфраструктурных данных.

## P3

### 4) Небольшие проблемы качества и поддерживаемости
- Файлы:
  - [tasks/configure/auditd.yml](../tasks/configure/auditd.yml#L96) (опечатка в названии задачи)
  - [tasks/configure/rsyslogd.yml](../tasks/configure/rsyslogd.yml#L7) (сложные shell/grep выражения)
- Риск:
  - ухудшение читаемости и сопровождения, но без прямого функционального блокера.

## Рекомендованный порядок исправления (оставшееся)

1. Вынести production inventory в отдельный закрытый контур.
2. Исправить мелкие проблемы качества (`task name typo`, сложные grep-условия).
