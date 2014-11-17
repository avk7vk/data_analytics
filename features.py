#!/usr/bin/python
import os
import sys
import fnmatch
import pandas as panda
import numpy as nump
import cv2

f = open('features.txt','w')
temp2 = list()
coordinates = list()
def parse_data(path):
        pattern = '*.txt'
	f.write('Area\tPerimeter\tEqui permeter\tisContour\tConvexity\tConvex Area\tSolidity\tEllipse\tMajor Axis\tMinor Axis\tEccentricity\n')
        for root, dirs, files in os.walk(path):
                for filename in fnmatch.filter(files,pattern):
                        print os.path.join(root,filename)
                        with open(os.path.join(root,filename),'r') as text:
                                next(text)
                                for line in text:
					line = line.strip()
                                        boundary_vals = line.split('\t')[51].strip().split(';')
					
                                        boundary_vals.pop()
                                        boundary_vals = [[int(float(n)) for n in i.split(',')] for i in boundary_vals]
					
					contr = nump.array(boundary_vals)

					#area
					area = cv2.contourArea(contr)

					#perimeter
					perimeter = cv2.arcLength(contr,True)

    					# equivalent diameter
    					equi_diameter = nump.sqrt(4*area/nump.pi)

    					#check if contour or not
    					isContour = cv2.isContourConvex(contr)

    					### CONVEX HULL ###
    					# convex hull
    					convex_hull = cv2.convexHull(contr)

    					# convex hull area
    					convex_area = cv2.contourArea(convex_hull)

    					# solidity = contour area / convex hull area
    					solidity = area/float(convex_area)

    					### ELLIPSE  ###

    					ellipse = cv2.fitEllipse(contr)

    					# center, axis_length and orientation of ellipse
    					(center,axes,orientation) = ellipse

    					# length of MAJOR and minor axis
    					majoraxis_length = max(axes)
    					minoraxis_length = min(axes)

    					# eccentricity = sqrt( 1 - (ma/MA)^2) --- ma= minor axis --- MA= major axis
    					eccentricity = nump.sqrt(1-(minoraxis_length/majoraxis_length)**2)

    					f.write(str(area) + '\t' + str(perimeter))
    					f.write('\t' + str(equi_diameter) + '\t' + str(isContour) + '\t' + str(convex_area))
    					f.write('\t' + str(solidity) + '\t' + str(ellipse) + '\t' + str(majoraxis_length) + '\t' + str(minoraxis_length) + '\t' + str(eccentricity))

f.close

if __name__ == '__main__':
        path = sys.argv[1]
        parse_data(path)

