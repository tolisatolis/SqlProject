# ----- CONFIGURE YOUR EDITOR TO USE 4 SPACES PER TAB ----- #
import os
import sys
from collections import Counter
import pymysql as db
import settings
import nltk
from nltk.corpus import stopwords
import random
sys.path.append(os.path.join(os.path.split(os.path.abspath(__file__))[0], 'lib'))


def connection():
    """ User this function to create your connections """
    con = db.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_passwd,
        database=settings.mysql_schema)

    return con


def create_ngrams(text, num):
    # Making all letters lower case
    text = text.lower()
    # Remove numbers from string
    text = ''.join([i for i in text if not i.isdigit()])
    # Remove punctuations from string
    text = nltk.RegexpTokenizer(r"\w+").tokenize(text)
    # Define stopwords
    garbage = stopwords.words('english')
    garbage.extend(['patient', 'vaccine', 'covid', 'injection', 'hours', 'took', 'went',
                    'symptoms', 'dose', 'within', 'history', 'hr', 'rr', 'spo', 'thursday',
                    'night', 'c', 'day', 'number', 'finish', 'began', 'due', 'days', 'thought'])
    # Remove stopwords from string
    text = [word for word in text if word not in garbage]
    # Construct n-grams (n = num)
    text = zip(*[text[i:] for i in range(num)])
    # Transform zip object to list
    text = [" ".join(ngram) for ngram in text]
    return text


def mostcommonsymptoms(vax_name):
    # Create a new connection
    # Create a new connection
    con = connection()
    # Create a cursor on the connection
    cur = con.cursor()

    sql = "SELECT symptoms FROM vaccination WHERE vaccines_vax_name = '%s'; " % vax_name
    cur.execute(sql)
    rows = cur.fetchall()
    con.close()

    # If an empty table was returned
    if len(rows) == 0:
        return [(vax_name, " does not exist in our database")]

    symptoms = []
    for i in rows:
        symptoms += create_ngrams(i[0], 1)

    # Sort by most to least often occurrences
    symptoms.sort(key=Counter(symptoms).get, reverse=True)
    # Remove duplicates
    symptoms = list(dict.fromkeys(symptoms))

    return [("vax_name", "symptoms"), (vax_name, symptoms)]


def findnurse(x, y):
    # Create a new connection
    con = connection()
    # Create a cursor on the connection
    cur = con.cursor()
    sql = "SELECT count(*) as num_of_blocks FROM block b WHERE b.BlockFloor = '%s';" % (x)
    cur.execute(sql)
    num_of_blocks = cur.fetchall()
    sql2="""SELECT distinct n.name, n.EmployeeID, count(distinct v.patient_SSN)
            FROM nurse n, on_call oc, block b ,appointment a ,vaccination v
            WHERE  oc.Nurse = n.EmployeeID AND b.BlockFloor = '%s'  AND a.PrepNurse = n.EmployeeID AND v.nurse_EmployeeID=n.EmployeeID
            group by n.name 
            having count(distinct b.BlockCode) = '%s' AND count(distinct a.Patient) >= '%s' 
            UNION 
            SELECT distinct n.name, n.EmployeeID, 0
            FROM nurse n, on_call oc, block b ,appointment a ,vaccination v
            WHERE  oc.Nurse = n.EmployeeID AND b.BlockFloor = '%s'  AND a.PrepNurse = n.EmployeeID AND v.nurse_EmployeeID=n.EmployeeID
            group by n.name 
            having count(distinct b.BlockCode) = '%s' AND count(distinct a.Patient) >= '%s'
            """% (x, num_of_blocks[0][0], y,x,num_of_blocks[0][0],y)
    cur.execute(sql2)
    r3 = cur.fetchall()
    returnlist=[]
    for i in r3:
        returnlist+=i

    return [("Nurse", "ID", "Vaccinated Patiens"), returnlist]


def patientreport(patientName):
    # Create a new connection
    con = connection()

    # Create a cursor on the connection
    cur = con.cursor()
    sql = """SELECT  p.Name,d.Name,n.Name as Nurse ,t.Name,t.Cost,s.StayEnd,r.RoomNumber ,r.BlockFloor,r.BlockCode
            FROM patient p ,physician d,nurse n ,undergoes u,treatment t  ,stay s ,room r
            WHERE p.Name= '%s' and p.SSN=s.Patient and s.Room=r.RoomNumber and s.StayID=u.Stay and  u.Treatment=t.Code and u.Physician=d.EmployeeID and u.AssistingNurse=n.EmployeeID;
            """ % (patientName)
    cur.execute(sql)
    result = cur.fetchall()
    returnresult=[]
    for i in result:
        returnresult += i
    return [
        ("Patient", "Physician", "Nurse", "Date of release", "Treatement going on", "Cost", "Room", "Floor", "Block"),
        returnresult]


def buildnewblock(blockfloor):
    # Create a new connection
    con = connection()
    # Create a cursor on the connection
    cur = con.cursor()

    floornum = int(blockfloor) / 1000
    blockcode = int(blockfloor) % 1000 / 100

    sql = "SELECT count(distinct b.BlockCode) FROM block b WHERE b.BlockFloor = '%s';" % (floornum)
    cur.execute(sql)
    numofblocks = cur.fetchall()
    if numofblocks[0][0] < 9:
        sql = "INSERT INTO block(BlockFloor,BlockCode) VALUES('%s','%s');" % (int(floornum), int(blockcode))
        cur.execute(sql)
        con.commit()
        num_of_rooms = random.randint(1, 5)
        i = 0
        while i < num_of_rooms:
            unavailable = random.randint(0, 1)
            rtype = random.choice(["single", "double", "triple", "quadruple"])
            rnumber = int(floornum) * 1000 + int(blockcode) * 100 + i
            sql = "INSERT INTO room(RoomNumber,RoomType,BlockFloor,BlockCode,Unavailable) VALUES('%s','%s','%s','%s','%s');" % (
                int(rnumber), rtype, int(floornum), int(blockcode), unavailable)
            cur.execute(sql)
            con.commit()
            i = i + 1
        r2 = "ok"
    else:
        r2 = "error"

    return [("result",), r2]
