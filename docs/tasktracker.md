## Задача: Полная документация проекта PT_LEP_unix
- **Статус**: Завершена
- **Описание**: Подготовить полный комплект документации по текущему состоянию Ansible-роли, включая архитектуру, конфигурацию, запуск, риски и журналирование изменений.

### Шаг 1. Анализ репозитория и AGENTS-инструкций
- **Статус**: Завершена
- **Описание**:
  - Изучены [agents.md](../agents.md), структура репозитория, playbook и task-файлы.
  - Выявлены основные функциональные блоки: установка, конфигурация, шаблоны SIEM.
  - Подтверждено отсутствие существующей папки `docs/` и базовой документации (`README`, `CHANGELOG`).

### Шаг 2. Формирование структуры документации
- **Статус**: Завершена
- **Описание**:
  - Определен набор документов: README, CHANGELOG, ARCHITECTURE, CONFIGURATION, RUNBOOK, PROJECT_ANALYSIS, CODE_REVIEW.
  - Согласованы цели: эксплуатационная применимость, прозрачность ограничений, фиксация техдолга.

### Шаг 3. Подготовка и добавление документов
- **Статус**: Завершена
- **Описание**:
  - Созданы и заполнены все целевые документы.
  - Добавлены перекрестные ссылки между документами.
  - Описаны supported matrix, переменные, порядок исполнения роли и проверки после деплоя.

### Шаг 4. Финальная сверка и self-review изменений
- **Статус**: Завершена
- **Описание**:
  - Проверена структура файлов, корректность ссылок и соответствие содержимого коду.
  - Оформлены findings по рискам/дефектам реализации в отдельном документе [docs/CODE_REVIEW.md](./CODE_REVIEW.md).

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - Решение пользователя о приоритете исправления найденных дефектов (см. [docs/CODE_REVIEW.md](./CODE_REVIEW.md)).

---

## Задача: Исправление P1 замечаний из Code Review
- **Статус**: Завершена
- **Описание**: Устранить P1-риски из [docs/CODE_REVIEW.md](./CODE_REVIEW.md): mapping офлайн-пакетов REDOS/RED и надежность `without_repos` установки.

### Шаг 1. Подготовка и фиксация плана
- **Статус**: Завершена
- **Описание**:
  - Подтверждено выполнение P1-пакета изменений.
  - Определены целевые файлы: `vars/main.yml`, `tasks/install/without_repos/{audit,audispd-plugins,rsyslog}.yml`.

### Шаг 2. Исправление mapping пакетов REDOS/RED
- **Статус**: Завершена
- **Описание**:
  - Обновлен `packages_dirs.rpm` в `vars/main.yml`:
    - `REDOS -> redos7`;
    - `RED -> redos7`.

### Шаг 3. Повышение надежности offline установки
- **Статус**: Завершена
- **Описание**:
  - Удалены `ignore_errors: True` из offline-установок:
    - `tasks/install/without_repos/audit.yml`
    - `tasks/install/without_repos/audispd-plugins.yml`
    - `tasks/install/without_repos/rsyslog.yml`
    - `tasks/install/without_repos/misc.yml`
  - Добавлены post-install проверки через `package_facts` + `assert`.
  - Добавлены runtime проверки бинарников (`auditctl -v`, `rsyslogd -v`, `tar --version`).

### Шаг 4. Валидация и финализация
- **Статус**: Завершена
- **Описание**:
  - Выполнена быстрая проверка изменений и диффов.
  - Попытка `ansible-playbook --syntax-check` не выполнена из-за отсутствия `ansible-playbook` в окружении.

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: перейти к P2-исправлениям из [docs/CODE_REVIEW.md](./CODE_REVIEW.md).

---

## Задача: Исправление P2 замечаний из Code Review
- **Статус**: Завершена
- **Описание**: Устранить P2-риски из [docs/CODE_REVIEW.md](./CODE_REVIEW.md): детерминированный выбор syslog-демона и корректное сравнение версий auditd.

### Шаг 1. Подготовка изменений
- **Статус**: Завершена
- **Описание**:
  - Определены целевые файлы: `tasks/configure/syslog.yml`, `tasks/configure/audispd-plugins.yml`.
  - Принято решение заменить `pgrep` на `service_facts`/`set_fact` логику.
  - Принято решение заменить строковое сравнение версий на числовое (major version).

### Шаг 2. Реализация P2-фиксов
- **Статус**: Завершена
- **Описание**:
  - В [tasks/configure/syslog.yml](../tasks/configure/syslog.yml):
    - заменен `pgrep`-подход на `service_facts` + детерминированный выбор демона;
    - добавлен явный fallback на установку `rsyslog`, если сервисы не обнаружены.
  - В [tasks/configure/audispd-plugins.yml](../tasks/configure/audispd-plugins.yml):
    - строковое сравнение версий заменено на сравнение `auditd_major_version` (int).
  - В [tasks/install/with_repos/auditd.yml](../tasks/install/with_repos/auditd.yml):
    - строковое сравнение версии заменено на `version` test через нормализованную версию.

### Шаг 3. Валидация и финализация
- **Статус**: Завершена
- **Описание**:
  - Проверено отсутствие строковых сравнений `stdout <...` в `tasks/*`.
  - Попытка `ansible-playbook --syntax-check` не выполнена: в окружении отсутствует `ansible-playbook`.

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: перейти к P3-улучшениям и hardening inventory-практик.

---

## Задача: P3 hardening и cleanup качества
- **Статус**: Завершена
- **Описание**: Устранить оставшиеся findings: убрать чувствительные данные из inventory и закрыть мелкие проблемы качества в task-файлах.

### Шаг 1. Подготовка
- **Статус**: Завершена
- **Описание**:
  - Определены целевые файлы: `inventory/hosts`, `tasks/configure/auditd.yml`, `tasks/configure/rsyslogd.yml`.
  - Определен план: sanitize inventory, правка typo, упрощение grep-check без shell-конвейеров.

### Шаг 2. Реализация P3-фиксов
- **Статус**: Завершена
- **Описание**:
  - [inventory/hosts](../inventory/hosts) заменен на sanitized template без реальных адресов.
  - [vars/siem_agents.yml](../vars/siem_agents.yml) переведен на placeholder endpoint.
  - [tasks/configure/auditd.yml](../tasks/configure/auditd.yml) исправлена опечатка в имени задачи.
  - [tasks/configure/rsyslogd.yml](../tasks/configure/rsyslogd.yml) проверочные `grep`-шаги переведены с shell на `command` + `rc`.

### Шаг 3. Актуализация review и документации
- **Статус**: Завершена
- **Описание**:
  - Обновлен [docs/CODE_REVIEW.md](./CODE_REVIEW.md): оставшиеся findings закрыты.
  - Актуализированы [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md), [docs/changelog.md](./changelog.md), [CHANGELOG.md](../CHANGELOG.md).

### Шаг 4. Валидация
- **Статус**: Завершена
- **Описание**:
  - Проверено отсутствие внутренних адресов формата `10.255.*` и `10.7.*` в репозитории.
  - Попытка `ansible-playbook --syntax-check` по-прежнему недоступна из-за отсутствия `ansible-playbook` в окружении.

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: перейти к инфраструктурному этапу (CI + ansible-lint + molecule smoke).

---

## Задача: Расширение поддержки ОС (Debian 6.0 ... RedOS 9.0)
- **Статус**: Завершена
- **Описание**: Расширить поддерживаемые версии ОС с акцентом на Debian 6.x и RedOS 9.x, сохранив корректное поведение online/offline установки.

### Шаг 1. Подготовка
- **Статус**: Завершена
- **Описание**:
  - Определены целевые файлы: `vars/main.yml`, `tasks/install/with_repos/*.yml`, `tasks/install/without_repos/*.yml`.
  - Выбрана стратегия:
    - расширить `linux_supported`;
    - сделать RHEL/REDOS установку репозиторного режима package-manager-agnostic;
    - добавить явную проверку наличия офлайн-пакетов для текущей ОС, чтобы корректно обрабатывать версии без локальных пакетов.

### Шаг 2. Реализация расширения поддержки
- **Статус**: Завершена
- **Описание**:
  - Расширен список поддерживаемых ОС в [vars/main.yml](../vars/main.yml):
    - RedHat/CentOS/OracleLinux: `7..9`;
    - Debian: `6..12`;
    - REDOS/RED: `7..9`.
  - Репозиторная установка для RHEL-like переведена на `ansible.builtin.package`:
    - [tasks/install/with_repos/system-wide.yml](../tasks/install/with_repos/system-wide.yml)
    - [tasks/install/with_repos/auditd.yml](../tasks/install/with_repos/auditd.yml)
    - [tasks/install/with_repos/audispd-plugins.yml](../tasks/install/with_repos/audispd-plugins.yml)
    - [tasks/install/with_repos/rsyslogd.yml](../tasks/install/with_repos/rsyslogd.yml)
  - В offline-ветках добавлена явная валидация mapping и наличия локальных пакетов, а RPM-установка стала поддерживать `dnf/yum`:
    - [tasks/install/without_repos/audit.yml](../tasks/install/without_repos/audit.yml)
    - [tasks/install/without_repos/audispd-plugins.yml](../tasks/install/without_repos/audispd-plugins.yml)
    - [tasks/install/without_repos/rsyslog.yml](../tasks/install/without_repos/rsyslog.yml)
    - [tasks/install/without_repos/misc.yml](../tasks/install/without_repos/misc.yml)

### Шаг 3. Актуализация документации и валидация
- **Статус**: Завершена
- **Описание**:
  - Обновлены [README.md](../README.md), [docs/CONFIGURATION.md](./CONFIGURATION.md), [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md), [CHANGELOG.md](../CHANGELOG.md), [docs/changelog.md](./changelog.md).
  - Проверена структура обновленных YAML-файлов и отсутствие устаревших yum-only репозиторных вызовов.
  - Попытка `ansible-playbook --syntax-check` недоступна в окружении из-за отсутствия `ansible-playbook`.

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: добавить CI-проверки (`ansible-lint`, syntax-check, smoke inventory).

---

## Задача: Расширение поддержки до Debian 13 и CentOS 10
- **Статус**: Завершена
- **Описание**: Обновить supported matrix для Debian и CentOS, сохранив явную модель fallback для offline-режима.

### Шаг 1. Подготовка
- **Статус**: Завершена
- **Описание**:
  - Определен целевой scope: `linux_supported`, эксплуатационная документация.
  - Подтверждено, что offline-пакеты для Debian 13 / CentOS 10 в репозитории отсутствуют, поэтому поддержка для них остается repo-first.

### Шаг 2. Реализация
- **Статус**: Завершена
- **Описание**:
  - В [vars/main.yml](../vars/main.yml) обновлен `linux_supported`:
    - Debian `6..13`;
    - CentOS `7..10`.
  - Обновлены диапазоны в [README.md](../README.md), [docs/CONFIGURATION.md](./CONFIGURATION.md), [CHANGELOG.md](../CHANGELOG.md), [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md).

### Шаг 3. Валидация
- **Статус**: Завершена
- **Описание**:
  - Проверены итоговые диапазоны в коде и документации.
  - `ansible-playbook --syntax-check` не запускался: в окружении отсутствует `ansible-playbook`.

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: добавить offline-пакеты для Debian 13 и CentOS 10 либо оставить их в repo-only режиме.

---

## Задача: Добавление офлайн-пакетов для устаревших Debian
- **Статус**: Завершена
- **Описание**: Сформировать и добавить offline-наборы `.deb` для устаревших Debian-релизов (squeeze/wheezy/jessie) по пакетам `auditd`, `audispd-plugins`, `rsyslog`, `tar` с транзитивными зависимостями.

### Шаг 1. Подготовка
- **Статус**: Завершена
- **Описание**:
  - Подтвержден доступ к `archive.debian.org`.
  - Подтверждено отсутствие локальных наборов `debian6`, `debian7`, `debian8` в `files/packages`.

### Шаг 2. Сборка наборов пакетов
- **Статус**: Завершена
- **Описание**:
  - Добавлен вспомогательный скрипт [scripts/fetch_debian_legacy_offline.py](../scripts/fetch_debian_legacy_offline.py) для автоматической выгрузки legacy Debian пакетов.
  - Выполнена автоматическая выгрузка `.deb` и зависимостей в структуру `files/packages/debian{6,7,8}/{auditd,audispd-plugins,rsyslog,misc}`.
  - Добавлены offline-mapping записи для `squeeze/wheezy/jessie` в [vars/main.yml](../vars/main.yml).

### Шаг 3. Валидация и документация
- **Статус**: Завершена
- **Описание**:
  - Проверены объемы и состав выгруженных наборов (`debian6`: 53M, `debian7`: 58M, `debian8`: 50M).
  - Обновлены [README.md](../README.md), [docs/CONFIGURATION.md](./CONFIGURATION.md), [CHANGELOG.md](../CHANGELOG.md), [docs/changelog.md](./changelog.md), [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md).

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: аналогично собрать offline-наборы для Debian 13 и/или RHEL-like `9/10`.

---

## Задача: Fully-offline поддержка для Debian 13, CentOS 7..10 и REDOS 7..9
- **Статус**: Завершена
- **Описание**: Подготовить полный набор оффлайн-пакетов для актуальных Debian и всех целевых CentOS/REDOS сценариев, пригодный для запуска в полностью закрытом контуре.

### Шаг 1. Подготовка и анализ пробелов
- **Статус**: Завершена
- **Описание**:
  - Проверено текущее покрытие `files/packages`: отсутствовали `debian13`, `centos9`, `centos10`, `redos8`, `redos9`.
  - Подтверждена доступность Debian/CentOS репозиториев для выгрузки пакетов.

### Шаг 2. Реализация инструментов выгрузки
- **Статус**: Завершена
- **Описание**:
  - Обновлен [scripts/fetch_debian_legacy_offline.py](../scripts/fetch_debian_legacy_offline.py):
    - поддержка расширена до `debian13`;
    - добавлен параметр `--releases`.
  - Добавлен [scripts/fetch_rpm_offline.py](../scripts/fetch_rpm_offline.py):
    - разбор `repodata/primary` и расчет closure зависимостей;
    - загрузка RPM-наборов для `centos7..10`;
    - формирование `redos7..9` как alias-наборов.

### Шаг 3. Выгрузка пакетов и обновление mapping
- **Статус**: Завершена
- **Описание**:
  - Выполнена выгрузка `.deb` в `files/packages/debian13/{auditd,audispd-plugins,rsyslog,misc}`.
  - Выполнена выгрузка `.rpm` в `files/packages/centos{7,8,9,10}/{audit,audispd-plugins,rsyslog,misc}`.
  - Сформированы alias-каталоги `files/packages/redos{7,8,9}/...`.
  - В [vars/main.yml](../vars/main.yml) добавлены mapping записи для:
    - `Debian trixie -> debian13`,
    - `CentOS 9/10 -> centos9/centos10`,
    - `REDOS/RED 8/9 -> redos8/redos9`.

### Шаг 4. Документация и валидация
- **Статус**: Завершена
- **Описание**:
  - Актуализированы [README.md](../README.md), [docs/CONFIGURATION.md](./CONFIGURATION.md), [docs/RUNBOOK.md](./RUNBOOK.md), [docs/PROJECT_ANALYSIS.md](./PROJECT_ANALYSIS.md), [CHANGELOG.md](../CHANGELOG.md), [docs/changelog.md](./changelog.md).
  - Выполнена валидация скриптов: `python3 -m py_compile scripts/fetch_debian_legacy_offline.py scripts/fetch_rpm_offline.py`.
  - `ansible-playbook --syntax-check` не запускался: отсутствует `ansible-playbook` в окружении.

### Шаг 5. Git hygiene для служебных файлов
- **Статус**: Завершена
- **Описание**:
  - Добавлен [.gitignore](../.gitignore) с правилами для `.DS_Store` и `__pycache__`.
  - Удалены уже попавшие в git служебные файлы `.DS_Store` из `files/` и `files/packages/`.

### Текущий статус
- **Общий статус задачи**: Завершена
- **Оставшиеся шаги**:
  - По запросу: добавить отдельные native-REDOS источники в загрузчик при доступности внутреннего mirror RedOS.
