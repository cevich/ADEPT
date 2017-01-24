FROM docker.io/stackbrew/centos:latest
MAINTAINER Chris Evich <cevich@redhat.com>

RUN yum update -y && \
    yum install -y findutils epel-release https://rdoproject.org/repos/rdo-release.rpm && \
    # Keep every layer as clean (i.e. small) as possible
    yum clean all

# N/B: Use Ansible 2.1.0 until 2.1.2 is available b/c of:
#      https://github.com/ansible/ansible/issues/15915

ADD /files/slave.rpms /root/

RUN xargs -a /root/slave.rpms yum install -y && \
    rm -f /root/slave.rpms && \
    rm -rf /usr/src /usr/share/doc && \
    yum clean all

RUN yum install -y python-pip python-devel && \
    # Allow later removal of this and all subsequent transactions
    yum history | \
        awk -r -F '|' -e '/^ +[0-9]+ +/{print $1}' | \
        tr -d '[:blank:]' | \
        head -1 > /root/trans_num && \
    yum groupinstall -y 'Development Tools' && \
    # Very specific version is required for older Openstack Env.
    pip install --no-cache-dir --disable-pip-version-check shade==1.12.1 && \
    # Keep every layer as clean (i.e. small) as possible
    yum history -y undo $(cat /root/trans_num) && \
    rm -f /root/trans_num && \
    yum clean all && \
    rm -rf /usr/src /usr/share/doc

RUN echo "" > /etc/ansible/hosts && \
    mkdir -p /etc/openstack && \
    ln -s /var/lib/workspace/clouds.yml /etc/openstack/

VOLUME ["/var/lib/adept", "/var/lib/workspace"]
WORKDIR /var/lib/workspace
ENTRYPOINT ["/var/lib/adept/adept.py"]
