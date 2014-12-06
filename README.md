Source Files
============

Execution
=========
Steps
-----
1. Change to current directory
2. Check if the image properties database is already present.
3. If not or if user want's to regenerate database, execute
   "python features.py <path to input texfiles> <path to TIF images>".
   This will result in the creation of dass.db which holds the image
   properties
4. Run "python GUI.py"
3. On a remote session, Make sure X11 packages are loaded as this application starts a GUI

Workflow
--------
1) Input Section

The user can see the Input section "Choose Image" on the top right corner of the GUI.
User has to either give the path of tile image, if user want's to cluster the tile, or
has to give "all" in the input section to cluster entire image.
