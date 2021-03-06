# -*- coding: utf-8-*-
try:
    from ConfigParser import ConfigParser, Error, NoSectionError
except ImportError:
    from configparser import ConfigParser, Error, NoSectionError

from os import path, makedirs
from netaddr import IPAddress
import platform
import random
import string

class PupyConfig(ConfigParser):
    NoSectionError = NoSectionError

    def __init__(self, config='pupy.conf'):
        self.root = path.abspath(path.join(path.dirname(__file__), '..'))
        self.user_root = path.expanduser(path.join('~', '.config', 'pupy'))
        self.project_path = path.join('config', config)
        self.user_path = path.join(self.user_root, config)
        self.files = [
            path.join(self.root, config+'.default'),
            path.join(self.root, config),
            self.user_path,
            self.project_path,
            config
        ]
        self.randoms = {}
        self.command_line = {}

        ConfigParser.__init__(self)
        self.read(self.files)

    def save(self, project=True, user=False):
        if project:
            project_dir = path.dirname(self.project_path)
            if not path.isdir(project_dir):
                makedirs(project_dir)

            with open(self.project_path, 'w') as config:
                self.write(config)

        if user:
            user_dir = path.dirname(self.user_path)
            if not path.isdir(user_dir):
                makedirs(user_dir)

            with open(self.user_path, 'w') as config:
                self.write(config)

    def get_path(self, filepath, substitutions, create=True, dir=False):
        prefer_workdir = self.getboolean('paths', 'prefer_workdir')
        from_config = self.get('paths', filepath)

        retfilepath = ''
        if from_config:
            retfilepath = from_config
        elif path.isabs(filepath):
            retfilepath = filepath
        elif prefer_workdir:
            retfilepath = filepath
        else:
            retfilepath = path.join(self.user_root, filepath)

        for key, value in substitutions.iteritems():
            try:
                value = value.replace('/', '_').replace('..', '_')
                if platform.system == 'Windows':
                    value = value.replace(':', '_')
            except:
                pass

            retfilepath = retfilepath.replace(key, str(value))

        if dir and path.isdir(retfilepath):
            return path.abspath(retfilepath)
        elif not dir and path.isfile(retfilepath):
            return path.abspath(retfilepath)
        elif path.exists(retfilepath):
            raise ValueError('{} is not a file/idr'.format(retfilepath))
        elif create:
            if dir:
                makedirs(retfilepath)
            else:
                dirpath = path.dirname(retfilepath)
                if not path.isdir(dirpath):
                    makedirs(dirpath)

            return path.abspath(retfilepath)
        else:
            return path.abspath(retfilepath)

    def get_folder(self, folder='data', substitutions={}, create=True):
        return self.get_path(folder, substitutions, create, True)

    def get_file(self, folder='data', substitutions={}, create=True):
        return self.get_path(folder, substitutions, create)

    def remove_option(self, section, key):
        if section != 'randoms':
            ConfigParser.unset(self, section, key)
        elif section in self.command_line and key in self.command_line[section]:
            del self.command_line[section][key]
            if not self.command_line[section]:
                del self.command_line[section]
        else:
            if key in self.randoms:
                del self.randoms[key]
            elif key == 'all':
                self.randoms = {}

    def set(self, section, key, value, **kwargs):
        if kwargs.get('cmd', False):
            if not section in self.command_line:
                self.command_line[section] = {}
            self.command_line[section][key] = str(value)
        elif section != 'randoms':
            if section in self.command_line and key in self.command_line[section]:
                del self.command_line[section][key]
                if not self.command_line[section]:
                    del self.command_line[section]

            ConfigParser.set(self, section, key, value)
        else:
            if not key:
                N = kwargs.get('random', 10)
                while True:
                    key = ''.join(random.choice(
                        string.ascii_letters + string.digits) for _ in range(N))

                    if not key in self.randoms:
                        break

            self.randoms[key] = value
            return key

    def get(self, *args, **kwargs):
        try:
            if args[0] == 'randoms':
                if not args[1] in self.randoms:
                    N = kwargs.get('random', 10)
                    new = kwargs.get('new', True)
                    if new:
                        self.randoms[args[1]] = ''.join(
                            random.choice(
                                string.ascii_letters + string.digits) for _ in range(N))

                return self.randoms.get(args[1], None)

            elif args[0] in self.command_line and args[1] in self.command_line[args[0]]:
                return self.command_line[args[0]][args[1]]

            return ConfigParser.get(self, *args, **kwargs)
        except Error as e:
            return None

    def getip(self, *args, **kwargs):
        ip = self.get(*args, **kwargs)
        if not ip:
            return None
        return IPAddress(ip)

    def sections(self):
        sections = ConfigParser.sections(self)
        sections.append('randoms')
        for section in self.command_line:
            if not section in sections:
                sections.append(section)

        return sections

    def options(self, section):
        if section != 'randoms':
            return ConfigParser.options(self, section)

        keys = self.randoms.keys()
        if section in self.command_line:
            for key in self.command_line[section]:
                if not key in keys:
                    keys.append(key)

        return keys
