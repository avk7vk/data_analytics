from PIL import Image
import numpy

im = Image.open("path-image-100.tif")
mask = open("path-image-100.mask")
mask_dim = mask.readline().split(" ");
print "Mask Dim is " , mask_dim
imarray = numpy.array(im)
print "shape :", imarray.shape
print "Size :", imarray.size
height = imarray.shape[0]
width = imarray.shape[1]
rgb = imarray.shape[2]
mask_height = int(mask_dim[1])
mask_width = int(mask_dim[0])
if mask_width == width and mask_height == height:
	print "Width :", width, " Height :", height, "RGB :", rgb
	for i in range(0, height) :
		for j in range(0, width) :
			mask_val = int(mask.readline())
			if mask_val == 1:
				for k in range(0, rgb) :
					imarray[i][j][k] = 0
	print imarray
	new_img = Image.fromarray(imarray, 'RGB')
	new_img.save("masked-image.tif")
else :
	print "Image Dim and Mask Dims dont match"
	print "{} X {} != {} X {}".format(height, width, mask_height, mask_width);
