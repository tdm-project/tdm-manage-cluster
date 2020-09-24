#!/usr/bin/env python3

import argparse
import git
import logging
import os
import subprocess
import sys
import time

from contextlib import contextmanager

DefaultKubesprayVersion = os.getenv('DEFAULT_KUBESPRAY_VERSION', '2.14.0')

KsVersionStampFilename = 'kubespray_deployer_version'
PatchFilenameTemplate = '/home/manageks/kubespray_patches/v{}.patch'

# Correspondence between ansible and kubernetes versions
# (this is manually extracted from the tag commit messages)
VersionTable = [
    ("2.8.4", "1.12.7"),
    ("2.8.5", "1.12.7"),
    ("2.9.0", "1.12.7"),
    ("2.10.0", "1.14.3"),
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
    ("2.12.5", "1.16.8"),
    ("2.14.0", "1.18.8")
]


@contextmanager
def chdir(new_dir):
    old_dir = os.getcwd()
    try:
        os.chdir(new_dir)
        logging.debug("Changing directory to %s", new_dir)
        yield
    finally:
        logging.debug("Changing directory back to %s", old_dir)
        os.chdir(old_dir)


class KubesprayRepo(object):

    def __init__(self, path):
        self._path = path
        assert os.path.exists(self._path)
        self._repo = git.Repo(self._path)
        self._requirements_updated = False
        tag = self._repo.git.describe('--tags')
        if tag:
            self._ks_version = tag.lstrip('v')
        else:
            self._ks_version = None


    @property
    def path(self):
        return self._path


    @property
    def ks_version(self):
        return self._ks_version


    def clean(self):
        self._repo.head.reset(index=True, working_tree=True)
        self._repo.git.clean('-d', '-f')


    def checkout(self, ks_version):
        assert ks_version in (row[0] for row in VersionTable)
        self._requirements_updated = False
        ks_tag = 'v' + ks_version
        logging.info('Checking out KubeSpray tag %s', ks_tag)

        self.clean()
        self._repo.git.checkout(ks_tag)
        patch_filename = PatchFilenameTemplate.format(ks_version)
        if os.path.exists(patch_filename):
            logging.debug('Applying patch')
            self._repo.git.apply(patch_filename)
        else:
            logging.debug("Patch file %s doesn't exist.  No patch for this  version", patch_filename)
        logging.debug('Checkout completed')
        self._ks_version = ks_version


    def update_requirements(self, force=False):
        if self._requirements_updated and not force:
            return

        cmd = [ 'pip3', 'install', '-r', os.path.join(self.path, 'requirements.txt') ]
        logging.info("Installing any new requirements...")
        subprocess.check_call(cmd)
        logging.info("Done.")
        self._requirements_updated = True


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
            yield version_list[current_index]
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
                    return lines[-1].split()[0].rstrip('\n')
        except FileNotFoundError:
            logging.debug("kubespray version file doesn't exist for this deployment.")
            return None
        except IOError as e:
            logging.error("Error getting kubespray version from file %s", KsVersionStampFilename)
            logging.exception(e)
            raise

    def _exec_kubespray_upgrade(self, ks_repo):
        with chdir(self.path):
            # ensure the kubespray requirements are met
            ks_repo.update_requirements()
            logging.info("Executing upgrade-cluster playbook...")
            cmd = [ 'ansible-playbook', '-v', '--become',\
                    '-i', self._inventory,\
                    '--timeout', '30',
                    os.path.join(ks_repo.path, 'upgrade-cluster.yml') ]
            logging.debug("Executing command: %s", cmd)
            subprocess.check_call(cmd)


    def _stamp_installation(self, kubespray_version, action):
        with open(self._ks_version_stamp_file, 'a') as f:
                f.write("{} {}\n".format(kubespray_version, action))

    def deploy(self, ks_repo, version):
        logging.info("Deploying Kubernetes with KubeSpray version %s", version)
        logging.info("Using KubeSpray repository at path %s", ks_repo.path)

        ks_repo.checkout(version)
        ks_repo.update_requirements()

        logging.info("Deploying Kubernetes")
        cmd = [ 'ansible-playbook', '-v', '--become',\
                '-i', self._inventory,\
                '--timeout', '30',
                os.path.join(ks_repo.path, 'cluster.yml') ]
        logging.debug("Executing command: %s", cmd)
        subprocess.check_call(cmd)

        self._stamp_installation(version, 'deploy')
        logging.info("Deployment playbook completed")


    def upgrade(self, target_ks_version, ks_repo):
        logging.info("Current deployment created with KubeSpray version %s", self.current_ks_version)
        logging.info("Requested upgrade to version %s", target_ks_version)
        logging.info("Using KubeSpray repository at path %s", ks_repo.path)

        for ks_version in ks_repo.iterversions(self.current_ks_version, target_ks_version):
            logging.info("Attempting upgrade to version %s", ks_version)
            self._exec_kubespray_upgrade(ks_repo)
            self._stamp_installation(ks_version, 'upgrade')
            logging.info("Upgrade playbook for version %s completed", ks_version)
            logging.warn("Sleeping 60 seconds hoping it'll be enough for everything to come up...")
            time.sleep(60)
            

        logging.info("Upgrade operation complete.  Cluster is now deployed with Kubespray version %s", target_ks_version)


def checkout_cmd(ks_repo, options):
    target_ks_version = options.target_version
    ks_repo.checkout(target_ks_version)
    if not options.no_update_requirements:
        ks_repo.update_requirements()


def deploy_cmd(repo, options):
    deployment = _construct_deployment(options)
    target_ks_version = options.target_version
    deployment.deploy(repo, target_ks_version)


def upgrade_cmd(repo, options):
    deployment = _construct_deployment(options)
    target_ks_version = options.target_version
    k8s_version = KubesprayRepo.find_corresponding_k8s_version(target_ks_version)
    logging.info("Upgrading to Kubespray version %s (k8s version %s)", target_ks_version, k8s_version)

    if not options.yes_upgrade_28_29:
        if tuple(target_ks_version.split('.')) >= ('2', '9') and \
           tuple(deployment.current_ks_version.split('.')) < ('2', '9'):
            logging.error("You must update the configuration  if upgrading from 2.8.5 to 2.9. " \
                          "Some of the variable formats changed in the k8s-cluster.yml between 2.8.5 and 2.9.0 " \
                          "If you do not keep your inventory copy up to date, your upgrade will fail and your " \
                          "first master will be left non-functional until fixed and re-run. " \
                          "See https://github.com/kubernetes-sigs/kubespray/blob/master/docs/upgrades.md#multiple-upgrades " \
                          "for details.")
            raise RuntimeError("Specify --yes-upgrade-28-29 to upgrade from 2.8.5 to 2.9.")

    deployment.upgrade(target_ks_version, repo)
    logging.info("Upgrade complete!")


def _construct_deployment(options):
    return Deployment(options.cluster_dir, os.path.join(options.cluster_dir, 'hosts.ini'))


def create_parser():
    parser = argparse.ArgumentParser(description="Managed KubeSpray Kubernetes installation")
    parser.add_argument('kubespray_repo', metavar='KUBESPRAY_DIR', help="Path to Kubespray git repository")
    parser.add_argument('--cluster-dir', metavar='CLUSTER_TF_DIR', help="Path to cluster tf deployment directory", default=os.getcwd())
    parser.add_argument('--target-version', metavar='x.y.z', help='Target kubespray version', default=DefaultKubesprayVersion)

    subparsers = parser.add_subparsers(dest='action')

    parser_checkout = subparsers.add_parser('checkout',
      help='Checkout a version of Kubespray in the container repository')
    parser_checkout.add_argument('--no-update-requirements', action='store_true',
            help="Don't pip install requirements for checked out version of kubespray")
    parser_checkout.set_defaults(func=checkout_cmd)

    parser_install = subparsers.add_parser('deploy-k8s')
    parser_install.set_defaults(func=deploy_cmd)

    parser_upgrade = subparsers.add_parser('upgrade-k8s')
    parser_upgrade.add_argument('--yes-upgrade-28-29', action='store_true', default=False, help="Allow upgrade from 2.8.5 to 2.9")
    parser_upgrade.set_defaults(func=upgrade_cmd)

    return parser


def main(args=None):
    parser = create_parser()
    options = parser.parse_args(args)

    repo = KubesprayRepo(options.kubespray_repo)

    options.func(repo, options)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main(sys.argv[1:])
