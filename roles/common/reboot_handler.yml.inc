---
- name: The needs_reboot flag is set because of install or package update
  set_fact:
    needs_reboot: true
