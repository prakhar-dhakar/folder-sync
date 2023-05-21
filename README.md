# folder-sync
Python implementation to sync between 2 folders. This branch implments a one direction sync from the `SOURCE_FOLDER` to a folder on the client

## Idea behind implementation:

1. I am using the watchdog library to keep track of folder changes.
2. Mutiple clients can be added to the server

Next Steps happen for each client that has been added to the server i.e. each client has its own separate queue

3. If one of the events (on_deleted, on_modified, on_created) is triggered, then this action is added to the queue that is being maintained
4. After every 1 second, the function `sync_files` checks the queue and executes the synchronization until all elements are popped out from the queue.

## How to run:
1. install the required dependencies using `pip install -r requirements.txt` 
2. Then set the `SOURCE_FOLDER` and add a  `client` to the server for syncing
3. To run use: `python sync_folders.py`

Please keep note, this keeps only the changes added after the python program is run in sync between the 2 folders


