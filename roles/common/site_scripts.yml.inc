---

- name: Site scripts are copied
  copy:
  args:
    dest: /root/{{ item.filename }}
    mode: "a+x"
    # This will look in role/files directory first
    src: "{{ item.filename }}"
  when: item.filename != None and
        item.filename != ""
  with_items: site_scripts

- name: Site scripts are executed
  command: /root/{{ item.filename }}
  args:
    creates: "{{ item.creates | default(omit) }}"
    removes: "{{ item.removes | default(omit) }}"
  register: site_scripts_results
  when: item.filename != None and
        item.filename != ""
  with_items: site_scripts

- debug: var=site_script_results
  when: site_script_results is defined

- name: Avoid running site script twice
  set_fact:
    site_scripts:
        - { filename: "" }
  when: site_script_results is defined
