# Usage of Mirror Links for Deployment

User can set mirror links for image and package repositories as well as URLs for binaries downloaded during kubespray deployment. To set up mirrors correctly, please follow steps below:

## Generate group vars with mirror links as parameters

To generate mirror links in group vars for any profile, set MIRRORS=true for make command during profile generation. 
Example:

```bash
    make k8s-profile PROFILE=full_nfv ARCH=spr NIC=cvl MIRRORS=true
```

## Set correct values for mirror links and file URLs

After profile generation, all available mirror links and urls are defined `group_vars/all.yml`.
Please make following changes to the mirrors parameters:

- comment parameters that are not required for your target configuration e.g comment Ubuntu repositories if target OS is RedHat.
- update values to desired links so that all mirrors work. Default values represent original URLs used.

## Patch kubespray to use defined mirror urls

To patch kubespray to work with mirror URls run following:

```bash
    ansible-playbook -i inventory.ini playbooks/k8s/patch_mirrors.yml
```

Please remove patch from kubespray before atempting to run deployment without mirrors configured. Patch can be removed by reset of kubespray submodule:

```bash
    git submodule update --force
```
