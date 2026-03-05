# Конфигурация проекта

## 1. Точки входа

- Инвентори по умолчанию: [inventory/hosts](../inventory/hosts)
- Конфигурация ansible: [ansible.cfg](../ansible.cfg)
- Плейбуки:
  - [playbook.yml](../playbook.yml)
  - [playbook_local.yml](../playbook_local.yml)

## 2. Переменные по умолчанию

Файл: [defaults/main.yml](../defaults/main.yml)

| Переменная | Значение по умолчанию | Назначение |
|---|---|---|
| `facility` | `default` | Выбор группы SIEM-агентов из `vars/siem_agents.yml` |

## 3. Основные переменные роли

Файл: [vars/main.yml](../vars/main.yml)

| Переменная | Тип | Значение по умолчанию | Назначение |
|---|---|---|---|
| `upload_local_packages` | bool | `true` | Разрешить fallback на локальные пакеты |
| `auditd_write_logs` | bool | `false` | Запись audit-логов локально (`write_logs`) |
| `modify_etc_hosts` | bool | `false` | Включает блок модификации `/etc/hosts` |
| `syslog_options` | regex string | `rsyslog\|syslog-ng` | Определение имени активного syslog-процесса |
| `linux_supported` | list | см. файл | Белый список поддерживаемых дистрибутивов |
| `packages_dirs` | map | см. файл | Соответствие ОС -> каталоги офлайн-пакетов |

Также задаются пути конфигов для:
- `auditd` (`auditd_config`, `auditd_rules_dir`, ...),
- `audispd` (`audispd_plugin_config_v2`, `audispd_plugin_config_v3`),
- `rsyslog`/`syslog-ng` (`rsyslog_config`, `syslog_ng_config`, ...).

## 4. SIEM-агенты и facility-группы

Файл: [vars/siem_agents.yml](../vars/siem_agents.yml)

Структура:
```yaml
facilities:
  default:
    - { address: 'mpxagent01.example.com', transport: 'udp', port: '514' }
```

Выбор группы:
- по умолчанию используется `facility=default`;
- можно переопределить `facility` на host/group-уровне в inventory.

## 5. Шаблоны конфигурации

### `auditd_00-siem.rules.j2`
Файл: [templates/auditd_00-siem.rules.j2](../templates/auditd_00-siem.rules.j2)
- Загружает SIEM-ориентированный набор audit-правил.
- Использует `uid_min`, полученный из `/etc/login.defs`.

### `rsyslog_10-siem.conf.j2`
Файл: [templates/rsyslog_10-siem.conf.j2](../templates/rsyslog_10-siem.conf.j2)
- Для каждого агента facility-группы генерирует action с `omfwd`.
- Поддерживает `udp` и `tcp`.
- При `auditd_write_logs: false` добавляет `local6.* stop`.

### `syslog-ng_10-siem.conf.j2`
Файл: [templates/syslog-ng_10-siem.conf.j2](../templates/syslog-ng_10-siem.conf.j2)
- Создает `destination`/`log`-блоки на каждый SIEM-агент.
- Поддерживает `udp` и `tcp`.

## 6. Поддерживаемые платформы

Источник: `linux_supported` из [vars/main.yml](../vars/main.yml)

- RedHat 7-9
- CentOS 7-10
- OracleLinux 7-9
- Debian 6-13
- Ubuntu 16-24
- Astra Linux 1-2
- REDOS 7-9
- RED 7-9
- Altlinux 10

Примечание:
- Локальные офлайн-пакеты в `files/packages` доступны для:
  - Debian `6..13`,
  - CentOS `7..10`,
  - REDOS/RED `7..9`.
- Для REDOS/RED `7..9` используются совместимые CentOS-бандлы (alias-каталоги `redos7/8/9`).
- Для AstraLinux оффлайн-мэппинг расширен на основные релизы `1.5/1.6/1.7/1.8/2.12`:
  - `1.7` использует `astra17` bundle;
  - другие релизы используют Debian-совместимые bundles (`debian9`/`debian12`) в режиме compatibility.
- Для других supported ОС и версий, не имеющих локального mapping, роль требует установку из репозиториев или добавление собственных локальных пакетов.

## 7. Переопределение переменных

Рекомендуемый порядок (Ansible precedence):
1. `group_vars` / `host_vars`;
2. переменные inventory;
3. `--extra-vars` при запуске.

Пример:
```bash
ansible-playbook playbook.yml -e "facility=default auditd_write_logs=true"
```
