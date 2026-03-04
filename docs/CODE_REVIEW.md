# Code Review Findings

Ниже перечислены основные найденные риски в текущей реализации (без внесения правок в код роли).

## P1

### 1) Некорректный mapping каталогов пакетов для REDOS/RED
- Файл: [vars/main.yml](../vars/main.yml#L100)
- Детали:
  - `REDOS` указывает `dir_name: 'murom7'`, но в `files/packages/` используется каталог `redos7`.
  - для `RED` задана запись `{ name, min_ver, max_ver }`, но без `dist/ver/dir_name`, из-за чего offline-ветки установки не смогут выбрать каталог пакетов.
- Риск:
  - fallback `without_repos/*` на REDOS/RED может не установить пакеты.

### 2) В offline-инсталляции ошибки установки игнорируются
- Файлы:
  - [tasks/install/without_repos/audit.yml](../tasks/install/without_repos/audit.yml#L21)
  - [tasks/install/without_repos/audispd-plugins.yml](../tasks/install/without_repos/audispd-plugins.yml#L21)
  - [tasks/install/without_repos/rsyslog.yml](../tasks/install/without_repos/rsyslog.yml#L21)
- Детали:
  - `ignore_errors: True` на ключевых шагах установки пакетов.
  - Отсутствует обязательная post-check в этих же файлах.
- Риск:
  - роль может завершиться "успешно", но с частично неустановленными зависимостями.

## P2

### 3) Определение syslog-демона зависит только от запущенного процесса
- Файл: [tasks/configure/syslog.yml](../tasks/configure/syslog.yml#L2)
- Детали:
  - используется `pgrep` по активному процессу.
  - если демон установлен, но остановлен, логика переключается на установку `rsyslog`.
- Риск:
  - возможная смена/дублирование syslog-стека вопреки ожиданиям.

### 4) Строковые сравнения версий Auditd
- Файл: [tasks/configure/audispd-plugins.yml](../tasks/configure/audispd-plugins.yml#L7)
- Детали:
  - условия вида `< '3'` и `>= '3.0'` завязаны на строковое сравнение.
- Риск:
  - некорректное ветвление при нестандартном формате версии.

### 5) В inventory присутствуют внутренние IP/hostnames
- Файл: [inventory/hosts](../inventory/hosts#L31)
- Детали:
  - в репозитории хранится production-подобный список хостов.
- Риск:
  - повышенный риск утечки инфраструктурных данных.

## P3

### 6) Небольшие проблемы качества и поддерживаемости
- Файлы:
  - [tasks/configure/auditd.yml](../tasks/configure/auditd.yml#L96) (опечатка в названии задачи)
  - [tasks/configure/rsyslogd.yml](../tasks/configure/rsyslogd.yml#L7) (сложные shell/grep выражения)
- Риск:
  - ухудшение читаемости и сопровождения, но без прямого функционального блокера.

## Рекомендованный порядок исправления

1. Исправить `packages_dirs` для REDOS/RED.
2. Убрать "тихое" игнорирование ошибок в offline-инсталляции и добавить post-install проверки.
3. Сделать детерминированный выбор syslog-демона (по service/package facts, а не только по pgrep).
4. Привести сравнение версий к числовому/нормализованному формату.
5. Вынести production inventory в отдельный закрытый контур.
