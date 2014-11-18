#!/usr/bin/env python
import numpy as np
from scipy.cluster import vq
from matplotlib import pyplot as plt
import cv2


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
	cv2.imwrite('outimg.tif', im);		
	cv2.imshow('image',im);
	cv2.waitKey();
if __name__ == '__main__':
        path = sys.argv[1]
        image_clustering(path)




