BMRA_DIRECTORIES_WITH_SHELL_FILES ?= roles/ examples/ playbooks/infra/ playbooks/intel/

shellcheck:
	find $(BMRA_DIRECTORIES_WITH_SHELL_FILES) -type f \( -name '*.sh' -o -name '*.bash' -o -name '*.ksh' -o -name '*.bashrc' -o -name '*.bash_profile' -o -name '*.bash_login' -o -name '*.bash_logout' \) \
    | xargs shellcheck

ansible-lint:
	ansible-lint playbooks/* roles/* -c .ansible-lint

profile ?= ''
bmra-profiles:
	python3 profiles/render.py --config profiles/profiles.yml --host profiles/host_vars.j2 --group profiles/group_vars.j2 --inventory profiles/inventory.j2 --output examples -p $(profile)
