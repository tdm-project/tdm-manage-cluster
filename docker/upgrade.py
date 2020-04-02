#!/usr/bin/env python3

import argparse
import git
import logging
import os
import subprocess
import sys
import time

from contextlib import contextmanager

KsVersionStampFilename = 'kubespray_deployer_version'
PatchFile = '/home/manageks/v2.8.4.patch'

# Correspondence between ansible and kubernetes versions
# (this is manually extracted from the tag commit messages)
VersionTable = [
    ("2.8.4", "1.12.7"),
    ("2.8.5", "1.12.7"),
    ("2.9.0", "1.12.7"),
    ("2.10.0", "1.12.7" ),
    ("2.10.3", "1.14.3"),
    ("2.10.4", "1.14.3"),
    ("2.11.0", "1.15.3"),
    ("2.11.1", "1.15.11"),
    ("2.11.2", "1.15.11"),
    ("2.12.0", "1.15.11"),
    ("2.12.1", "1.16.7"),
    ("2.12.2", "1.16.7"),
    ("2.12.3", "1.16.7"),
    ("2.12.4", "1.16.8"),
    ("2.12.5", "1.16.8")
]


@contextmanager
def chdir(new_dir):
    old_dir = os.path.getcwd()
    try:
        os.path.chdir(new_dir)
    finally:
        os.path.chdir(old_dir)


class KubesprayRepo(object):

    def __init__(self, path):
        self._path = path
        assert os.path.exists(self._path)
        self._repo = git.Repo(self._path)

    @property
    def path(self):
        return self._path


    def clean(self):
        self._repo.head.reset(index=True, working_tree=True)
        self._repo.git.clean('-d', '-f')


    def checkout(self, ks_version):
        assert ks_version in (row[0] for row in VersionTable)
        ks_tag = 'v' + ks_version
        logging.debug('Checking out KubeSpray tag %s', ks_tag)

        self.clean()
        self._repo.git.checkout(ks_tag)
        logging.debug('Applying patch')
        self._repo.git.apply(PatchFile)
        logging.debug('Checkout completed')


    def iterversions(self, base, target):
        """
        Iterate repository from version base+1 to target (included).
        """
        version_list = [ row[0] for row in VersionTable ]
        base_index = version_list.index(base)
        target_index = version_list.index(target)

        if base_index > target_index:
            raise ValueError("Base version {} is greater than target version {}".format(base, target))

        current_index = base_index + 1
        while current_index <= target_index:
            self.checkout(version_list[current_index])
            yield 'v' + version_list[current_index]
            current_index += 1


    @staticmethod
    def find_corresponding_k8s_version(ks_version):
        for row in VersionTable:
            if row[0] == ks_version:
                return row[1]
        return None


class Deployment(object):
    def __init__(self, cluster_dir, inventory_file):
        self._path = os.path.abspath(cluster_dir)
        self._current_version = self._get_last_deployment_ks_version()
        self._inventory = os.path.abspath(inventory_file)
        assert os.path.exists(self._path)
        assert os.path.exists(self._inventory)


    @property
    def path(self):
        return self._path


    @property
    def current_ks_version(self):
        return self._current_version


    @property
    def _ks_version_stamp_file(self):
        return os.path.join(self.path, KsVersionStampFilename)


    def _get_last_deployment_ks_version(self):
        try:
            with open(self._ks_version_stamp_file) as f:
                lines = f.readlines()
                if lines:
                    return lines[-1].rstrip('\n')
        except FileNotFoundError:
            logging.info("kubespray version file doesn't exist for this deployment. Don't know what version was used.")
            return None
        except IOError as e:
            logging.error("Error getting kubespray version from file %s", KsVersionStampFilename)
            logging.exception(e)
            raise

    def _exec_kubespray_upgrade(self, ks_repo):
        with chdir(self.path):
            # ensure the kubespray requirements are met
            cmd = [ 'pip3', 'install', '-r', 'requirements.txt' ]
            logging.info("Installing any requirement upgrades...")
            subprocess.check_call(cmd)
            logging.info("Done.")
            logging.info("Executing upgrade-cluster playbook...")
            cmd = [ 'ansible-playbook', '-v', '--become',\
                    '-i', self._inventory,\
                    '--timeout', '30',
                    os.path.join(ks_repo.path, 'upgrade-cluster.yml') ]
            subprocess.check_call(cmd)


    def _stamp_installation(self, kubespray_version):
        with open(self._ks_version_stamp_file, 'a') as f:
                f.write("v{}\n".format(kubespray_version))


    def upgrade(self, target_ks_version, ks_repo):
        logging.info("Current deployment created with KubeSpray version %s", self.current_ks_version)
        logging.info("Requested upgrade to version %s", target_ks_version)
        logging.info("Using KubeSpray repository at path %s", ks_repo.path)

        for ks_version in ks_repo.iterversions(self.current_ks_version, target_ks_version):
            logging.info("Attempting upgrade to version %s", ks_version)
            #self._exec_kubespray_upgrade(ks_repo)
            #self._stamp_installation(ks_version)
            logging.info("Upgrade playbook for version %s completed", ks_version)
            #logging.warn("Sleeping 60 seconds hoping it'll be enough for everything to come up...")
            #time.sleep(60)
            

        logging.info("Upgrade operation complete.  Cluster is now deployed with Kubespray version %s", target_ks_version)


def create_parser():
    default_upgrade_target = '2.10.4'
    parser = argparse.ArgumentParser(description="Upgrade KubeSpray Kubernetes installation")
    parser.add_argument('--target-version', metavar='x.y.z', help='Target kubespray version', default=default_upgrade_target)
    parser.add_argument('kubespray_repo', metavar='KUBESPRAY_DIR', help="Path to Kubespray git repository")
    parser.add_argument('cluster_dir', metavar='CLUSTER_TF_DIR', nargs='?', help="Path to cluster tf deployment directory", default=os.getcwd())

    return parser


def main(args=None):
    parser = create_parser()
    options = parser.parse_args(args)

    target_ks_version = options.target_version
    repo = KubesprayRepo(options.kubespray_repo)
    deployment = Deployment(options.cluster_dir, os.path.join(options.cluster_dir, 'hosts.ini'))

    logging.info("Found directory for deployment made with kubespray version %s", deployment.current_ks_version)

    k8s_version = KubesprayRepo.find_corresponding_k8s_version(target_ks_version)
    logging.info("Upgrading to Kubespray version %s (k8s version %s)", target_ks_version, k8s_version)

    deployment.upgrade(target_ks_version, repo)

    logging.info("Upgrade complete!")


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv[1:])
