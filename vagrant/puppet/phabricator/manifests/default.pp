# Basic Puppet Apache manifest

$phab_dir      = "/phabricator"
$dev_dir       = "${phab_dir}/instances/dev"
$document_root = "${dev_dir}/phabricator/webroot"
$std_path      = "/usr/bin:/usr/sbin:/bin"
$http_proxy    = ""
$https_proxy    = ""

file { 'apt-proxyconfig' :
  path    => '/etc/apt/apt.conf.d/95proxies',
  ensure  => present,
  content => "Acquire::http::proxy \"${http_proxy}\";",
  notify  => Exec['apt-update'],
}

exec { 'apt-update':
    command     => 'apt-get update',
    refreshonly => true,
    path        => $std_path,
}

class { 'apache':
      default_mods        => false,
      default_confd_files => false,
      mpm_module => 'prefork',
}

class { '::apache::mod::php': }

apache::mod { 'env': }

  apache::vhost { 'localhost':
    priority => 10,
    port => '80',
    docroot => "${document_root}",
    setenv => [ 'PHABRICATOR_ENV production' ],
    rewrites => [
                 { rewrite_rule => ['^/rsrc/(.*) - [L,QSA]'], },
                 { rewrite_rule => ['^/favicon.ico - [L,QSA]'], },
                 { rewrite_rule => ['^(.*)$ /index.php?__path__=$1 [B,L,QSA]'],},
                ],
  }

class otherpackages {
    $packages = ["git-core", "mysql-server", "php5", "dpkg-dev", "unzip"]
    $php_packages = ["php5-mysql", "php5-gd", "php5-dev", "php5-curl", "php-apc", "php5-cli"]

    package { $packages: ensure     => installed, }
    package { $php_packages: ensure => installed, }
}

class phabricatordirs {
    # puppet won't create parent directories and will fail if we don't
    # manually specify each of them as separate dependencies
    # it does automatically create them in the correct order though
    file { "/phabricator/instances/dev":
        ensure => directory,
    }
    file { "/phabricator/instances":
        ensure => directory,
    }
    file { "/phabricator":
        ensure => directory,
    }
}

class phabricator {

    define phabgithubunzip ($repo = $title, $commit) {
        $proxy_string = "https_proxy=${https_proxy}"
        $github_string = "https://github.com/facebook"
        exec { "wget ${github_string}/${repo}/archive/${commit}.zip -O ${dev_dir}/${repo}.zip --no-check-certificate && unzip ${dev_dir}/${repo}.zip -d ${dev_dir} && mv ${dev_dir}/${repo}-${commit} ${dev_dir}/${repo}":
            path        => $std_path,
            creates     => "${dev_dir}/${repo}",
            environment => $proxy_string,
        }
    }

    # set 'commit' to 'master' for the latest version
    phabgithubunzip {'phabricator': commit => 'df8474d778048a7364b2e332a1e4cae55d93291e'}
    phabgithubunzip {'libphutil': commit => '0b9f193303dfae4f9204d8f577e2bd45acd4963f'}
    phabgithubunzip {'arcanist': commit => '42ae7cd92f92e026bdd604e659d2bc23e9352baa'}
}

class phabricatordb {
    file { "initial.db":
	path   => "${phab_dir}/initial.db",
	source => "puppet:///modules/phabricator/initial.db",
	ensure => present,
    }

    exec { "mysql < ${phab_dir}/initial.db && ${dev_dir}/phabricator/bin/storage upgrade --force":
        path    => $std_path,
        unless  => "${dev_dir}/phabricator/bin/storage status",
	require => File["initial.db"],
    }
}

# declare our entities
class {'otherpackages':}
class {'phabricatordirs':}
class {'phabricator':}
class {'phabricatordb':}

# declare our dependencies
Class['apache'] <- Class['phabricator']
Class['otherpackages'] <- File['apt-proxyconfig']
Class['phabricator']   <- Class['otherpackages']
Class['phabricator']   <- Class['phabricatordirs']
Class['phabricatordb'] <- Class['phabricator']
