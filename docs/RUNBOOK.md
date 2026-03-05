# Runbook: запуск, проверка, откат

## 1. Подготовка

1. Проверить доступность хостов из inventory.
2. Убедиться, что на целевых хостах есть python и права `become`.
3. Проверить актуальность SIEM-агентов в [vars/siem_agents.yml](../vars/siem_agents.yml).
4. При необходимости задать `facility` на host/group-уровне.

## 2. Запуск

Полный запуск:
```bash
ansible-playbook playbook.yml
```

Локальный запуск:
```bash
ansible-playbook playbook_local.yml
```

Пробный прогон (без изменений):
```bash
ansible-playbook playbook.yml --check
```

Запуск только конфигурации:
```bash
ansible-playbook playbook.yml --tags configure
```

## 2.1 Подготовка полностью закрытого контура (offline bundles)

На хосте с доступом в интернет выполните:

```bash
python3 scripts/fetch_debian_legacy_offline.py --releases all
python3 -u scripts/fetch_rpm_offline.py --releases centos7,centos8,centos9,centos10,redos7,redos8,redos9
```

После выгрузки перенесите каталог `files/packages/` в закрытый контур вместе с ролью.
Примечание: для `REDOS/RED 7..9` используются совместимые CentOS-бандлы.

## 3. Пост-проверки на хосте

### Проверка сервисов
```bash
systemctl status auditd
systemctl status rsyslog || systemctl status syslog-ng
```

### Проверка правил auditd
```bash
auditctl -l
ls -l /etc/audit/rules.d/00-siem.rules
```

### Проверка вывода audispd
```bash
grep -E '^active|^args' /etc/audisp/plugins.d/syslog.conf 2>/dev/null || true
grep -E '^active|^args' /etc/audit/plugins.d/syslog.conf 2>/dev/null || true
```

### Проверка пересылки в SIEM
`rsyslog`:
```bash
grep -n "10-siem.conf" /etc/rsyslog.conf /etc/rsyslog.d/10-siem.conf 2>/dev/null
```

`syslog-ng`:
```bash
grep -n "10-siem.conf" /etc/syslog-ng/syslog-ng.conf /etc/syslog-ng/10-siem.conf 2>/dev/null
```

## 4. Диагностика

### Роль остановилась с сообщением "Linux distribution ... is not supported"
- Проверить фактические `ansible_distribution` и `ansible_distribution_major_version`.
- Сверить с `linux_supported` в [vars/main.yml](../vars/main.yml).

### Пакет не ставится из репозитория
- Проверить сетевой доступ к mirror/repo.
- Если нужен офлайн-режим: `upload_local_packages: true`.
- Проверить, что каталог пакетов для вашей ОС существует в `files/packages/`.

### Не определяется syslog-демон
- Логика использует `service_facts` и анализ установленных unit-файлов (`rsyslog`/`syslog-ng`).
- Если ни один daemon не обнаружен, роль ставит `rsyslog`.

## 5. Откат

Прямого автоматизированного rollback нет. Используйте:
1. Снимки/backup на уровне инфраструктуры.
2. Восстановление ключевых конфигов:
   - `/etc/audit/auditd.conf`
   - `/etc/audit/rules.d/*.rules`
   - `/etc/rsyslog.conf`, `/etc/rsyslog.d/10-siem.conf`
   - `/etc/syslog-ng/syslog-ng.conf`, `/etc/syslog-ng/10-siem.conf`
3. Перезапуск сервисов после восстановления.

Примечание:
- Роль делает backup старых правил audit в `rules_backup.tar` внутри `auditd_rules_dir`.

## 6. Безопасная эксплуатация

1. Не хранить production inventory с реальными IP в публичных репозиториях.
2. Проверять изменения шаблонов на стенде перед production.
3. Регулярно обновлять офлайн-пакеты в `files/packages/`.
4. Планово внедрить CI-проверки (`ansible-lint`, smoke-test на тестовом хосте).
