# Tool to extract SW version from CEK code

## Output of this tool to be used as input for BOM generation

In order to extract SW versions system should be configured for deployment.
group_vars and host_vars needs to be generated for expected profile.

Follow README.md up to point 10. The deployment itself is not needed, so we do not need target machines anailable.

To start tool execute `ansible-playbook`.

    ```bash
    ansible-playbook -i inventory.ini playbooks/versions.yml
    or
    ansible-playbook playbooks/versions.yml
    ```

Software component versions are generated to csv file versions_output.csv
Possible errors are generated to file versions_parsing_errors
Both files are located in project dir:
    ```bash
    versions_output_file: "{{ playbook_dir }}/../versions_output.csv"
    versions_parsing_errors_file: "{{ playbook_dir }}/../versions_parsing_errors"
    ```
