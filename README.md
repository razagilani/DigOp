DigOps
======

DigOps is a Django App designed to keep track of time spent in different 
workflow steps involved in digitization of items. DigOps also supports generation
of reports that can be used to track the rate at which items are being digitized.
It also supports plotting of data in graphs using Google chart API.
It uses Django authentication to identify users of the system.It drastically 
reduces tedious labor and endless headaches in keeping track of hours spent 
on a digital operation.

Installation Instructions
-------------------------

This software should be runnable on any kind of operating system. However, 
these installation instructions are tailored to a Linux server, and have
only been tested on ubuntu 10.04 LTS.

**Part I - Basic server requirements**

1. Install the Apache Django and other dependencies using the following command:

        sudo apt-get install apache2 python-dev mysql-server mysql-client python-setuptools libapache2-mod-wsgi python-mysqldb libmysqlclient15-dev 

2. Install git

        sudo apt-get install git-core


- - -

**Part II - Setting up the project environment**

1. Install virtualenv

        sudo apt-get install python-setuptools
        sudo easy_install virtualenv

2. Create directory for your projects (replace DIGOPS-HOME with your root directory)

        mkdir /DIGOPS-HOME
        cd /DISOPS-HOME

3. Clone the git repository using one of the following commands 

        (GW staff only)
        git clone git@github.com:gwu-libraries/DigOp.git

        (everyone else)
        git clone https://github.com/gwu-libraries/DigOp.git

4. cd into digop directory

        cd /DIGOPS-HOME/digop
	
5. Create virtual python environment using following command 

        virtualenv --no-site-packages ENV
        
6. Activate the virtual environemnt using the following command

	source ENV/bin/activate 

7. Install python suds library using following commands 

	sudo wget https://fedorahosted.org/releases/s/u/suds/python-suds-0.3.7.tar.gz
	tar -zxvf python-suds-0.3.7.tar.gz
	cd python-suds-0.3.7
	python setup.py install
	cd ..
	rm -rf python-suds-0.3.7
	rm -r python-suds-0.3.7.tar.gz

8. Install the additional required packages 

	pip install -r requirements.txt


- - -

**Part III - Configuring installation**

1. Login to mysql create the Database, Database user and assign the privileges to user. Change the username and password

	mysql -u root -p

2. Create the Database
        
        create Database Production;

3. Create Database user while changing user1 with a different username and pass1 with a different password
        
        CREATE USER 'user1'@'localhost' IDENTIFIED BY 'pass1';

4. Assign the privileges to user

	GRANT ALTER,CREATE,SELECT,INSERT,UPDATE,DELETE ON Production.* TO 'user1'@'localhost';

5. Commit the chages

	FLUSH PRIVILEGES;

6. Install Django's mssql server driver and fill in the values for Database in settings.py as follows:

        DATABASES = {
                'default': {
                    'NAME': 'Production',
                    'ENGINE': 'sqlserver_ado',
                    'HOST': 'GLS-KABIS\SQLEXPRESS',
                    'USER': '',
                    'PASSWORD': '',
                    'OPTIONS' : {
                        'provider': 'SQLOLEDB',             
	                'use_mars': True, 
                        },
                    }
                }

7. Update the Path to the Templates folder in the following variable in settings.py 
        
        TEMPLATE_DIRS = (
                # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
                # Always use forward slashes, even on Windows.
                # Don't forget to use absolute paths, not relative paths.
                "C:/templates"
                )

8. Move the templates password_reset_confirm.html, password_reset_complete.html to templates on your django path under regestration folder. 

        Example of path is /home/gilani/DigOp/ENV/lib/python2.6/site-packages/django/contrib/admin/templates/registration/

9. Type in the url of the Barcode_getpages_webservice that interacts with the KILTS Database in the following variable of settings.py file

        KABIS_SERVER_URL = ''

