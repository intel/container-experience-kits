CEK_DIRECTORIES_WITH_SHELL_FILES ?= roles/ examples/ playbooks/infra/ playbooks/intel/
ARCH ?= 'icx'
NIC ?= 'cvl'
MIRRORS ?= false
PLAYBOOKS_DIRS = playbooks playbooks/infra playbooks/intel
PLAYBOOK_NAMES = access basic full_nfv on_prem on_prem_vss on_prem_sw_defined_factory on_prem_aibox regional_dc remote_fp build_your_own

# set default target available with simple 'make' command
.DEFAULT_GOAL := examples

.PHONY: shellcheck ansible-lint all-profiles clean clean-playbooks help k8s-profiles vm-profiles cloud-profiles

shellcheck:
	find $(CEK_DIRECTORIES_WITH_SHELL_FILES) -type f \( -name '*.sh' -o -name '*.bash' -o -name '*.ksh' -o -name '*.bashrc' -o -name '*.bash_profile' -o -name '*.bash_login' -o -name '*.bash_logout' \) \
    | xargs shellcheck

ansible-lint:
	ansible-lint playbooks/* roles/* -c .ansible-lint

# make sure PROFILE is set to an 'all_examples' string for 'examples' and empty target
ifeq ($(MAKECMDGOALS), $(filter $(MAKECMDGOALS),examples ''))
override PROFILE = 'all_examples'
endif

# make sure PROFILE is defined for mode-related targets
ifndef PROFILE
ifeq ($(MAKECMDGOALS), $(filter $(MAKECMDGOALS),k8s-profile vm-profile cloud-profile))
$(error please specify which profile should be generated, e.g. PROFILE=basic. Run 'make help' for more information.)
endif
endif

examples: k8s-profile vm-profile cloud-profile

k8s-profile: clean-playbooks
	python3 generate/render.py \
	--config generate/profiles_templates/k8s/profiles.yml \
	--host generate/profiles_templates/common/host_vars.j2 \
	--group generate/profiles_templates/common/group_vars.j2 \
	--inventory generate/profiles_templates/k8s/inventory.j2 \
	--output examples/k8s \
	--mode k8s \
	-p $(PROFILE) \
	-a $(ARCH) \
	-n ${NIC} \
	-m ${MIRRORS}

vm-profile: clean-playbooks
	python3 generate/render.py \
	--config generate/profiles_templates/vm/vm_host_profiles.yml \
	--vmsconfig generate/profiles_templates/vm/vms_profiles.yml \
	--host generate/profiles_templates/common/host_vars.j2 \
	--group generate/profiles_templates/common/group_vars.j2 \
	--inventory generate/profiles_templates/vm/inventory.j2 \
	--output examples/vm \
	--mode vm \
	-p $(PROFILE) \
	-a $(ARCH) \
	-n ${NIC} \
	-m ${MIRRORS}

cloud-profile: clean-playbooks
	python3 generate/render.py \
	--config generate/profiles_templates/cloud/profiles.yml \
	--host generate/profiles_templates/common/host_vars.j2 \
	--group generate/profiles_templates/common/group_vars.j2 \
	--inventory generate/profiles_templates/cloud/inventory.j2 \
	--output examples/cloud \
	--mode cloud \
	-p $(PROFILE) \
	-a $(ARCH) \
	-n ${NIC} \
	-m ${MIRRORS}

clean: clean-playbooks clean-project-root-dir

clean-backups:
	rm -rf backups

clean-project-root-dir:
	rm -rf examples host_vars group_vars inventory.ini

clean-playbooks:
	for d in $(PLAYBOOKS_DIRS) ; do for n in $(PLAYBOOK_NAMES) ; do rm -f $$d/$$n.yml ; done done

help:
	@echo "Cleaning targets:"
	@echo "    clean                                   - removes examples directory,"
	@echo "                                              all host_vars and group_vars dirs,"
	@echo "                                              inventory files and playbooks"
	@echo ""
	@echo "    clean-backups                           - clean generated backup files."
	@echo ""
	@echo "Genertare example profiles:"
	@echo "    make, examples                          - generate sample files of all available profiles."
	@echo ""
	@echo "Generating k8s profile:"
	@echo "    k8s-profile PROFILE=<profile_name>      - generate files required for deployment of specific profile in k8s mode."
	@echo ""
	@echo "Generating VM profile:"
	@echo "    vm-profile PROFILE=<profile_name>       - generate files required for deployment of specific profile in vm mode."
	@echo ""
	@echo "Generating Cloud profile:"
	@echo "    cloud-profile PROFILE=<profile_name>    - generate files required for deployment of specific profile in cloud mode."
	@echo ""
	@echo "For more information about:"
	@echo "		- profiles generation"
	@echo "		- supported architectures"
	@echo "		- available profiles"
	@echo "please read the docs/generate_profiles.md file."
