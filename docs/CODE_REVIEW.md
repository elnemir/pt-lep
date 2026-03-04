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

## Открытые findings

## P2

### 1) Определение syslog-демона зависит только от запущенного процесса
- Файл: [tasks/configure/syslog.yml](../tasks/configure/syslog.yml#L2)
- Детали:
  - используется `pgrep` по активному процессу.
  - если демон установлен, но остановлен, логика переключается на установку `rsyslog`.
- Риск:
  - возможная смена/дублирование syslog-стека вопреки ожиданиям.

### 2) Строковые сравнения версий Auditd
- Файл: [tasks/configure/audispd-plugins.yml](../tasks/configure/audispd-plugins.yml#L7)
- Детали:
  - условия вида `< '3'` и `>= '3.0'` завязаны на строковое сравнение.
- Риск:
  - некорректное ветвление при нестандартном формате версии.

### 3) В inventory присутствуют внутренние IP/hostnames
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

1. Сделать детерминированный выбор syslog-демона (по service/package facts, а не только по pgrep).
2. Привести сравнение версий к числовому/нормализованному формату.
3. Вынести production inventory в отдельный закрытый контур.
4. Исправить мелкие проблемы качества (`task name typo`, сложные grep-условия).
