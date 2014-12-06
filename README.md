Source Files
============
features.py,dbsetup.py
GUI.py
Optics.py,AutomaticClustering.py,OpticsClusterArea.py,dass.db(database file)


Execution
=========
Steps
-----
1. Change to current directory
2. Check if the image properties database is already present.
3. If not or if user want's to regenerate database, execute
   "python features.py <path to input texfiles> <path to TIF images>".
   For eg: python features.py ./example_files/data_595_output ./example_files/data_595_input
   Note that our parser program parses correctly, when files are in specific format.Consider the files in examples folder as an example 
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

2) Feature Selection

All the features supported are displayed in the selection below Input Section. All the
feature except 'Mean Pixel Intensity' are scalars. If user wants to cluster using 'Mean
Pixel Intensity', which is a 3D vector feature, the user cannot use any other scalar feature along with this. Apart
from this, user can select any number of scalar features for clustering. After the
clustering is done, the clusters are visulised in 2D using the first two features selected.


3) Clustering Algorithm Selection

This application provides two Algorithms, i) KMeans and ii) Optics clustering
The user can selection one of the above algorithms for clustering, in this section

4) K-Value

If the user selects KMeans Algorithm, this section is activated. The user has
to enter the number of clusters to formed in this section.

5) Interactive Updates

If user selects KMeans Algorithm, User has an option to visualize the updates over
iterations of KMeans Aglorithm. The user can enable this option for visualizing
updates.

6) Initial Centroid Selection

If user selects KMeans Algorithm, the user can select the initial centroids by
clicking on the 2D visualized data on the left canvas visible. To do this, user
has to first check "Initial Centroid Selection" option. Following this, the user
must use "Show Image/Reset" button to first generate the initial data on the 
left canvas, Now user can click k times (already selection in previous section)
on the graph. These selected points will be used as centroids for clustering

7) Starting the clustering algorithm

The user must use "Start" button to start the clsutering and the results can be
seen on the canvas present on the left side.

8) Generating Image with cluster mapped onto Nuclei

If user selects KMeans algorithm, once the clustering is done, the user will
have an option to watch the nuclei of image with their boundaries marked in
distinct colors each representing an unique cluster. User has to click 
"Generate Image" button, which will then save an above described image,
and also open up a pop up showing the same image.

Dependent Packages
------------------
Numpy
Scipy
Matplotlib
Pylab
wxPython
OpenCV
