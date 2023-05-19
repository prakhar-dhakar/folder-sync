from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil
import os
import time
from queue import Queue, Empty
import threading
import hashlib

class FolderSyncHandler(FileSystemEventHandler):
    def __init__(self, folder1, folder2):
        self.folder1 = folder1
        self.folder2 = folder2
        self.sync_queue = Queue()
        self.queue_lock = threading.Lock()

    def check_md5(self, filepath1, filepath2):
        """
        Checks whether the md5 checksum of the files is same or not, if not returns False else True
        """

        if os.path.exists(filepath1) and os.path.exists(filepath2):
            hash1 = hashlib.md5()
            hash2 = hashlib.md5()

            # Read the files and update the hashes.
            with open(filepath1, "rb") as f:
                for chunk in f:
                    hash1.update(chunk)

            with open(filepath2, "rb") as f:
                for chunk in f:
                    hash2.update(chunk)

            # Compare the hashes.
            return hash1.digest() == hash2.digest()
        return False

    def synchronize_folders(self):
        """
        Syncs the 2 folders together using the queue
        """
        with self.queue_lock:
            while not self.sync_queue.empty():
                try:
                    event_type, file_path = self.sync_queue.get(block=False)
                    if event_type == 'created':
                        self.sync_file_to_other_folder(file_path)
                    elif event_type == 'modified':
                        self.sync_file_to_other_folder(file_path)
                    elif event_type == 'deleted':
                        self.remove_file_from_other_folder(file_path)
                except Empty:
                    break
            time.sleep(1)
        

    def enqueue_sync_event(self, event_type, file_path):
        """
        Adds an event to the queue that needs to be synced later
        """
        with self.queue_lock:
            self.sync_queue.put((event_type, file_path))

    def sync_file_to_other_folder(self, file_path):
        """
        Syncs a file between the 2 folders, copies from one folder to another
        """
        print("syncing")
        if os.path.exists(file_path):
            if self.folder1 in file_path and self.folder2 not in file_path:
                destination_path = file_path.replace(self.folder1, self.folder2)
                shutil.copy2(file_path, destination_path)

            elif self.folder2 in file_path and self.folder1 not in file_path:
                destination_path = file_path.replace(self.folder2, self.folder1)
                shutil.copy2(file_path, destination_path)

    def remove_file_from_other_folder(self, file_path):
        """
        Deletes files from both the folders
        """
        print("deleting")

        if self.folder1 in file_path and self.folder2 not in file_path:
            destination_path = file_path.replace(self.folder1, self.folder2)
            if os.path.exists(destination_path):
                os.remove(destination_path)
                
        elif self.folder2 in file_path and self.folder1 not in file_path:
            destination_path = file_path.replace(self.folder2, self.folder1)
            if os.path.exists(destination_path):
                os.remove(destination_path)

    def on_created(self, event):
        """
        Watchdog event that is triggered when a new file is created in the folder
        """
        print("On created")
        if not event.is_directory:
            try:
                self.enqueue_sync_event('created', event.src_path)
            except FileNotFoundError:
                print("File was not found")


    def on_modified(self, event):
        """
        Watchdog event when a file is modified in the folder
        """
        print("On modified")
        if not event.is_directory:
            file_path = event.src_path
            try:
                if self.folder2 in file_path:
                    file_path2 = file_path.replace(self.folder2, self.folder1)
                if self.folder1 in file_path:
                    file_path2 = file_path.replace(self.folder1, self.folder2)
                if not self.check_md5(file_path, file_path2):
                    self.enqueue_sync_event('modified', event.src_path)
            except FileNotFoundError:
                print("File has been deleted")

    def on_deleted(self, event):
        """
        Watchdog event when a file is deleted in the folder
        """
        print("On deleted")
        if not event.is_directory:
            self.enqueue_sync_event('deleted', event.src_path)


if __name__ == "__main__":

    folder1 = '/Users/prakhar/Desktop/folder1'
    folder2 = '/Users/prakhar/Desktop/folder2'

    event_handler = FolderSyncHandler(folder1, folder2)

    observer1 = Observer()
    observer1.schedule(event_handler, folder1, recursive=False)
    observer1.start()

    observer2 = Observer()
    observer2.schedule(event_handler, folder2, recursive=False)
    observer2.start()

    try:
        while True:
            event_handler.synchronize_folders()
            time.sleep(1)
    except KeyboardInterrupt:
        observer1.stop()
        observer1.join()
        observer2.stop()
        observer2.join()
