import psycopg2
import urllib.parse, urllib.request, urllib.error, json
import secret

# Contact the CIRCL API for a list of vendors
def callCVE():
    req_url = "https://cve.circl.lu/api/browse/"
    try:
        cve_data_str = urllib.request.urlopen(req_url)
        cve_data = json.load(cve_data_str)
        saveVendors(cve_data)
    except urllib.error.HTTPError as e:
        print("The designated server could not fulfill the request.")
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We could not reach a server successfully.")
        print("Reason: ", e.reason)

# Initialize connection to Postgres container
conn = psycopg2.connect(host="172.19.0.2", port="5432" dbname="jopents", user="jopents", password=str(secret.passwd))
jopents = conn.cursor()

# Go through each of the vendors and add them if they aren't in Postgres yet
def saveVendors(raw):
    for vname in raw["vendor"]:
        try:
            if not checkVendor(vname):
                jopents.execute("""
                    INSERT INTO vendors (name) VALUES (%s);
                    """,
                    (str(vname),))
                conn.commit()
        except:
            print("Error writing vendors to database")
    with open("cronlog.txt", "w") as f:
        f.write("success!")

# Check for already existing vendor in Postgres
# (necessary for retention of primary key information)
def checkVendor(vendor):
    jopents.execute("""
        SELECT * FROM vendors WHERE name=%s;
        """,
        (str(vendor),))
    response = jopents.fetchall()
    if len(response) >= 1:
        return True
    else:
        return False

# contact the api, load all the vendors, close connection
callCVE()
if(conn):
    jopents.close()
    conn.close()