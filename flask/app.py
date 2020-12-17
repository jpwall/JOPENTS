import psycopg2
import sys
sys.path.insert(1, './scripts')
import secret
sys.path.insert(1, './')

from flask import Flask
from flask import render_template, request
from jinja2 import Environment, FileSystemLoader

import urllib.parse, urllib.request, urllib.error, json, re
from requests_html import HTMLSession
session = HTMLSession()

# Miscellaneous methods
def isInt(n):
    try:
        int(n)
        return True
    except ValueError:
        return False

def parseVersion(text):
    nums = re.findall(r'\d+', text)
    ret = ""
    for i,num in enumerate(nums):
        if i <= 3:
            ret = ret + str(num) + "."
    if len(ret) > 1:
        return ret[:-1]
    return "Not Found"

# API methods
base_url = "https://cve.circl.lu/api"
def circlGetProducts(vendor):
    req_url = base_url + "/browse/{}".format(vendor)
    try:
        product_data_str = urllib.request.urlopen(req_url)
        product_data = json.load(product_data_str)
        saveProducts(product_data)
    except urllib.error.HTTPError as e:
        print("The designated server could not fulfill the request.")
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We could not reach a server successfully.")
        print("Reason: ", e.reason)

def getCVEs(vendor, product):
    product = product.replace("_", "+")
    req_url = "https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword={}+{}".format(vendor, product)
    page = session.get(req_url)
    table = page.html.find('#TableWithRules')
    CVEs = table[0].find('a')
    TDs = table[0].find('td')
    ret = []
    for CVE in CVEs:
        temp_tuple = ()
        temp_tuple = temp_tuple + (CVE.text,)
        #ret.append(CVE.text)
        ret.append(temp_tuple)
    for i,TD in enumerate(TDs):
        if (i - 1) % 2 == 0:
            index = int((i - 1)/2)
            try:
                ret[index] = ret[index] + (parseVersion(TD.text),)
            except IndexError:
                break
    return ret

def getCVE(cve_id):
    req_url = base_url + "/cve/{}".format(cve_id)
    try:
        cve_data_str = urllib.request.urlopen(req_url)
        cve_data = json.load(cve_data_str)
        return cve_data
    except urllib.error.HTTPError as e:
        print("The designated server could not fulfill the request.")
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We could not reach a server successfully.")
        print("Reason: ", e.reason)
    

# Database methods
conn = psycopg2.connect(host="172.19.0.2", port="5432", dbname="jopents", user="jopents", password=str(secret.passwd))
jopents = conn.cursor()

def dbSearchVendors(qry):
    jopents.execute("""
        SELECT vid, name FROM vendors WHERE name LIKE %s ESCAPE '';
        """,
        (str(qry) + "%",))
    response = jopents.fetchall()
    return response

def dbSearchProducts(qry):
    jopents.execute("""
        SELECT pid, name FROM products WHERE name LIKE %s ESCAPE '';
        """,
        (str(qry) + "%",))
    response = jopents.fetchall()
    return response

def getVendor(name):
    jopents.execute("""
        SELECT vid FROM vendors WHERE name=%s;
        """,
        (str(name),))
    vid = jopents.fetchall()
    return vid[0][0]

def getVendorName(vid):
    jopents.execute("""
        SELECT name FROM vendors WHERE vid=%s;
        """,
        (int(vid),))
    name = jopents.fetchall()
    return name[0][0]

def getVnameByPid(pid):
    jopents.execute("""
        SELECT vid FROM products WHERE pid=%s;
        """,
        (pid,))
    vid = jopents.fetchall()
    name = getVendorName(vid[0][0]) #here?
    return name

def saveProducts(data):
    vid = getVendor(data["vendor"])
    for pname in data["product"]:
        if not checkProduct(vid, str(pname)):
            jopents.execute("""
                INSERT INTO products (vid, name) VALUES (%s, %s);
                """,
                (vid, pname))
            conn.commit()

def hasProducts(vid):
    jopents.execute("""
        SELECT COUNT(*) FROM products WHERE vid=%s;
        """,
        (int(vid),))
    count = jopents.fetchall()
    #print(str(count))
    if count[0][0] > 0:
        return True
    return False

def checkProduct(vid, pname):
    jopents.execute("""
        SELECT * FROM products WHERE vid=%s AND name=%s;
        """,
        (vid, pname))
    product = jopents.fetchall()
    if len(product) >= 1:
        return True
    return False

def getPname(pid):
    jopents.execute("""
        SELECT name FROM products WHERE pid=%s;
        """,
        (pid,))
    pname = jopents.fetchall()
    return pname[0][0]

def getProducts(vid):
    jopents.execute("""
        SELECT pid, name FROM products WHERE vid=%s;
        """,
        (vid,))
    products = jopents.fetchall()
    return products

# Flask endpoints
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def main():
    if request.method == 'POST':
        return 'Great POST request, 10/10'

@app.route('/search', methods=['GET'])
def searchVendors():
    if str(request.args.get('search')) != '':
        results = dbSearchVendors(request.args.get('search').lower().replace(" ", "_"))
        count = len(results)
        p_results = dbSearchProducts(request.args.get('search').lower().replace(" ", "_"))
        p_count = len(p_results)
        return render_template('search.html', vendors=results, vcount=count, products=p_results, pcount=p_count)
    return 'Please enter a search term'

@app.route('/vendor/<vid>', methods=['GET'])
def loadProducts(vid):
    vname = getVendorName(vid)
    if not hasProducts(vid):
        # call API to get products and insert into database
        circlGetProducts(vname)
    # load products in page
    results = getProducts(vid)
    count = len(results)
    return render_template('products.html', products=results, vendor=vname, pcount=count)

@app.route('/product/<pid>', methods=['GET'])
def loadCVEs(pid):
    vname = getVnameByPid(pid)
    pname = getPname(pid)
    CVEs = getCVEs(vname, pname)
    CVEs_length = len(CVEs)
    return render_template('CVEs.html', vendor=vname, product=pname, cve_data=CVEs, ccount=CVEs_length)

@app.route('/cve/<cve_id>', methods=['GET'])
def cve(cve_id):
    data = getCVE(cve_id)
    """
        summary = data['summary']

        access_ease = data['access']['complexity']
        access_vector = data['access']['vector']
        access_auth = data['access']['authentication']

        impact_avail = data['impact']['availability']
        impact_conf = data['impact']['confidentiality']
        impact_integ = data['impact']['integrity']

        date = data['Published']

        FOR IN 'capec':
        attk_name = data['capec'][i]['name']
        attk_prereq = data['capec'][i]['prerequisites']
        attk_sol = data['capec'][i]['solutions']

        severity = data['cvss']

        FOR IN 'references':
        reference = data['references'][i]

        FOR IN 'vunlerable_product':
        product = data['vulnerable_product'][i]
    """
    capec_length = len(data['capec'])
    ref_length = len(data['references'])
    vuln_length = len(data['vulnerable_product'])
    return render_template('CVE.html', summary=data['summary'],
                    access_ease=data['access']['complexity'], access_vector=data['access']['vector'], access_auth=data['access']['authentication'],
                    impact_avail=data['impact']['availability'], impact_conf=data['impact']['availability'], impact_integ=data['impact']['integrity'],
                    date=data['Published'],
                    capec=data['capec'], capec_len=capec_length,
                    severity=data['cvss'],
                    references=data['references'], r_len=ref_length,
                    vuln=data['vulnerable_product'], v_len=vuln_length,
                    id=cve_id)
    #return str(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3100)