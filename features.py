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


def parse_data(path):
	dbsetup.initializeBaseDB()
	image_path = "/data_595_input";
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
					datalist.append(majoraxis_length)
					datalist.append(minoraxis_length)
    					# eccentricity = sqrt( 1 - (ma/MA)^2) --- ma= minor axis --- MA= major axis
    					eccentricity = float("{0:.2f}".format(nump.sqrt(1-(minoraxis_length/majoraxis_length)**2)))
					datalist.append(eccentricity)

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
if __name__ == '__main__':
	p = time.time()
        path = sys.argv[1]
        parse_data(path)
	print 'END TIME:',time.time()-p

