#!/usr/bin/env python

import os
import shutil
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler, FileSystemEventHandler, FileMovedEvent

from configparser import ConfigParser
import io

global config, syncing_directories
syncing_directories = {}
config = ConfigParser()


def dir_from_event(event):
    if isinstance(event, FileMovedEvent):
        import ipdb; ipdb.set_trace()
        return event.dest_path, get_dest_from_src(src=event.dest_path)
    return event.src_path, get_dest_from_src(src=event.src_path)


class Handler(FileSystemEventHandler):
    """file handler events"""

    def on_any_event(self, event):
        """
        For logging system.
        """
        pass

    def on_created(self, event):
        print("on_created")

    def on_deleted(self, event):
        src, dest = dir_from_event(event)
        print("{} deleted --> syncing to {}".format(src, dest))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        deleting_dest_source = get_dest_from_src(src=event.src_path)
        if os.path.isfile(deleting_dest_source):
            if event.is_directory:
                shutil.rmtree(deleting_dest_source)
            else:
                os.remove(deleting_dest_source)

    def on_modified(self, event):
        if not event.is_directory:
            src, dest = dir_from_event(event)
            print("{} modified --> syncing to {}".format(src, dest))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)

    def on_moved(self, event):
        src, dest = dir_from_event(event)
        print("{} moved to {} --> syncing to {}".format(event.src_path, src, dest))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        moving_dest_source = get_dest_from_src(src=event.src_path)
        if os.path.exists(moving_dest_source):
            if event.is_directory:
                shutil.rmtree(moving_dest_source)
            else:
                os.remove(moving_dest_source)
        if not event.is_directory:
            shutil.copy2(src, dest)
        else:
            shutil.copytree(src, dest)


def watch(directory=None):
    '''I am the watcher, I look for a file coming on deposit'''
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    path = directory or '.'
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def load_configuration():
    # Load the configuration file
    config.read('config.ini')


def get_dest_from_src(src):
    """
    """
    folder_separator = '/'
    if os.name == 'nt':
        folder_separator = '\\'
    path = src.split(folder_separator)
    directory_searching = path[0]
    for directory in path[1:]:
        if (syncing_directories.get(directory_searching + directory)):
            found_path = directory_searching + directory
            return found_path + src.replace(found_path, '')
        directory_searching = directory_searching + directory
    syncing_directory = syncing_directories.get(directory_searching)
    from_dir = directory_searching
    if not syncing_directory:
        from_dir = path[0]
        syncing_directory = syncing_directories.get(path[0])
    if not syncing_directory:
        return None
    return syncing_directory + src.replace(from_dir, '')


def synced_mkdir(path):
    os.makedirs(path, exist_ok=True)


def main():
    """main"""
    load_configuration()
    for section in config.sections():
        # TODO set this into multi-threading
        print("Section: %s" % section)
        src = config.get(section, 'src')
        dest = config.get(section, 'dest')
        synced_mkdir(dest)
        print('[{}] syncing {} to {}'.format(section, src, dest))
        syncing_directories[src] = dest
        watch(directory=src)


if __name__ == "__main__":
    main()
