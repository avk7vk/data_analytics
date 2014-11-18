#!/usr/bin/python
import os
import sys
import fnmatch
#import pandas as panda
import numpy as nump
import cv2
import test_image
import dbsetup

f = open('features','w')
temp2 = list()
coordinates = list()
img_path = 'path-image-110.tif'
im = cv2.imread(img_path)
imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
contr_list = []
means_list = []
def parse_data(path):
	initializeBaseDB()
        pattern = '*.txt'
	f.write('Area\tPerimeter\tEqui-diameter\tisContour\tConvex Area\tSolidity\tEllipse\tMajor Axis\tMinor Axis\tEccentricity\tMean\n')
        for root, dirs, files in os.walk(path):
                for filename in fnmatch.filter(files,pattern):
                        print os.path.join(root,filename)
                        with open(os.path.join(root,filename),'r') as text:
                                next(text)
                                for line in text:
					datalist = []
					datalist.append(filename)
					line = line.strip()
					boundarys = line.split('\t')[51].strip()
                                        boundary_vals = boundarys.split(';')
					
                                        boundary_vals.pop()
                                        boundary_vals = [[int(float(n)) for n in i.split(',')] for i in boundary_vals]
					
					contr = nump.array(boundary_vals)
					
					#area
					area = cv2.contourArea(contr)
					datalist.append(area)
					#roundness
					roundness = (4*3.14*area)/(perimeter*perimeter)
					#perimeter
					perimeter = cv2.arcLength(contr,True)
					datalist.append(perimeter)
					datalist.append(roundness)
    					# equivalent diameter
    					equi_diameter = nump.sqrt(4*area/nump.pi)
					datalist.append(equi_diameter)

    					### CONVEX HULL ###
    					# convex hull
    					convex_hull = cv2.convexHull(contr)

    					# convex hull area
    					convex_area = cv2.contourArea(convex_hull)
					datalist.append(convex_area)
    					# solidity = contour area / convex hull area
    					solidity = area/float(convex_area)
					datalist.append(solidity)
    					### ELLIPSE  ###

    					ellipse = cv2.fitEllipse(contr)

    					# center, axis_length and orientation of ellipse
    					(center,axes,orientation) = ellipse

    					# length of MAJOR and minor axis
    					majoraxis_length = max(axes)
    					minoraxis_length = min(axes)
					datalist.append(majoraxis_length)
					datalist.append(minoraxis_length)
    					# eccentricity = sqrt( 1 - (ma/MA)^2) --- ma= minor axis --- MA= major axis
    					eccentricity = nump.sqrt(1-(minoraxis_length/majoraxis_length)**2)
					datalist.append(eccentricity)

					datalist.append(boundarys)
					# Find Mean Pixel Intensity
					mask = nump.zeros(imgray.shape,nump.uint8)
					cv2.drawContours(mask,[contr],0,255,-1)
					mean = cv2.mean(im,mask = mask)
					means_list.append(list(mean[0:3]))
					contr_list.append(contr)
					datalist.append(means_list)
					datalist.append(None)
					datalist.append(None)
					insertData(datalist,False)
    					f.write(str(area) + '\t' + str(perimeter)+ '\t' + str(roundness))
    					f.write('\t' + str(equi_diameter) + '\t' + str(isContour) + '\t' + str(convex_area))
    					f.write('\t' + str(solidity) + '\t' + str(ellipse) + '\t' + str(majoraxis_length) + '\t' + str(minoraxis_length) + '\t' + str(eccentricity) + '\n')
					f.write('\t Mean = ' + str(mean) + '\n') 

	f.close
	test_image.image_clustering(means_list, contr_list, img_path)

if __name__ == '__main__':
        path = sys.argv[1]
        parse_data(path)
