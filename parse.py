#!/usr/bin/python
import os 
import sys
import fnmatch

def parse_data(path):
	pattern = '*.txt'
	for root, dirs, files in os.walk(path):
		for filename in fnmatch.filter(files,pattern):
			print os.path.join(root,filename)
			with open(os.path.join(root,filename),'r') as text:
				next(text)
				for line in text:
					line = line.strip()
					boundary_vals = line.split('\t')[51].strip().split(';')
					boundary_vals.pop()
					print boundary_vals
					

if __name__ == '__main__':
	path = sys.argv[1]
	parse_data(path)

