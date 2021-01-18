FROM centos:7.9.2009
USER root
WORKDIR /root/
# 需要当前目录下有Python-3.7.9.tgz和pip.conf文件
COPY ./ /root/project/
RUN set -ex \
    && rm -f /bin/sh && ln -s /bin/bash /bin/sh \
    # 修改yum源
    && rm -f /etc/yum.repos.d/CentOS-Base.repo \
    && curl -o /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-7.repo \
    && yum makecache \
    # 安装python3.7.9
    && yum install -y git vim gcc make patch gdbm-devel openssl-devel sqlite-devel readline-devel zlib-devel bzip2-devel libffi-devel \
    && mkdir -p /usr/local/python3 && mv /root/project/Python-3.7.9.tgz /usr/local/python3/ \
    && cd /usr/local/python3/ && tar -xzf Python-3.7.9.tgz \
    && cd ./Python-3.7.9/ \
    && ./configure prefix=/usr/local/python3/ \
    && make && make install && make clean \
    && rm -f ../Python-3.7.9.tgz /root/project/Dockerfile \
    && ln -s /usr/local/python3/bin/python3.7 /usr/local/bin/python3 \
    && ln -s /usr/local/python3/bin/pip3 /usr/local/bin/pip3 \
    && mkdir /root/.pip && mv /root/project/pip.conf /root/.pip/ \
    && pip3 install --upgrade pip \
    && pip3 install -r /root/project/requirement.txt \
    # 修改系统时区为东八区
    && rm -rf /etc/localtime \
    && ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    # 支持中文
    && yum install -y kde-l10n-Chinese \
    && localedef -c -f UTF-8 -i zh_CN zh_CN.UTF-8 \
    && echo -e "LANG=\"zh_CN.UTF-8\"\nLC_ALL=\"zh_CN.UTF-8\"" > /etc/locale.conf
ENV LANG zh_CN.UTF-8
ENV LC_ALL zh_CN.UTF-8
CMD ["/bin/bash", "-ce", "tail -f /dev/null"]
