import cherrypy
import time
import hashlib
import re
from random import randint
import sqlite3 as sql
import smtplib

class SimpleOTP:

    def _getQsVal(self, name=""):
        '''
        Returns the request GET query string variable

        Args:
          name (string):  The name of the GET query string parameter

        Return:
          string: The value of the requested GET query string parameter
        '''
        try:
            val = cherrypy.request.params.get(name)
            if val == "":
                return False
        except:
            return False

        return val

    def _renderView(self, template, params):
        '''
        Reads an html template from the local file system and substitutes the template variable place holders
        with the values from the params list

        Args:
          template (string):   The name of the template file, without the .html extension
          params (dictionary): The dictionary containing the template variable placholders ot be substituted

        Return:
          string: The final html content to be displayed
        '''
        tplFile = template+".html"
        tpl = open(os.path.join(cherrypy.config.get('templates_dir'), tplFile))
        out = str(tpl.read())

        # Add the site logo to the parameters list
        params['{{site_logo}}'] = cherrypy.config.get('custom.site_logo')

        regex = re.compile('|'.join(params.keys()))
        result = regex.sub(lambda m: params[m.group(0)], out)
        return result


    def _sendHeaders(self):
        '''
        Sends the appropriate headers to the browser which indicates it to not allow caching of the page content.

        Args:
          None

        Return:
          Void
        '''
        cherrypy.response.headers['Content-Type'] = "text/html"
        cherrypy.response.headers['Expires'] = 'Tue, 01 Jan 1969 00:00:00 GMT'
        cherrypy.response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        cherrypy.response.headers['Pragma'] = 'no-cache'


    def index(self, **args):
        '''
        This page allows any user to enter a password, and then stores it in an row in the sqlite DB.  
        Once created, the user will receive a one-time url to retrieve the password
        
        Args:
          None

        Return:
          string: The corresponding HTML template to be rendered to the user
        '''
        self._sendHeaders()

        try:
            con = sql.connect(cherrypy.config.get('db.name'))
            cur = con.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS otp (hash TEXT, password TEXT, date_created INT)")
        except:
            return self._renderView("password_link", {'{{message}}': "Error: could not open DB!"})

        return self._renderView("index", {})

    index.exposed = True



    def getPasswordLink(self, **args):
        '''
        In this action, the user is shown the newly generated one type password link. The password entry
        in the database is also immediately deleted upon retreival.

        Args:
          password: A password consisting of any type of characters, via POST form data
          email:    A vallid email, via POST form data

        Return:
          string: The corresponding HTML template to be rendered to the user
        '''

        # Send the appropriate headers
        self._sendHeaders()
        
        try:
            password = cherrypy.request.body.params['password']
            email = cherrypy.request.body.params['email']
        except:
            # If the necessary parameters have not been posted, then redirect to the index
            # which is the starting point to generate a one-time password link
            raise cherrypy.HTTPRedirect("/")
            
        t = time.time()

        m = hashlib.md5()
        m.update(str(password)+str(int(t))+str(randint(1,9999999)))
        hashval = m.hexdigest()

        # Insert the password into the DB
        try:
            con = sql.connect(cherrypy.config.get('db.name'))
            cur = con.cursor()
        except:
            return self._renderView("password_link", {'{{message}}': "Could not open DB!"})

        cur.execute("INSERT INTO otp(hash, password, date_created) VALUES (:hashval,:password,:date_created);", {"hashval":hashval, "password":password, "date_created":int(t)})
        con.commit()

        if cherrypy.config.get('email.enable') == True:
            mail_header = 'Subject: %s\n\n' % ("Your One-Time Password Link",)

        out = 'One-time password link:\n\n '
        link = cherrypy.request.base+'/getPassword?hash='+hashval
        
        # Now send the email with the link  the user if the email option has been enabled
        if cherrypy.config.get('email.enable') == True:
            server = smtplib.SMTP('localhost')
            server.sendmail(cherrypy.config.get('email.from'), email, mail_header+out+link)
            server.quit()

        message = "One-Time password link listed below has been sent to %s.<br/><br/>" % (email,)
        message += link+"<br/>"


        return self._renderView("password_link", {'{{message}}': message})
  
    getPasswordLink.exposed = True



    def getPassword(self, **args):
        '''
        In this action, the user retrieves the password based on the hash he provides via the 'hash' query string

        Args:
          hash (string):  The hash key coresponding to the one-time password entry
        
        Return:
          string:  The corresponding HTML template to be rendered to the user
        '''
        self._sendHeaders()

        hashval = self._getQsVal('hash')
        hashval = str(hashval)
        
        if re.match('^[\w-]+$', hashval) == False:
            return self._renderView("password_link", {'{{message}}': 'Error: Invalid hash<br/><br/><a href="'+cherrypy.request.base+'">Create new OTP link</a>'})

        if hashval == False or hashval == "":
            return self._renderView("password_link", {'{{message}}': 'Error: Hash not specified<br/><br/><a href="'+cherrypy.request.base+'">Create new OTP link</a>'})

        # Get the password
        try:
            con = sql.connect(cherrypy.config.get('db.name'))
            cur = con.cursor()
        except:
            return self._renderView("password_link", {'{{message}}': "Error: Could not connect to DB!"})

        cur.execute("SELECT password FROM otp WHERE hash=?", (hashval,))

        # If entry isn't found in the DB
        if cur.rowcount == 0:
            return self._renderView("password_link", {'{{message}}': 'Error: Entry does not exist!<br/><br/><a href="'+cherrypy.request.base+'">Create new OTP link</a>'})

        # Store the result in a variable
        try:
            res = cur.fetchone()[0]
        except:
            return self._renderView("password_link", {'{{message}}': 'Error: No matching entries found!<br/><br/><a href="'+cherrypy.request.base+'">Create new OTP link</a>'})

        # Now delete the row
        cur.execute("DELETE FROM otp WHERE hash=:hashval", {"hashval":hashval})
        con.commit()

        return self._renderView("password_link", {'{{message}}': "Your password is:<br/><br/>"+res+"<br/>"})
    
    getPassword.exposed = True

    

import os.path
conf = os.path.join(os.path.dirname(__file__), 'data/app.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(SimpleOTP(), config=conf)
