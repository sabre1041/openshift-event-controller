FROM centos/python-35-centos7

USER root

ENV PATH=/opt/app-root/bin:/opt/rh/rh-python35/root/usr/bin:/opt/app-root/src/.local/bin/:/opt/app-root/src/bin:/opt/app-root/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    LD_LIBRARY_PATH=/opt/rh/rh-python35/root/usr/lib64 \
    ORIGIN_CLIENT=https://github.com/openshift/origin/releases/download/v3.6.0/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit.tar.gz

RUN yum -y install libffi-devel; \
  pip install --upgrade pip; \
  pip install requests pkiutils pyopenssl; \
  yum clean all;

RUN mkdir -p /opt/event-controller

COPY ./src/ /opt/event-controller/

COPY ./bin/ /opt/event-controller/bin

RUN wget -O $HOME/origin-client.tar.gz $ORIGIN_CLIENT && \
    tar -xzf $HOME/origin-client.tar.gz -C $HOME && \
    cp $HOME/openshift-origin-client-tools-v3.6.0-c4dd4cf-linux-64bit/oc /usr/bin/oc && \
    chown -R 1001:1001 /opt/event-controller

USER 1001

ENTRYPOINT ["/opt/event-controller/bin/start.sh"]
