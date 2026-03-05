# PT_LEP_unix

Ansible-роль для настройки Linux-хостов под сбор и пересылку событий в SIEM:
- установка и настройка `auditd`;
- настройка `audispd-plugins` для вывода событий в `local6`;
- настройка `rsyslog` или `syslog-ng` для пересылки в SIEM-агенты;
- поддержка установки пакетов из репозиториев и офлайн-режима (локальные `.deb/.rpm`).

Документация проекта:
- [Архитектура](docs/ARCHITECTURE.md)
- [Конфигурация](docs/CONFIGURATION.md)
- [Runbook (запуск и проверка)](docs/RUNBOOK.md)
- [Анализ проекта](docs/PROJECT_ANALYSIS.md)
- [Code review](docs/CODE_REVIEW.md)
- [Рабочий трекер задач](docs/tasktracker.md)
- [Рабочий журнал изменений документации](docs/changelog.md)
- [История релизов](CHANGELOG.md)

## 1. Быстрый старт

### Требования
- Ansible 2.12+.
- Python на целевых хостах.
- Права `become` (роль меняет системные конфиги и сервисы).
- Для AltLinux при установке `rsyslog-classic` нужна коллекция `community.general`.

### Минимальный запуск
```bash
ansible-playbook playbook.yml
```

Локальный запуск на текущем хосте:
```bash
ansible-playbook playbook_local.yml
```

### Теги
- `install` - установка пакетов;
- `configure` - настройка конфигурации;
- `auditd`, `syslog`, `system`, `pt` - функциональные срезы.

Пример:
```bash
ansible-playbook playbook.yml --tags "install,auditd"
```

## 2. Что делает роль

1. Проверяет, что ОС и версия поддерживаются (`vars/main.yml -> linux_supported`).
2. Настраивает системные параметры (опционально корректирует `/etc/hosts`).
3. Устанавливает `tar`, `auditd`, `audispd-plugins`.
4. Настраивает правила `auditd` (шаблон `templates/auditd_00-siem.rules.j2`).
5. Настраивает плагин `audispd` для отправки в `local6`.
6. Определяет активный syslog-демон:
   - если найден `rsyslogd` -> настраивает `rsyslog`;
   - если найден `syslog-ng` -> настраивает `syslog-ng`;
   - если не найден -> устанавливает и настраивает `rsyslog`.
7. Перезапускает сервисы (`auditd`, `rsyslog`, `syslog-ng`, `systemd-journald` по условиям).

## 3. Ключевые переменные

Определены в [vars/main.yml](vars/main.yml) и [defaults/main.yml](defaults/main.yml):
- `facility` (default: `default`) - группа SIEM-агентов;
- `upload_local_packages` (default: `true`) - разрешить fallback на локальные пакеты;
- `auditd_write_logs` (default: `false`) - писать ли audit-события локально;
- `modify_etc_hosts` (default: `false`) - модификация `/etc/hosts` (режим только для осознанного использования).

Группы SIEM-агентов задаются в [vars/siem_agents.yml](vars/siem_agents.yml), а выбор группы можно задавать host/group-переменной `facility` в inventory.

## 4. Поддерживаемые ОС

Роль ориентирована на:
- RedHat 7-9;
- CentOS 7-10;
- OracleLinux 7-9;
- Debian 6-13;
- Ubuntu 16-24;
- Astra Linux 1.7;
- REDOS 7-9;
- RED 7-9;
- Altlinux 10.

Точный список и диапазоны версий: [vars/main.yml](vars/main.yml).

## 5. Структура репозитория

```text
.
├── ansible.cfg
├── playbook.yml
├── playbook_local.yml
├── defaults/
├── vars/
├── tasks/
│   ├── configure/
│   └── install/
│       ├── with_repos/
│       └── without_repos/
├── templates/
├── files/packages/     # офлайн-пакеты
├── inventory/
└── docs/
```

## 6. Важные замечания

- [inventory/hosts](inventory/hosts) в репозитории является sanitized-шаблоном. Для реального контура используйте отдельный приватный inventory-файл.
- В [vars/siem_agents.yml](vars/siem_agents.yml) по умолчанию указан placeholder (`mpxagent01.example.com`), задайте реальные адреса SIEM-агентов перед production-запуском.
- Офлайн-пакеты (`files/packages`) подготовлены для:
  - Debian `6..13` (native `.deb` bundles),
  - CentOS `7..10` (native `.rpm` bundles),
  - REDOS/RED `7..9` (совместимые RPM-наборы, собранные из CentOS-бандлов).
- Для актуализации оффлайн-бандлов используйте:
  - `python3 scripts/fetch_debian_legacy_offline.py --releases all`
  - `python3 -u scripts/fetch_rpm_offline.py --releases centos7,centos8,centos9,centos10,redos7,redos8,redos9`
- `ansible.cfg` задает `roles_path = ../`; для запуска убедитесь, что имя роли и путь в окружении соответствуют этому layout.
- Перед запуском в production проверьте раздел "Риски и техдолг" в [docs/PROJECT_ANALYSIS.md](docs/PROJECT_ANALYSIS.md).
