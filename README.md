# folder-sync
Python implementation to sync between 2 folders

## Idea behind implementation:

1. I am using the watchdog library to keep track of folder changes.
2. If one of the events (on_deleted, on_modified, on_created) is triggered, then this action is added to a queue that is being maintained
3. After every 1 second, the function `synchronize_folders` checks the queue and executes the syncronization until all elements are popped out from the queue.

## How to run:
1. install the required dependencies using `pip install -r requirements.txt` 
2. Then set the `folder1` and `folder2` path variables
3. To run use: `python sync_folders.py`

Please keep note, this keeps only the changes added after the python program is run in sync between the 2 folders


