import os
import time
import queue
import threading
import paramiko
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileChangeHandler(FileSystemEventHandler):
    """
    Checks for events in the source folder and adds to the queue
    """
    def __init__(self, sync_server):
        self.sync_server = sync_server

    def on_any_event(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        file_action = event.event_type
        for file_action_queue in self.sync_server.file_action_queues:
            file_action_queue.put((file_action, file_path))


class SyncServer:

    def __init__(self, source_folder, sync_interval=2):
        self.source_folder = source_folder
        self.sync_interval = sync_interval
        self.file_action_queues = []

    def add_client(self, client):
        """
        Adds a client that needs to be synced with the server
        """
        file_action_queue = queue.Queue()
        self.file_action_queues.append(file_action_queue)
        threading.Thread(target=client.sync_files, args=(file_action_queue,)).start()

    def monitor_files(self):
        """
        Monitors changes in the source folder using the FileChangeHandler class
        """
        event_handler = FileChangeHandler(sync_server=self)
        observer = Observer()
        observer.schedule(event_handler, self.source_folder, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


class SyncClient:

    def __init__(self, host, port, username, password, destination_folder):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.destination_folder = destination_folder

    def create_directory(self, destination_path, sftp):
        """
        Checks if the directory exists or not on the client, if it does not exist, creates it
        """
        destination_dir = os.path.dirname(destination_path)
        dir_exists = False
        file_list = sftp.listdir(os.path.dirname(destination_dir))
        if os.path.basename(destination_dir) in file_list:
            dir_exists = True
        if not dir_exists:
            sftp.mkdir(destination_dir)

    def sync_files(self, file_action_queue):
        """
        Syncs the files between the source and the client using the queue
        """
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        sftp = transport.open_sftp_client()

        while True:
            try:
                file_action, file_path = file_action_queue.get(timeout=sync_server.sync_interval)
                destination_path = file_path.replace(sync_server.source_folder, self.destination_folder)
                if file_action == 'created' or file_action == 'modified':
                    self.create_directory(destination_path, sftp)
                    sftp.put(file_path, destination_path)
                    print(f'Copied: {file_action} {file_path} -> {destination_path}')

                elif file_action == 'deleted':
                    try:
                        sftp.remove(destination_path)
                        print(f'Deleted: {destination_path}')
                    except IOError:
                        print(f'File not found: {destination_path}')
                file_action_queue.task_done()
            except queue.Empty:
                pass
            time.sleep(2)

        sftp.close()
        transport.close()


if __name__ == "__main__":

    SOURCE_FOLDER = '/Users/prakhar/Desktop/folder1'

    sync_server = SyncServer(SOURCE_FOLDER)

    # Add clients
    client2 = SyncClient('client2_host', 22, 'client2_username', 'client2_password', '/path/to/destination/folder2')

    sync_server.add_client(client2)

    # Start file monitoring
    threading.Thread(target=sync_server.monitor_files).start()
