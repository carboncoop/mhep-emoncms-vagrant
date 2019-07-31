#!/bin/bash -eux

# See:
# * https://github.com/emoncms/emoncms/blob/stable/docs/LinuxInstall.md
# * https://github.com/emoncms/MyHomeEnergyPlanner/blob/master/.travis.yml
# * https://github.com/emoncms/MyHomeEnergyPlanner/tree/development


update_package_index() {
  if [ ! -f "/var/run/initial_apt_update_ok" ]; then
    sudo apt-get update
    touch /var/run/initial_apt_update_ok
  fi
}

install_mysql() {
  MYSQL_ROOT_PASSWORD=foo
  debconf-set-selections <<< "mysql-server mysql-server/root_password password $MYSQL_ROOT_PASSWORD"
  debconf-set-selections <<< "mysql-server mysql-server/root_password_again password $MYSQL_ROOT_PASSWORD"
  DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server

  apt install -y \
    mysql-client \
    libapache2-mod-php
}

install_php_7_2() {
  # https://github.com/emoncms/emoncms/blob/master/docs/LinuxInstall.md
  # note: no need to configure PECL or Redis

  sudo apt-get install -y \
    apache2 \
    php \
    php-mysql \
    php-curl \
    php-pear \
    php-dev \
    php-json \
    git-core \
    build-essential \
    php7.2-mbstring
}

install_additional_packages() {
    sudo apt-get install -y \
	ack-grep \
        dos2unix \
	git \
	htop \
	make \
	nfs-common \
	run-one \
	sqlite3 \
	tree \
	unzip \
	whois \
	zip
}

install_emoncms() {
  if [ ! -d "/var/www/html/emoncms/.git" ]; then
    chown vagrant /var/www/html/emoncms

    run_as_vagrant "git clone -b stable https://github.com/emoncms/emoncms.git /var/www/html/emoncms"

    # latest commit on `stable` branch at time of writing:
    # https://github.com/emoncms/emoncms/commit/a0c672e4dbf7989d79b00758d5c7a0841e6dce8d
    run_as_vagrant "cd /var/www/html/emoncms && git checkout a0c672e4dbf7989d79b00758d5c7a0841e6dce8d"
  fi

  mkdir -p /var/log/emoncms
  touch /var/log/emoncms.log
  chown -R www-data:adm /var/log/emoncms
}

create_emoncms_database() {
  if [ ! -f "/root/created_mysql_emoncms" ]; then
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e 'CREATE DATABASE IF NOT EXISTS emoncms DEFAULT CHARACTER SET utf8;'
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "CREATE USER 'emoncms'@'localhost' IDENTIFIED BY 'emoncms';"
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "GRANT ALL ON emoncms.* TO 'emoncms'@'localhost';"
    mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "flush privileges;"

    touch "/root/created_mysql_emoncms"
  fi
}

install_database_dump() {
  if [ ! -f "/root/installed_database_dump" ]; then
    run_as_vagrant "mysql < /vagrant/vagrant/example_data.sql"
  fi
}


configure_emoncms_settings_php() {
  cp /var/www/html/emoncms/default.settings.php /var/www/html/emoncms/settings.php

  sed -i 's|$server = .*;|$server = "localhost";|g' /var/www/html/emoncms/settings.php
  sed -i 's|$database = .*;|$database = "emoncms";|g' /var/www/html/emoncms/settings.php
  sed -i 's|$username = .*;|$username = "emoncms";|g' /var/www/html/emoncms/settings.php
  sed -i 's|$password = .*;|$password = "emoncms";|g' /var/www/html/emoncms/settings.php
}

install_emoncms_mhep_theme() {
  if [ ! -d "/var/www/html/emoncms/Theme/CCoop" ]; then
    run_as_vagrant "cd /var/www/html/emoncms/Theme && git clone --depth=3 https://github.com/carboncoop/MHEP_theme.git CCoop"
    run_as_vagrant "cd /var/www/html/emoncms/Theme/CCoop && git checkout c65e083ef9f072e4c9d5af7ec0e98942a59d0a06"
  fi

  sed -i 's/$theme = "basic";/$theme = "CCoop";/g' /var/www/html/emoncms/settings.php
}

install_assessment_module() {
  if [ ! -d "/var/www/html/emoncms/Modules/assessment" ]; then
    run_as_vagrant "cd /var/www/html/emoncms/Modules && git clone -b development https://github.com/paulfurley/MyHomeEnergyPlanner.git assessment"
    run_as_vagrant "cd /var/www/html/emoncms/Modules/assessment && git checkout cfab04784a1e7559358556f615ebcf57178b9864"
  fi

  if ! grep 'MHEP_image_gallery' /var/www/html/emoncms/settings.php ; then
    echo "\$MHEP_image_gallery = true; // If true then the image gallery will be available" >> /var/www/html/emoncms/settings.php
  fi

  if ! grep 'MHEP_key' /var/www/html/emoncms/settings.php ; then
    # empty key: disable encryption
    echo '// note: MHEP_key not set: disable encryption' >> /var/www/html/emoncms/settings.php
  fi

   ## Change ownership of images directory to allow MHEP save pictures
   chown :www-data /var/www/html/emoncms/Modules/assessment/images
   chmod 774 /var/www/html/emoncms/Modules/assessment/images
}

install_openfuvc() {
  run_as_vagrant "cd /var/www/html/emoncms/Modules/assessment && git submodule init && git submodule update"
}

add_emoncms_apache_config() {
  # https://github.com/emoncms/emoncms/blob/master/docs/LinuxInstall.md#configure-apache

  a2enmod rewrite
  cat <<EOF >> /etc/apache2/sites-available/emoncms.conf
<Directory /var/www/html/emoncms>
    Options FollowSymLinks
    AllowOverride All
    DirectoryIndex index.php
    Order allow,deny
    Allow from all
</Directory>
EOF

  if ! grep 'ServerName localhost' /etc/apache2/apache2.conf ; then
    echo "ServerName localhost" | tee -a /etc/apache2/apache2.conf 1>&2
  fi

  if [ ! -s "/etc/apache2/sites-enabled/emoncms.conf" ]; then
    a2ensite emoncms
  fi
  service apache2 reload
}

configure_ack() {
    sudo dpkg-divert --local --divert /usr/bin/ack --rename --add /usr/bin/ack-grep
}

install_symlinks() {
    ln -sf /vagrant/vagrant/bashrc /home/vagrant/.bashrc
    ln -sf /vagrant/vagrant/my.cnf /home/vagrant/.my.cnf
}

atomic_download() {
    URL=$1
    DEST=$2

    TMP="$(tempfile)"

    wget -qO "${TMP}" "${URL}" && mv "${TMP}" "${DEST}"
}

run_as_vagrant() {
  su vagrant bash -l -c "$1"
}


install_symlinks
update_package_index
install_mysql
install_php_7_2
install_additional_packages
install_emoncms
create_emoncms_database
install_database_dump
configure_emoncms_settings_php
install_emoncms_mhep_theme
install_assessment_module
install_openfuvc
add_emoncms_apache_config

set +x
echo
echo "All done!"
echo
echo "Now open:"
echo "http://localhost:8080/emoncms"
