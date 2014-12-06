#!/usr/bin/python
import os
import sys
import fnmatch
#import pandas as panda
import numpy as nump
import cv2
import test_image
import dbsetup
import time

'''
 parse_data function input parameters:
 path:This is the absolute path of the output folder which contains text files that are to be parsed
 for feature extraction.
 image_path:Absolute path of folder that contains original .tif formatted input title images
 This function essentially locates and parses text files to extract various number
 of features and extracts them into our sqlite database.
 In general, this script is used one time to parse data,get features and store them in DB.

'''
def parse_data(path,image_path):
	dbsetup.initializeBaseDB()
	#image_path = "/data03/shared/data_595_input"
        pattern = '*.txt'
        for root, dirs, files in os.walk(path):
                for filename in fnmatch.filter(files,pattern):
                        print os.path.join(root,filename)
			nuclie_id = 0
			t = time.time()	
                        with open(os.path.join(root,filename),'r') as text:
                                next(text)
				for file in os.listdir(image_path):
					if file.startswith(filename[0:filename.index('.seg')]) and file.endswith(".tif"):
						im = cv2.imread(os.path.join(image_path,file))
						imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
						break
                                for line in text:
					datalist = []
					datalist.append(filename[0:filename.index('.seg')])
					nuclie_id += 1
					datalist.append(nuclie_id)
		
					line = line.strip()
					boundarys = line.split('\t')[51].strip()
                                        boundary_vals = boundarys.split(';')
					
                                        boundary_vals.pop()
                                        boundary_vals = [[int(float(n)) for n in i.split(',')] for i in boundary_vals]
					
					contr = nump.array(boundary_vals)
					
					#area
					area = float("{0:.2f}".format(cv2.contourArea(contr)))
					datalist.append(area)
					
					#perimeter
					perimeter = float("{0:.2f}".format(cv2.arcLength(contr,True)))
					datalist.append(perimeter)
					
					#roundness
                                        roundness = float("{0:.2f}".format((4*3.14*area)/(perimeter*perimeter)))
					datalist.append(roundness)
					
					#equivalent diameter
    					equi_diameter = float("{0:.2f}".format(nump.sqrt(4*area/nump.pi)))
					datalist.append(equi_diameter)

    					### CONVEX HULL ###
    					# convex hull
    					convex_hull = cv2.convexHull(contr)

    					# convex hull area
    					convex_area = float("{0:.2f}".format(cv2.contourArea(convex_hull)))
					datalist.append(convex_area)
    					# solidity = contour area / convex hull area
    					solidity = float("{0:.2f}".format(area/float(convex_area)))
					datalist.append(solidity)
    					### ELLIPSE  ###

    					ellipse = cv2.fitEllipse(contr)

    					# center, axis_length and orientation of ellipse
    					(center,axes,orientation) = ellipse

    					# length of MAJOR and minor axis
    					majoraxis_length = float("{0:.2f}".format(max(axes)))
    					minoraxis_length = float("{0:.2f}".format(min(axes)))
					orientation_angle = float("{0:.2f}".format(orientation))
					datalist.append(majoraxis_length)
					datalist.append(minoraxis_length)
					datalist.append(orientation_angle)
    					# eccentricity = sqrt( 1 - (ma/MA)^2) --- ma= minor axis --- MA= major axis
    					eccentricity = float("{0:.2f}".format(nump.sqrt(1-(minoraxis_length/majoraxis_length)**2)))
					datalist.append(eccentricity)
	
					#Radius of minimum enclosing circle
					(x,y),radius = cv2.minEnclosingCircle(contr)
					encl_radius = float("{0:.2f}".format(radius))
					datalist.append(encl_radius)
					#Shape index
					
					edgeLength = 0
					for j in range(0, len(contr)-1):
						k = j + 1
						length = nump.sqrt(((contr[k][1] - contr[j][1]) ** 2) + ((contr[k][0] - contr[j][0]) ** 2))
						edgeLength += length
					shape_index = (edgeLength)/(4*(nump.sqrt(area)))

					shape_index = float("{0:.2f}".format(shape_index))
					datalist.append(shape_index)
			
                                        #border_index
                                        (x,y),(w,h),theta = cv2.minAreaRect(contr)
                                        border_index = edgeLength/(2*(w+h))
					
					border_index = float("{0:.2f}".format(border_index))
					datalist.append(border_index)
                                        # aspect ratio
                                        aspect_ratio = w/float(h)
					aspect_ratio = float("{0:.2f}".format(aspect_ratio))
					datalist.append(aspect_ratio)
					datalist.append(str(boundarys))
					# Find Mean Pixel Intensity
					mask = nump.zeros(imgray.shape,nump.uint8)
					cv2.drawContours(mask,[contr],0,255,-1)
					mean = cv2.mean(im,mask = mask)
					datalist.append(str(mean[0:3]))
					(min_val,max_val,min_loc,max_loc) = cv2.minMaxLoc(imgray,mask = mask)
					min_val = float("{0:.2f}".format(min_val))
					max_val = float("{0:.2f}".format(max_val))
					datalist.extend([max_val,min_val])
					s = time.time()
					dbsetup.insertData(datalist,False)
					print "time for nuclie:%s - %d is %d"%(datalist[0],datalist[1],time.time()-s)
			print "Parsing done for %s ! Time taken %d "%(filename,float((time.time()-t)/60))				
	#test_image.image_clustering(means_list, contr_list, img_path)
	dbsetup.closeConnBaseDB()
'''
Script can be executed as
python features.py /data03/shared/data_output /data03/shared/data_input
where the first parameter is folder containing text files and the 
second one is the folder containing tif images

'''
if __name__ == '__main__':
	p = time.time()
        path,image_path = sys.argv[1],sys.argv[2]
        parse_data(path,image_path)
	print 'END TIME:',time.time()-p

