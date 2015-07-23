---

- name: Site scripts are copied
  copy:
  args:
    dest: "{{ item.chdir | default('/root') }}/{{ item.filename }}"
    mode: "a+x"
    # This will look in role/files directory first
    src: "{{ item.srcpath }}/{{ item.filename }}"
  when: item.filename != None and
        item.filename != ""
  with_items: site_scripts

- name: Site scripts are executed
  command: "{{ item.chdir | default('/root') }}/{{ item.filename }} \
            {{ item.args | default(omit) }}"
  args:
    creates: "{{ item.creates | default(omit) }}"
    removes: "{{ item.removes | default(omit) }}"
    chdir: "{{ item.chdir | default('/root') }}"
    executable: "{{ item.executable | default(omit) }}"
  register: site_scripts_results
  when: item.filename != None and
        item.filename != ""
  with_items: site_scripts

- debug: var=site_script_results
  when: site_script_results is defined

- name: Set reboot flag when site scripts were executed
  set_fact:
    needs_reboot: true
  when: item | changed
  with_items: site_scripts_results.results
