.DEFAULT_GOAL := help

POWERSHELL := powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File scripts/dev.ps1

.PHONY: help start dev up stop down restart status logs test install db-migrate db-seed data-import review-import

help:
	@$(POWERSHELL) help

start dev up:
	@$(POWERSHELL) start

stop down:
	@$(POWERSHELL) stop

restart:
	@$(POWERSHELL) restart

status:
	@$(POWERSHELL) status

logs:
	@$(POWERSHELL) logs

test:
	@$(POWERSHELL) test

install:
	@$(POWERSHELL) install

db-migrate:
	@$(POWERSHELL) db-migrate

db-seed:
	@$(POWERSHELL) db-seed

data-import:
	@$(POWERSHELL) data-import

review-import:
	@$(POWERSHELL) review-import
