import numpy as np
from scipy.cluster import vq
from matplotlib import pyplot as plt
import cv2
import sqlite3
import dbsetup
import random
import re
def image_clustering(mean_list,contour_list,image_path):
        z = np.array(mean_list)
        center,dist = vq.kmeans(z,3)
        code,distance = vq.vq(z,center)
        im = cv2.imread(image_path)
        for index,i in enumerate(code):
                if i == 0:
                        cv2.drawContours(im,contour_list,index,(255,0,0),-1)
                elif i == 1:
                        cv2.drawContours(im,contour_list,index,(0,255,0),-1)
                elif i == 2:
                        cv2.drawContours(im,contour_list,index,(0,0,0),-1)
        cv2.imwrite('outimg.tif', im)
        cv2.imshow('image',im)
        cv2.waitKey()


def generate_image(tile_name,no_clusters,code,image_path):
	#Red,Green,Blue,Marooon,Cyan,Yellow,Magenta,Purple,Navy,Gray(BGR format NOT RGB)
	colors = {0:(0,0,255),1:(0,255,0),2:(255,0,0),3:(0,0,128),4:(255,255,0),5:(0,255,255),6:(255,0,255),7:(128,0,128)
			,8:(128,0,0),9:(128,128,128)}
	basedb = dbsetup.getBaseDB()
	conn = sqlite3.connect(basedb)
	#Query DB to get boundary values for this image.
	c = conn.cursor()
	c.execute("SELECT BOUNDARY_VALS FROM Features WHERE IMAGE_NAME = '%s'" %tile_name)
	rows = c.fetchall()
	contour_list = []
	for row in rows:
		boundary_vals = row[0].strip().split(';')
		boundary_vals.pop()
		boundary_vals = [[int(float(n)) for n in i.split(',')] for i in boundary_vals]
		contr = np.array(boundary_vals)
		contour_list.append(contr)
	im = cv2.imread(image_path)
	for index,i in enumerate(code):
		cv2.drawContours(im,contour_list,index,colors[i],-1)

	outputfile = "Output_"+tile_name+".tif"
	cv2.imwrite(outputfile,im);
	cv2.imshow('image',im)
	cv2.waitKey()
	dbsetup.closeConnBaseDB()
	return(im)

def helper_mean(tile_name):
	basedb = dbsetup.getBaseDB()
        conn = sqlite3.connect(basedb)
	c = conn.cursor()
	c.execute("SELECT MEAN_PIXEL_DEN FROM Features WHERE IMAGE_NAME = '%s'" %tile_name)
	rows = c.fetchall()
	data_list = []
	for row in rows:
		item = str(row[0])
		match = re.search(r'\((.*)\)',item)
		if match:
			data = match.group(1).split(',')
			data_list.append(data)
	data_list = [[float(j) for j in i ] for i in data_list]			
	dbsetup.closeConnBaseDB()
	return data_list
	

if __name__ == '__main__':
        #path = sys.argv[1]
        #image_clustering(path)
	helper_mean("path-image-110")
	#choice = [0,1,2,3,4]
	#m = generate_image("path-image-110",len(choice),[random.choice(choice) for i in range(1000)],"path-image-110.tif")
