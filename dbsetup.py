import random
import sqlite3
basedb = "dass.db"
basedb_conn = None

def setBaseDB(name):
	global basedb
	basedb=name

def getBaseDB():
	global basedb
	return basedb

def setConnBaseDB(conn):
	global basedb_conn
	basedb_conn  = conn	

def getConnBaseDB():
	global basedb_conn
	return basedb_conn

def closeConnBaseDB():
	global basedb_conn
	if basedb_conn != None:
		basedb_conn.close()

def initializeBaseDB():
	basedb = getBaseDB()
	#Check if there is an already existing DB
	dbconn = sqlite3.connect(basedb)
	cursor = dbconn.cursor()
	create = 'CREATE TABLE IF NOT EXISTS Features (IMAGE_NAME TEXT,NUCLEI INT,\
			  AREA REAL ,PERIMETER REAL, ROUNDNESS REAL,EQUI_DIAMETER REAL, CONVEX_AREA REAL,\
			   SOLIDITY REAL, MAJOR_AXIS_LEN REAL, MINOR_AXIS_LEN REAL,ORIENTATION REAL,ECCENTRICITY REAL,CIR_RADIUS REAL,SHAPE_INDEX REAL,BORDER_INDEX REAL,ASPECT_RATION REAL, BOUNDARY_VALS TEXT,MEAN_PIXEL_DEN TEXT,\
			   MAX_PIXEL_DEN REAL,MIN_PIXEL_DEN REAL,PRIMARY KEY(IMAGE_NAME,NUCLEI))'
	cursor.execute(create)
	dbconn.commit()
	#Make all the required settings and give a handle to evaluate function
	setConnBaseDB(dbconn)


def insertData(datalist, override=True):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized."
	stuple = (datalist[0],datalist[1],)
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Features WHERE IMAGE_NAME = '%s' AND NUCLEI = '%d'" % stuple)
	row = cursor.fetchall()
	datatuple = tuple(datalist)
	if len(row) == 0:
		cursor.execute("INSERT INTO Features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datatuple)
		conn.commit()
		#print "Added entry",datatuple, "to database"
	else:
		print "Just skip ! Record already present!"
		if override:
			cursor.execute("DELETE FROM Features WHERE IMAGE_NAME = '%s' AND NUCLEI = '%d'" % stuple)
			cursor.execute("INSERT INTO Features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datatuple)
			conn.commit()
def getFeatures(filename, feature1, feature2):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized."
	cursor = conn.cursor()
	stuple = (filename,)
	if (filename == "all"):
		cursor.execute("SELECT IMAGE_NAME, NUCLEI, "+feature1+", "+feature2+" FROM Features")# WHERE IMAGE_NAME = '%s'" % stuple)
	else :
		cursor.execute("SELECT IMAGE_NAME, NUCLEI, "+feature1+", "+feature2+" FROM Features WHERE IMAGE_NAME = '%s'" % stuple)
	return [(str(f), int(n), float(f1), float(f2)) for (f,n, f1, f2) in cursor.fetchall()]


def getFeaturesList(filename, featurelist):
		conn = getConnBaseDB()
		if conn == None:
			print "Looks like DB is not initialized."
		
		cursor = conn.cursor()
		stuple = (filename,)
		
		sql_query = "SELECT IMAGE_NAME,NUCLEI,"
		s = ''
		for feature in featurelist:
			s = s+str(feature)+','
		s = s[:-1]
		sql_query += s
		if (filename == "all"):
			cursor.execute(sql_query+ " FROM Features");
		else:
			cursor.execute(sql_query+" FROM Features where IMAGE_NAME = '%s'" %filename)
		list1 = []
		for index,j in enumerate(featurelist):
			list1.append('f'+str(index))
		list2 = ['f','n']+list1

	        return [list2 for list2 in cursor.fetchall()]


def getAllFeatures(filename, feature1, feature2, val1,val2):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized"

	print "feature1",feature1
	print "feature2", feature2
	print "feature-val1", val1
	print "featue-val2", val2

	cursor = conn.cursor()
	str1 = (str(filename),val1,val2,)
	str2 = (val1,val2,)

	if (filename == "all"):
		cursor.execute("SELECT IMAGE_NAME,NUCLEI,AREA,PERIMETER,ROUNDNESS,EQUI_DIAMETER,CONVEX_AREA,SOLIDITY,"
					"MAJOR_AXIS_LEN,MINOR_AXIS_LEN,ORIENTATION,ECCENTRICITY,CIR_RADIUS,"
					"SHAPE_INDEX,BORDER_INDEX,ASPECT_RATION,MAX_PIXEL_DEN,MIN_PIXEL_DEN FROM Features WHERE "+
					feature1 +" = ?  AND "+ feature2 + " = ? ",str2)
	else:
		cursor.execute("SELECT IMAGE_NAME,NUCLEI,AREA,PERIMETER,ROUNDNESS,EQUI_DIAMETER,CONVEX_AREA,SOLIDITY,"
					"MAJOR_AXIS_LEN,MINOR_AXIS_LEN,ORIENTATION,ECCENTRICITY,CIR_RADIUS,"
					"SHAPE_INDEX,BORDER_INDEX,ASPECT_RATION,MAX_PIXEL_DEN,MIN_PIXEL_DEN FROM Features WHERE IMAGE_NAME = ? AND "+ 
					feature1 +" = ?  AND "+ feature2 + " = ? ",str1)
	
	return [[f,i, float(f1),float(f2),float(f3),float(f4),float(f5),
			 float(f6),float(f7),float(f8),float(f9),float(f10),
			 float(f11),float(f12),float(f13),float(f14),float(f15),float(f16)] 
			 for (f,i,f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16) in cursor.fetchall()]	


def getSingleFeature(feature):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized."
	cursor = conn.cursor()
        cursor.execute("SELECT NUCLEI, "+feature+" FROM Features")
        return [(str(n), str(f)) for (n, f) in cursor.fetchall()]

if __name__ == '__main__':
	
	initializeBaseDB()
	'''
	for i in range(1000):
		data = [str(i)]
		data.extend([str(random.choice(range(1000))) for i in range(10)])
		insertData(data)	
	conn = getConnBaseDB()
	cursor = conn.cursor()
	for i in range(10):
		tup = (str(i),)
		cursor.execute("SELECT * FROM Features WHERE Nucluei = '%s'" % tup)
		row = cursor.fetchall()
		for j in row:
			print tuple(j)
		#print row
	'''
	rows = getFeatures('Feature1', 'Feature2')
	print rows
	closeConnBaseDB()
