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
	create = 'CREATE TABLE IF NOT EXISTS Features (Nucluei TEXT,\
			  Feature1 TEXT, Feature2 TEXT, Feature3 TEXT, Feature4 TEXT, Feature5 TEXT,\
			  Feature6 TEXT, Feature7 TEXT, Feature8 TEXT, Feature9 TEXT, Feature10 TEXT)'
	cursor.execute(create)
	dbconn.commit()
	#Make all the required settings and give a handle to evaluate function
	setConnBaseDB(dbconn)

def insertData(datalist, override=True):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized."
	stuple = (datalist[0],)
	cursor = conn.cursor()
	cursor.execute("SELECT * FROM Features WHERE Nucluei = '%s'" % stuple)
	row = cursor.fetchall()
	datatuple = tuple(datalist)
	if len(row) == 0:
		cursor.execute("INSERT INTO Features VALUES (?,?,?,?,?,?,?,?,?,?,?)", datatuple)
		conn.commit()
		print "Added entry",datatuple, "to database"
	else:
		if override:
			cursor.execute("DELETE FROM Features WHERE Nucluei = '%s'" % stuple)
			cursor.execute("INSERT INTO Features VALUES (?,?,?,?,?,?,?,?,?,?,?)", datatuple)
			conn.commit()
def getFeatures(feature1, feature2):
	conn = getConnBaseDB()
	if conn == None:
		print "Looks like DB is not initialized."
	cursor = conn.cursor()
	cursor.execute("SELECT Nucluei, "+feature1+", "+feature2+" FROM Features")
	return [(str(n), float(f1), float(f2)) for (n, f1, f2) in cursor.fetchall()]


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