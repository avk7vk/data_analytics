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
			   SOLIDITY REAL, MAJOR_AXIS_LEN REAL, MINOR_AXIS_LEN REAL,ECCENTRICITY REAL, BOUNDARY_VALS TEXT,MEAN_PIXEL_DEN TEXT,\
			   MAX_PIXEL_DEN TEXT,MIN_PIXEL_DEN TEXT,PRIMARY KEY(IMAGE_NAME,NUCLEI))'
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
		cursor.execute("INSERT INTO Features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datatuple)
		conn.commit()
		#print "Added entry",datatuple, "to database"
	else:
		print "Just skip ! Record already present!"
		if override:
			cursor.execute("DELETE FROM Features WHERE IMAGE_NAME = '%s' AND NUCLEI = '%d'" % stuple)
			cursor.execute("INSERT INTO Features VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", datatuple)
			conn.commit()
def getFeatures(feature1, feature2):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized."
	cursor = conn.cursor()
	cursor.execute("SELECT NUCLEI, "+feature1+", "+feature2+" FROM Features")
	return [(str(n), float(f1), float(f2)) for (n, f1, f2) in cursor.fetchall()]

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
